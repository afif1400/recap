from datetime import datetime

from recap.ingestion.fhir import load_bundle


def test_loads_observation_as_lab_event():
    events = load_bundle("tests/fixtures/tiny_fhir.json", source_id="tiny_fhir.json")
    labs = [e for e in events if e.category == "lab"]
    assert len(labs) == 1
    assert "Creatinine" in labs[0].title
    assert "1.4" in labs[0].title or "1.4" in labs[0].body
    assert labs[0].date == datetime.fromisoformat("2022-03-14T10:00:00+00:00")


def test_loads_encounter_as_visit_event():
    events = load_bundle("tests/fixtures/tiny_fhir.json", source_id="tiny_fhir.json")
    visits = [e for e in events if e.category == "visit"]
    assert len(visits) == 1
    assert "Nephrology" in visits[0].title


def test_loads_medication_as_med_event():
    events = load_bundle("tests/fixtures/tiny_fhir.json", source_id="tiny_fhir.json")
    meds = [e for e in events if e.category == "med"]
    assert len(meds) == 1
    assert "Lisinopril" in meds[0].title


def test_events_are_chronologically_orderable():
    events = load_bundle("tests/fixtures/tiny_fhir.json", source_id="tiny_fhir.json")
    sorted_events = sorted(events, key=lambda e: e.date)
    assert [e.id for e in sorted_events] == [e.id for e in sorted(events, key=lambda e: e.date)]
