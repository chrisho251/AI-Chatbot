import math

import pytest

from chatbot_contracts import samples
from chatbot_contracts.enums import SourceType
from chatbot_contracts.knowledge_base import PageFlags
from chatbot_platform import gate
from chatbot_platform.gate import GateContext


def _context(chunk_sets=None, pages=None, documents=None, manifest=None):
    document = samples.sample_document_version()
    return GateContext(
        manifest=manifest or samples.sample_manifest(),
        chunk_sets=[samples.sample_chunk_set()] if chunk_sets is None else chunk_sets,
        clean_pages=[samples.sample_clean_page(page_no=p) for p in (1, 2, 3)]
        if pages is None
        else pages,
        documents={document.doc_version: document} if documents is None else documents,
    )


def test_all_default_checks_pass_on_clean_input(platform):
    results = [check(_context()) for check in gate.default_checks(platform.settings)]
    failed = [r.name for r in results if not r.passed and not r.skipped]
    assert failed == []
    assert {r.name for r in results if r.skipped} == {"retrieval_regression", "ragas_regression"}


def test_page_coverage_reports_missing_pages():
    result = gate.check_page_coverage(_context(pages=[samples.sample_clean_page(page_no=1)]))
    assert not result.passed
    assert "[2, 3]" in result.details[0]


def test_chunk_ids_must_match_content():
    chunk_set = samples.sample_chunk_set()
    broken = chunk_set.model_copy(
        update={"chunks": [chunk_set.chunks[0].model_copy(update={"text": "edited"})]}
    )
    assert not gate.check_chunk_ids(_context(chunk_sets=[broken])).passed


def test_ocr_pii_and_duplicates_come_from_page_flags():
    pages = [
        samples.sample_clean_page(page_no=1, flags=PageFlags(min_ocr_conf=0.5)),
        samples.sample_clean_page(page_no=2, flags=PageFlags(pii_remaining=2)),
        samples.sample_clean_page(page_no=3, flags=PageFlags(dup_of="other@abc")),
    ]
    context = _context(pages=pages)
    assert not gate.check_ocr_confidence(context, 0.8).passed
    assert not gate.check_pii(context).passed
    assert not gate.check_duplicate_rate(context, 0.05).passed
    assert gate.check_duplicate_rate(context, 0.5).passed


@pytest.mark.parametrize("vector", [[0.0] * 8, [math.nan] * 8, [1.0] * 4])
def test_bad_embeddings_fail(vector):
    chunk_set = samples.sample_chunk_set()
    bad = chunk_set.model_copy(
        update={"chunks": [chunk_set.chunks[0].model_copy(update={"embedding": vector})]}
    )
    assert not gate.check_embeddings(_context(chunk_sets=[bad]), 8).passed


def test_external_exercise_without_licence_fails():
    document = samples.sample_document_version(
        source_type=SourceType.EXTERNAL_EXERCISE, licence=None
    )
    context = _context(documents={document.doc_version: document})
    assert not gate.check_licences(context).passed


def test_sme_decision_is_needed_for_new_documents(platform, upload):
    from chatbot_platform.versioning import create_candidate

    document = upload(b"edition one")
    manifest = create_candidate(
        platform.registry,
        add=[document.doc_version],
        embedding_model=samples.EMBEDDING_MODEL,
        chunker_version=samples.CHUNKER_VERSION,
    )
    report = gate.run_gate(platform.registry, _context(manifest=manifest), [gate.check_pii])
    assert report.auto_passed and report.requires_sme and not report.approved
    stored = gate.record_sme_decision(platform.registry, report.report_id, approved=True, by="sme")
    assert stored.approved
    assert platform.registry.get_kb_version(manifest.version_id).gate_report_id == stored.report_id


def test_embedding_refresh_needs_no_sme(platform, upload, ingest):
    from chatbot_platform.versioning import create_candidate

    document = upload(b"edition one")
    ingest({document.doc_version: list(samples.PAGE_TEXTS)})
    refresh = create_candidate(
        platform.registry, embedding_model="bge-m3-v2", chunker_version=samples.CHUNKER_VERSION
    )
    assert not gate.sme_required(platform.registry, refresh)
