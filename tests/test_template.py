import pytest

from prompt_registry import template


def test_extract_variables_returns_unique_names_in_order() -> None:
    result = template.extract_variables(
        "Summarize {topic} in {tone} tone about {topic}."
    )

    assert result == ["topic", "tone"]


def test_extract_variables_empty_template() -> None:
    assert template.extract_variables("") == []


def test_extract_variables_no_placeholders() -> None:
    assert template.extract_variables("Plain text.") == []


def test_extract_variables_strips_whitespace_inside_braces() -> None:
    assert template.extract_variables("Hello { name }") == ["name"]


def test_render_substitutes_variables() -> None:
    result = template.render(
        "Summarize {topic} in {tone} tone.",
        {"topic": "AI safety", "tone": "concise"},
    )

    assert result == "Summarize AI safety in concise tone."


def test_render_reuses_variable_multiple_times() -> None:
    result = template.render(
        "{word} {word}",
        {"word": "echo"},
    )

    assert result == "echo echo"


def test_render_ignores_extra_values() -> None:
    result = template.render(
        "Hello {name}",
        {"name": "world", "unused": "ignored"},
    )

    assert result == "Hello world"


def test_render_empty_template() -> None:
    assert template.render("", {}) == ""


def test_render_missing_variable_raises() -> None:
    with pytest.raises(template.TemplateRenderError) as exc_info:
        template.render("Hello {name}", {})

    assert exc_info.value.missing == ["name"]


def test_render_missing_one_of_many_raises_with_all_missing() -> None:
    with pytest.raises(template.TemplateRenderError) as exc_info:
        template.render("{a} and {b}", {"a": "1"})

    assert exc_info.value.missing == ["b"]
