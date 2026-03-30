"""Tests for Markdown → Telegram HTML converter."""

from nutrition_agent.handlers.utils import markdown_to_telegram_html


def test_bold():
    assert "<b>hello</b>" in markdown_to_telegram_html("**hello**")


def test_italic():
    assert "<i>hello</i>" in markdown_to_telegram_html("*hello*")


def test_inline_code():
    assert "<code>foo</code>" in markdown_to_telegram_html("`foo`")


def test_fenced_code_block():
    md = "```python\nprint('hi')\n```"
    result = markdown_to_telegram_html(md)
    assert "<pre>" in result
    assert "print(&#x27;hi&#x27;)" in result  # html-escaped quote


def test_html_escape():
    result = markdown_to_telegram_html("1 < 2 & 3 > 0")
    assert "&lt;" in result
    assert "&amp;" in result
    assert "&gt;" in result


def test_markdown_table_to_box():
    md = (
        "| Блюдо   | Ккал | Б  | Ж  | У  |\n"
        "|---------|------|----|----|----|\n"
        "| Овсянка | 350  | 12 | 8  | 55 |\n"
        "| Курица  | 450  | 45 | 12 | 30 |"
    )
    result = markdown_to_telegram_html(md)
    assert "<pre>" in result
    assert "┌" in result
    assert "├" in result
    assert "└" in result
    assert "│" in result
    assert "Овсянка" in result
    assert "Курица" in result


def test_header_to_bold():
    result = markdown_to_telegram_html("### Итого за день")
    assert "<b>Итого за день</b>" in result


def test_strikethrough():
    result = markdown_to_telegram_html("~~deleted~~")
    assert "<s>deleted</s>" in result


def test_mixed_content():
    md = (
        "**Завтрак:**\n"
        "\n"
        "| Продукт | Ккал |\n"
        "|---------|------|\n"
        "| Яйца   | 150  |\n"
        "\n"
        "Итого: `150 ккал`"
    )
    result = markdown_to_telegram_html(md)
    assert "<b>Завтрак:</b>" in result
    assert "┌" in result
    assert "<code>150 ккал</code>" in result


def test_underscore_in_words_not_italic():
    result = markdown_to_telegram_html("some_variable_name")
    assert "<i>" not in result
    assert "some_variable_name" in result


def test_empty_input():
    assert markdown_to_telegram_html("") == ""


def test_no_table_false_positive():
    result = markdown_to_telegram_html("a | b means or")
    # Single line with pipe shouldn't become a table (no separator row)
    assert "┌" not in result
