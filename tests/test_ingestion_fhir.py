from datetime import datetime, timezone

from recap.ingestion.fhir import load_bundle, load_demographics


FIXTURE = "tests/fixtures/tiny_fhir.json"


def test_loads_observation_as_lab_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    labs = [e for e in events if e.category == "lab"]
    assert len(labs) == 1
    assert "Creatinine" in labs[0].title
    assert "1.4" in labs[0].title or "1.4" in labs[0].body
    assert labs[0].date == datetime.fromisoformat("2022-03-14T10:00:00+00:00")


def test_loads_encounter_as_visit_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    visits = [e for e in events if e.category == "visit"]
    assert len(visits) == 1
    assert "Nephrology" in visits[0].title


def test_loads_medication_as_med_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    meds = [e for e in events if e.category == "med"]
    assert len(meds) == 1
    assert "Lisinopril" in meds[0].title


def test_loads_condition_as_diagnosis_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    dx = [e for e in events if e.category == "diagnosis"]
    assert len(dx) == 1
    assert "Chronic kidney disease" in dx[0].title
    assert dx[0].metadata["clinical_status"] == "active"


def test_loads_procedure_as_procedure_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    procs = [e for e in events if e.category == "procedure"]
    assert len(procs) == 1
    assert "Renal ultrasound" in procs[0].title


def test_loads_diagnostic_report_as_report_event():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    reports = [e for e in events if e.category == "report"]
    assert len(reports) == 1
    assert "metabolic panel" in reports[0].title.lower()
    assert "stage 3 CKD" in reports[0].body


def test_events_are_chronologically_orderable():
    events = load_bundle(FIXTURE, source_id="tiny_fhir.json")
    sorted_events = sorted(events, key=lambda e: e.date)
    assert [e.id for e in sorted_events] == [e.id for e in sorted(events, key=lambda e: e.date)]


def test_load_demographics_extracts_name_age_gender():
    demo = load_demographics(FIXTURE)
    assert demo is not None
    # Trailing digits ("Jane45 Doe123") stripped for display
    assert demo.display_name.startswith("Jane Doe")
    assert demo.gender == "female"
    # Born 1957 → age depends on current date but should be > 60
    assert demo.age is not None and demo.age >= 60


def test_load_demographics_returns_none_if_no_patient_resource(tmp_path):
    import json
    p = tmp_path / "no_patient.json"
    p.write_text(json.dumps({"resourceType": "Bundle", "entry": []}))
    assert load_demographics(str(p)) is None
