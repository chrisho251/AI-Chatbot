import pytest

from chatbot_contracts.ids import make_chunk_id, make_doc_id, make_doc_version, sha256_hex


def test_doc_id_is_normalized():
    assert make_doc_id(" STAT 101 ", "Textbook Chapter 1") == "stat_101/textbook_chapter_1"


def test_doc_id_rejects_empty_parts():
    with pytest.raises(ValueError):
        make_doc_id("STAT 101", "  ")


def test_doc_version_changes_with_the_file_hash():
    doc_id = make_doc_id("STAT 101", "notes")
    first = make_doc_version(doc_id, sha256_hex(b"first"))
    second = make_doc_version(doc_id, sha256_hex(b"second"))
    assert first != second
    assert first.startswith(doc_id + "@")


def test_chunk_id_is_deterministic_and_sensitive_to_every_field():
    base = ("doc@abc", 1, 2, "text", "structure-v1", "bge-m3")
    assert make_chunk_id(*base) == make_chunk_id(*base)
    for position in range(len(base)):
        changed = list(base)
        changed[position] = changed[position] + 1 if isinstance(changed[position], int) else "x"
        assert make_chunk_id(*changed) != make_chunk_id(*base)
