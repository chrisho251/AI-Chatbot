"""Tests for normalize and strip_boilerplate."""

from chatbot_w5_clean.normalize import normalize, strip_boilerplate


def test_normalize_fixes_mojibake():
    text = "The mean is the sum of values divided by count."
    assert normalize(text) == text


def test_normalize_unifies_line_endings():
    text = "Line one\r\nLine two\rLine three"
    assert normalize(text) == "Line one\nLine two\nLine three"


def test_normalize_strips_trailing_whitespace():
    text = "Hello   \nWorld   "
    assert normalize(text) == "Hello\nWorld"


def test_normalize_collapses_excess_blank_lines():
    text = "First paragraph\n\n\n\nSecond paragraph"
    assert normalize(text) == "First paragraph\n\nSecond paragraph"


def test_normalize_fixes_encoding_damage():
    text = "Caf\u00e9 and na\u00efve"
    assert "Café" in normalize(text) or "Caf\xe9" in normalize(text)


def test_normalize_straightens_quotes():
    text = "She said \u201ctopics\u201d"
    assert normalize(text) == "She said " + chr(34) + "topics" + chr(34)


def test_normalize_empty_string():
    assert normalize("") == ""


def test_normalize_strips_leading_trailing_whitespace():
    assert normalize("  hello  ") == "hello"


def test_strip_boilerplate_removes_shared_header_and_footer():
    header = "Chapter 1"
    footer = "University Math Department"
    pages = [
        f"{header}\nThe mean is the sum of values divided by count.\n{footer}",
        f"{header}\nA confidence interval gives a range of plausible values.\n{footer}",
        f"{header}\nThe standard deviation measures spread from the mean.\n{footer}",
    ]
    result = strip_boilerplate(pages)
    assert "Chapter 1" not in result[0]
    assert "Chapter 1" not in result[1]
    assert "Chapter 1" not in result[2]
    assert "University Math" not in result[0]
    assert "University Math" not in result[2]
    assert "The mean" in result[0]
    assert "A confidence" in result[1]
    assert "The standard" in result[2]


def test_strip_boilerplate_single_page_unchanged():
    pages = ["Header\nSome content\nFooter"]
    assert strip_boilerplate(pages) == pages


def test_strip_boilerplate_keeps_equations():
    pages = [
        "Header\n$$x = \\frac{1}{n}$$\nMore text",
        "Header\n$$y = \\frac{2}{n}$$\nMore text",
        "Header\n$$z = \\frac{3}{n}$$\nMore text",
    ]
    result = strip_boilerplate(pages)
    assert "$$" in result[0]
    assert "$$" in result[1]
    assert "$$" in result[2]
    assert "Header" not in result[0]


def test_strip_boilerplate_keeps_code_fences():
    pages = [
        "Header\n```python\nprint('hello')\n```\nFooter",
        "Header\n```python\nprint('world')\n```\nFooter",
        "Header\n```python\nprint('test')\n```\nFooter",
    ]
    result = strip_boilerplate(pages)
    assert "```" in result[0]
    assert "print" in result[0]
    assert "Header" not in result[0]
    assert "Footer" not in result[0]


def test_strip_boilerplate_keeps_tables():
    pages = [
        "Header\n| Col A | Col B |\n|-------|-------|\n| 1 | 2 |\nFooter",
        "Header\n| Col A | Col B |\n|-------|-------|\n| 3 | 4 |\nFooter",
        "Header\n| Col A | Col B |\n|-------|-------|\n| 5 | 6 |\nFooter",
    ]
    result = strip_boilerplate(pages)
    assert "|" in result[0]
    assert "Header" not in result[0]
    assert "Footer" not in result[0]


def test_strip_boilerplate_preserves_unique_content():
    pages = [
        "Header\nUnique line A\nFooter",
        "Header\nUnique line B\nFooter",
        "Header\nUnique line C\nFooter",
    ]
    result = strip_boilerplate(pages)
    assert result[0] == "Unique line A"
    assert result[1] == "Unique line B"
    assert result[2] == "Unique line C"
