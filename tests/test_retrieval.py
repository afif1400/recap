from datetime import datetime

from recap.models import Event
from recap.retrieval import retrieve


def _ev(eid, body, date_iso="2022-01-01"):
    return Event(
        id=eid,
        date=datetime.fromisoformat(date_iso),
        category="lab",
        title=body,
        source="x",
        body=body,
    )


def test_retrieves_relevant_events_for_question():
    events = [
        _ev("a", "Creatinine 1.4 mg/dL — first abnormal reading"),
        _ev("b", "Influenza vaccination administered"),
        _ev("c", "Hemoglobin A1c 8.2%"),
    ]
    hits = retrieve("when did creatinine become abnormal", events, top_k=2)
    assert hits[0].id == "a"


def test_retrieve_returns_at_most_top_k():
    events = [_ev(str(i), f"event {i}") for i in range(20)]
    hits = retrieve("event", events, top_k=5)
    assert len(hits) == 5


def test_retrieve_handles_empty_event_list():
    assert retrieve("anything", [], top_k=5) == []


def test_retrieve_falls_back_to_first_k_when_no_match():
    events = [_ev("a", "alpha"), _ev("b", "beta"), _ev("c", "gamma")]
    hits = retrieve("zzzzz", events, top_k=2)
    assert len(hits) == 2  # falls back to first k rather than empty
