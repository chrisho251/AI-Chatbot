"""Deterministic identifiers for documents and chunks.

Identifiers are content addressed, so the same input always gives the same id.
"""

import hashlib
import re

_SEPARATOR = "\x1f"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_doc_id(course_code: str, source_id: str) -> str:
    """Stable id of a source document, shared by all of its versions."""
    return f"{_slug(course_code)}/{_slug(source_id)}"


def make_doc_version(doc_id: str, sha256: str) -> str:
    """Id of one exact file of a document. A new file hash gives a new version."""
    return f"{doc_id}@{sha256[:12]}"


def make_chunk_id(
    doc_version: str,
    page_start: int,
    page_end: int,
    text: str,
    chunker_version: str,
    embedding_model: str,
) -> str:
    """Content addressed chunk id. Unchanged pages keep their id across knowledge base versions."""
    parts = [doc_version, str(page_start), str(page_end), text, chunker_version, embedding_model]
    return sha256_hex(_SEPARATOR.join(parts).encode("utf-8"))


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not slug:
        raise ValueError(f"cannot build an id from {value!r}")
    return slug
