from datetime import datetime

from recap.models import Event
from recap.timeline import build_timeline


def _ev(date_iso, cat="lab", title="t"):
    return Event(
        id=date_iso,
        date=datetime.fromisoformat(date_iso),
        category=cat,
        title=title,
        source="x",
    )


def test_timeline_sorts_chronologically():
    events = [_ev("2023-01-01"), _ev("2020-05-15"), _ev("2022-12-31")]
    tl = build_timeline(events)
    dates = [e.date for e in tl.events]
    assert dates == sorted(dates)


def test_timeline_groups_by_year():
    events = [_ev("2020-01-01"), _ev("2020-06-01"), _ev("2021-01-01")]
    tl = build_timeline(events)
    assert sorted(tl.years_covered) == [2020, 2021]


def test_empty_timeline_handles_zero_events():
    tl = build_timeline([])
    assert tl.events == []
    assert tl.years_covered == []
