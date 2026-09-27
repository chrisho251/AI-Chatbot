"""Tests for near duplicate detection."""

from chatbot_w5_clean.dedupe import PageKey, find_duplicates


def _key(doc_version: str, page_no: int) -> PageKey:
    return (doc_version, page_no)


def test_nearly_identical_pages_are_duplicates():
    base = "The mean is the sum of values divided by the number of values."
    pages = {
        _key("v1", 1): base,
        _key("v1", 2): base + " Extra sentence here.",
    }
    result = find_duplicates(pages)
    assert _key("v1", 2) in result
    assert result[_key("v1", 2)] == _key("v1", 1)


def test_pages_differing_by_one_word_are_duplicates():
    base = "The mean is the sum of values divided by the number of values."
    pages = {
        _key("v1", 1): base,
        _key("v1", 2): base.replace("mean", "average"),
    }
    result = find_duplicates(pages)
    assert _key("v1", 2) in result


def test_unrelated_pages_are_not_duplicates():
    pages = {
        _key("v1", 1): "The mean is the sum of values divided by count.",
        _key("v1", 2): "A confidence interval gives a range of plausible values for a parameter.",
    }
    result = find_duplicates(pages)
    assert result == {}


def test_three_pages_one_duplicate():
    a = "The standard deviation measures how far values spread from the mean."
    b = "The standard deviation measures how far values spread from the mean."
    c = "The variance is the square of the standard deviation."
    pages = {_key("v1", 1): a, _key("v1", 2): b, _key("v1", 3): c}
    result = find_duplicates(pages)
    assert _key("v1", 2) in result
    assert _key("v1", 3) not in result


def test_single_page_returns_empty():
    pages = {_key("v1", 1): "Some content."}
    assert find_duplicates(pages) == {}


def test_empty_input_returns_empty():
    assert find_duplicates({}) == {}


def test_duplicate_maps_to_first_occurrence():
    base = "The standard deviation measures spread from the mean."
    pages = {
        _key("v1", 1): base,
        _key("v1", 2): base,
        _key("v1", 3): base,
    }
    result = find_duplicates(pages)
    assert _key("v1", 2) in result
    assert _key("v1", 3) in result
    assert result[_key("v1", 2)] == _key("v1", 1)
    assert result[_key("v1", 3)] == _key("v1", 1)


def test_different_document_versions_detected():
    text = "The mean is the sum of values divided by the number of values."
    pages = {
        _key("v1", 1): text,
        _key("v2", 1): text,
    }
    result = find_duplicates(pages)
    assert _key("v2", 1) in result
    assert result[_key("v2", 1)] == _key("v1", 1)
