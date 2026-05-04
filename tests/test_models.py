from datetime import datetime

from recap.models import Citation, Event, Patient


def test_citation_roundtrip():
    c = Citation(source_id="lab_2022-03-14.pdf", page=2, snippet="Cr 1.4 mg/dL")
    d = c.model_dump()
    assert d["source_id"] == "lab_2022-03-14.pdf"
    assert d["page"] == 2


def test_event_orderable_by_date():
    a = Event(
        id="a",
        date=datetime(2022, 3, 14),
        category="lab",
        title="Cr 1.4",
        source="lab_2022-03-14.pdf",
    )
    b = Event(
        id="b",
        date=datetime(2023, 1, 1),
        category="visit",
        title="Nephrology",
        source="visit_2023-01-01.pdf",
    )
    assert sorted([b, a], key=lambda e: e.date) == [a, b]


def test_patient_holds_events():
    p = Patient(id="sarah", display_name="Sarah, 67", events=[])
    assert p.id == "sarah"
    assert len(p.events) == 0
