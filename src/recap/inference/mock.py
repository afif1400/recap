"""Mock backend for CPU-only local dev. Returns canned text without loading a model."""

import re


def generate_mock(system: str, user: str) -> str:
    """Pretend-answer that always cites the first source it sees in the user prompt."""
    m = re.search(r"\[src:([^\]]+)\]", user)
    src = m.group(1) if m else "unknown.pdf"

    # Try to surface the first event date and title for a slightly more useful demo string.
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", user)
    snippet_match = re.search(r"\[src:[^\]]+\][^\n]*?— (.+?)(?:\n|$)", user)

    date_str = date_match.group(1) if date_match else "an unknown date"
    snippet = snippet_match.group(1).strip() if snippet_match else "a record"

    return (
        f"[mock answer] Based on the records, the earliest relevant signal "
        f"appears on {date_str}: {snippet} [src:{src}]. "
        f"Set RECAP_BACKEND=zerogpu or mi300x for real inference."
    )
