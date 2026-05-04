"""Wrap medical images as Events with caller-provided date and category.

We do not auto-extract dates from EXIF — clinical workflow requires curation.
The caller (case manifest, upload handler) provides the date explicitly.
"""

from datetime import datetime
from pathlib import Path

from recap.models import Event, EventCategory


def _parse_date(s: str) -> datetime:
    if "T" not in s:
        s = f"{s}T00:00:00+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def load_image_event(
    path: str,
    *,
    category: EventCategory,
    title: str,
    date_iso: str,
    source_id: str | None = None,
) -> Event:
    src = source_id or Path(path).name
    return Event(
        id=f"img-{src}",
        date=_parse_date(date_iso),
        category=category,
        title=title,
        source=src,
        body=f"Image: {title}",
        metadata={"path": path},
    )
