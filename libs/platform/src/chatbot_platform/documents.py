"""Register uploaded source files. This is step 1 of ingestion.

The file goes to the raw bucket under its sha256 and is never overwritten. The registry records a
document version. When the same course and source id arrive with a new hash, the new version
supersedes the previous one. Uploading the exact same file twice returns the existing version.
"""

from pathlib import PurePath

from chatbot_contracts.corpus import DocumentVersion
from chatbot_contracts.enums import SourceType
from chatbot_contracts.ids import make_doc_id, make_doc_version, sha256_hex
from chatbot_platform.errors import VersioningError
from chatbot_platform.registry import Registry
from chatbot_platform.settings import RAW_BUCKET
from chatbot_platform.storage import ObjectStore


def raw_key(sha256: str, filename: str) -> str:
    extension = PurePath(filename).suffix.lower().lstrip(".") or "bin"
    return f"{sha256[:2]}/{sha256}.{extension}"


def register_document(
    registry: Registry,
    store: ObjectStore,
    data: bytes,
    *,
    filename: str,
    course_code: str,
    source_id: str,
    source_type: SourceType,
    licence: str | None = None,
    source_url: str | None = None,
    producer: str = "platform",
) -> DocumentVersion:
    if source_type == SourceType.EXTERNAL_EXERCISE and not licence:
        raise VersioningError("external exercises must carry a licence")
    sha256 = sha256_hex(data)
    doc_id = make_doc_id(course_code, source_id)
    existing = registry.find_doc_version(doc_id, sha256)
    if existing is not None:
        return existing

    key = raw_key(sha256, filename)
    if not store.exists(RAW_BUCKET, key):
        store.put(RAW_BUCKET, key, data)
    previous = registry.latest_doc_version(doc_id)
    document = DocumentVersion(
        producer=producer,
        doc_id=doc_id,
        doc_version=make_doc_version(doc_id, sha256),
        sha256=sha256,
        source_type=source_type,
        course_code=course_code,
        source_id=source_id,
        raw_uri=f"s3://{RAW_BUCKET}/{key}",
        licence=licence,
        source_url=source_url,
        supersedes=previous.doc_version if previous else None,
    )
    registry.add_doc_version(document)
    return document


def retract_document(registry: Registry, doc_version: str) -> None:
    """Withdraw a version with no replacement. The next candidate drops it from the corpus."""
    registry.retract(doc_version)
