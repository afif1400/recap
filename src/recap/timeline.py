"""Build a chronological timeline view of a patient's events."""

from dataclasses import dataclass

from recap.models import Event


@dataclass
class Timeline:
    events: list[Event]
    years_covered: list[int]


def build_timeline(events: list[Event]) -> Timeline:
    sorted_events = sorted(events, key=lambda e: e.date)
    years = sorted({e.date.year for e in sorted_events})
    return Timeline(events=sorted_events, years_covered=years)
