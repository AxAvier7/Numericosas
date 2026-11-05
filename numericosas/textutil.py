from __future__ import annotations

import re

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(value: str | None) -> str:
    """Quita caracteres de control que rompen el XML de Excel."""
    if not value:
        return ""
    return _CONTROL_RE.sub("", value)


def word_count(value: str) -> int:
    return len(re.findall(r"\w+", value, flags=re.UNICODE))


def clean_url(url: str) -> str:
    url = url.strip()
    url = url.rstrip(".,;:!?")
    if url.endswith(")") and url.count("(") < url.count(")"):
        url = url[:-1]
    return url


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_urls(text: str) -> list[str]:
    return dedupe(clean_url(match) for match in URL_RE.findall(text))


def truncate(value: str, limit: int) -> str:
    value = value or ""
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
