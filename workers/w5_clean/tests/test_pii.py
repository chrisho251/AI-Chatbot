"""Tests for PII scrubbing."""

from chatbot_w5_clean.pii import ScrubResult, scrub


def test_scrubs_name_email_and_student_number():
    text = "John Smith has email john.smith@example.com and student number 301001234."
    result = scrub(text)
    assert isinstance(result, ScrubResult)
    assert result.hits == 3
    assert result.remaining == 0
    assert "John Smith" not in result.text
    assert "john.smith@example.com" not in result.text
    assert "301001234" not in result.text
    assert "[NAME]" in result.text
    assert "[EMAIL]" in result.text
    assert "[STUDENT_ID]" in result.text


def test_placeholder_per_entity_type():
    text = "Alice Johnson (student 987654321) can be reached at alice@university.edu."
    result = scrub(text)
    assert "[NAME]" in result.text
    assert "[EMAIL]" in result.text
    assert "[STUDENT_ID]" in result.text


def test_clean_text_returns_zero_hits():
    text = "The mean is the sum of values divided by the number of values."
    result = scrub(text)
    assert result.hits == 0
    assert result.remaining == 0
    assert result.text == text


def test_second_pass_catches_remaining_pii():
    scrubbed = scrub("John Smith")
    assert scrubbed.remaining == 0


def test_multiple_entities_on_multiple_lines():
    text = "Jane Doe submitted homework.\nContact: jane.doe@test.edu\nID: 123456789"
    result = scrub(text)
    assert result.hits == 3
    assert result.remaining == 0
    assert "Jane Doe" not in result.text
    assert "jane.doe@test.edu" not in result.text


def test_scrub_result_is_frozen():
    result = scrub("John Smith")
    try:
        result.text = "changed"
        raise AssertionError("ScrubResult should be frozen")
    except AttributeError:
        pass
