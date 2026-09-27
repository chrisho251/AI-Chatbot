"""Offline entrypoint of W5 clean. The pipeline lane runs it once per ingestion run.

Join the text regions and the ExtractedRegion rows of every page in reading order,
normalize, strip boilerplate, scrub PII, scan for injected instructions and mark
duplicates. Append exactly one CleanPage per page to ingest.cleaned_pages, blank
pages included, with PageFlags filled in for the quality gate.
Dagster starts it in the app image with the run id and the document version.
"""

import argparse
from collections import defaultdict

from chatbot_contracts.enums import RegionKind
from chatbot_contracts.knowledge_base import CleanPage, ExtractedRegion, PageFlags, Region
from chatbot_platform import ingest
from chatbot_platform.factory import Platform, build_platform
from chatbot_w5_clean import dedupe, injection, normalize, pii


def run(platform: Platform, run_id: str, doc_version: str) -> int:
    """Write one CleanPage per page of the document version and return the count."""
    regions = [
        r
        for r in ingest.read_records(platform.engine, "ingest.regions", Region, [run_id])
        if r.doc_version == doc_version
    ]
    extracted = {
        e.region_id: e
        for e in ingest.read_records(
            platform.engine, "ingest.extracted_regions", ExtractedRegion, [run_id]
        )
    }

    regions.sort(
        key=lambda r: (
            r.page_no,
            r.bbox[1] if r.bbox else 0.0,
            r.bbox[0] if r.bbox else 0.0,
        )
    )

    page_contents: dict[int, list[str]] = defaultdict(list)
    page_region_ids: dict[int, list[str]] = defaultdict(list)
    page_ocr_confs: dict[int, list[float]] = defaultdict(list)

    for region in regions:
        if region.kind == RegionKind.TEXT and region.raw_text:
            page_contents[region.page_no].append(region.raw_text)
            page_region_ids[region.page_no].append(region.region_id)
        elif region.region_id in extracted:
            er = extracted[region.region_id]
            page_contents[region.page_no].append(er.content)
            page_region_ids[region.page_no].append(region.region_id)
            if er.kind in (RegionKind.SCAN, RegionKind.TABLE):
                page_ocr_confs[region.page_no].append(er.confidence)

    doc = platform.registry.get_doc_version(doc_version)
    page_count = doc.page_count if doc else 0
    page_count = page_count or (max(page_contents) if page_contents else 0)

    page_texts: dict[int, str] = {}
    for page_no in range(1, page_count + 1):
        contents = page_contents.get(page_no, [])
        page_texts[page_no] = "\n\n".join(contents)

    normalized = {p: normalize.normalize(t) for p, t in page_texts.items()}
    sorted_pages = sorted(normalized)
    stripped = normalize.strip_boilerplate([normalized[p] for p in sorted_pages])

    cleaned: dict[int, str] = {}
    flags: dict[int, PageFlags] = {}
    for i, page_no in enumerate(sorted_pages):
        scrubbed = pii.scrub(stripped[i])
        cleaned[page_no] = scrubbed.text
        ocr_confs = page_ocr_confs.get(page_no, [])
        min_ocr = min(ocr_confs) if ocr_confs else None
        flags[page_no] = PageFlags(
            min_ocr_conf=min_ocr,
            pii_hits=scrubbed.hits,
            pii_remaining=scrubbed.remaining,
            injection_hits=0,
        )

    for page_no in sorted_pages:
        text = cleaned[page_no]
        if text.strip():
            hits = injection.scan(text).hits
            flags[page_no] = flags[page_no].model_copy(update={"injection_hits": hits})

    dup_keys = {(doc_version, p): cleaned[p] for p in sorted_pages}
    duplicates = dedupe.find_duplicates(dup_keys)
    for page_no in sorted_pages:
        dup_key = (doc_version, page_no)
        if dup_key in duplicates and duplicates[dup_key] != dup_key:
            source = duplicates[dup_key]
            flags[page_no] = flags[page_no].model_copy(
                update={"dup_of": f"{source[0]}:{source[1]}"}
            )

    clean_pages = [
        CleanPage(
            ingestion_run_id=run_id,
            doc_version=doc_version,
            page_no=page_no,
            markdown=cleaned[page_no],
            region_ids=page_region_ids.get(page_no, []),
            flags=flags[page_no],
        )
        for page_no in sorted_pages
    ]

    ingest.append_records(platform.engine, "ingest.cleaned_pages", clean_pages)
    return len(clean_pages)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--doc-version", required=True)
    args = parser.parse_args(argv)
    print(run(build_platform(), args.run_id, args.doc_version))


if __name__ == "__main__":
    main()
