"""Tests for web page text extraction."""

from pathlib import Path

from chatbot_w5_clean import web

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_text_keeps_article_content():
    html = """
    <html><body>
    <article><p>A confidence interval gives a range of plausible values.</p></article>
    <nav><a href="/">Menu</a></nav>
    </body></html>
    """
    text = web.extract_text(html)
    assert "confidence interval" in text
    assert "Menu" not in text


def test_extract_text_keeps_tables():
    html = """
    <html><body>
    <article>
    <table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>
    </article>
    </body></html>
    """
    text = web.extract_text(html)
    assert "A" in text
    assert "1" in text


def test_extract_text_returns_empty_string_for_nav_only():
    html = "<html><body><nav>only navigation links here</nav></body></html>"
    assert web.extract_text(html) == ""


def test_extract_text_returns_empty_for_empty_input():
    assert web.extract_text("") == ""
    assert web.extract_text("   ") == ""


def test_extract_text_drops_navigation_and_ads():
    html = """<html><body>
    <nav>Skip to content</nav>
    <article><p>Real exercise content about statistics.</p></article>
    <aside>Advertisement for pills</aside>
    </body></html>"""
    text = web.extract_text(html)
    assert "statistics" in text
    assert "Advertisement" not in text


def test_extract_text_from_fixture_file():
    html = (FIXTURES / "sample_page.html").read_text()
    text = web.extract_text(html)
    assert "confidence interval" in text.lower()
    assert "plausible values" in text
    assert "standard error" in text.lower() or "Standard error" in text
    assert "Menu" not in text
    assert "University Math" not in text
    assert "|" in text
