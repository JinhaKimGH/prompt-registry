"""Variable extraction and rendering for prompt templates."""

from __future__ import annotations

import re

_FIELD_NAME = re.compile(r"\{([^{}]+)\}")


class TemplateRenderError(ValueError):
    """Raised when required template variables are missing from the values dict."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(
            f"Missing template variables: {', '.join(missing)}"
        )


def extract_variables(template: str) -> list[str]:
    """Return unique {variable} names from a template, in first-seen order."""
    seen: set[str] = set()
    variables: list[str] = []
    for match in _FIELD_NAME.finditer(template):
        name = match.group(1).strip()
        if name and name not in seen:
            seen.add(name)
            variables.append(name)
    return variables


def render(template: str, values: dict[str, str]) -> str:
    """Fill {variable} placeholders using the provided values."""
    missing = [name for name in extract_variables(template) if name not in values]
    if missing:
        raise TemplateRenderError(missing)
    return template.format(**values)
