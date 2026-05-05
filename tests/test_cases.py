import json
import shutil

from recap.cases import load_case


def test_load_case_with_only_fhir(tmp_path):
    case = tmp_path / "tiny"
    case.mkdir()
    (case / "manifest.json").write_text(json.dumps({
        "id": "tiny",
        "display_name": "Tiny Test",
        "fhir_bundle": "fhir.json",
        "docs": [],
        "images": [],
        "demo_questions": [],
    }))
    shutil.copy("tests/fixtures/tiny_fhir.json", case / "fhir.json")

    p = load_case(str(tmp_path), "tiny")
    assert p.id == "tiny"
    assert p.display_name == "Tiny Test"  # manifest override wins
    assert len(p.events) > 0


def test_load_case_pulls_display_name_from_fhir_when_manifest_omits_it(tmp_path):
    """Minimal manifest — name, age, gender all come from the FHIR Patient resource."""
    case = tmp_path / "auto"
    case.mkdir()
    (case / "manifest.json").write_text(json.dumps({
        "id": "auto",
        "fhir_bundle": "fhir.json",
        "demo_questions": [],
    }))
    shutil.copy("tests/fixtures/tiny_fhir.json", case / "fhir.json")

    p = load_case(str(tmp_path), "auto")
    assert p.display_name.startswith("Jane Doe")  # from FHIR Patient.name
    assert p.age is not None and p.age >= 60
    assert p.gender == "female"


def test_load_case_with_pdf_docs(tmp_path):
    case = tmp_path / "tiny"
    case.mkdir()
    (case / "docs").mkdir()
    shutil.copy("tests/fixtures/tiny_lab.pdf", case / "docs" / "lab.pdf")

    (case / "manifest.json").write_text(json.dumps({
        "id": "tiny",
        "display_name": "Tiny",
        "fhir_bundle": None,
        "docs": [{
            "file": "docs/lab.pdf",
            "date": "2022-03-14",
            "category": "lab",
            "title": "Renal panel",
        }],
        "images": [],
        "demo_questions": [],
    }))

    p = load_case(str(tmp_path), "tiny")
    pdf_events = [e for e in p.events if e.source == "lab.pdf"]
    assert len(pdf_events) == 1
    assert pdf_events[0].category == "lab"
    assert "Creatinine" in pdf_events[0].body


def test_load_case_with_images(tmp_path):
    case = tmp_path / "tiny"
    case.mkdir()
    (case / "images").mkdir()
    from PIL import Image
    Image.new("RGB", (10, 10), "white").save(case / "images" / "fundus.png")

    (case / "manifest.json").write_text(json.dumps({
        "id": "tiny",
        "display_name": "Tiny",
        "fhir_bundle": None,
        "docs": [],
        "images": [{
            "file": "images/fundus.png",
            "date": "2023-04-01",
            "category": "scan",
            "title": "Fundus photo",
        }],
        "demo_questions": [],
    }))

    p = load_case(str(tmp_path), "tiny")
    assert len(p.events) == 1
    assert p.events[0].category == "scan"
    assert p.events[0].source == "fundus.png"


def test_load_case_events_chronologically_orderable(tmp_path):
    """Multi-source case (FHIR + PDF + image) yields a sortable timeline."""
    case = tmp_path / "tiny"
    case.mkdir()
    (case / "docs").mkdir()
    (case / "images").mkdir()
    shutil.copy("tests/fixtures/tiny_fhir.json", case / "fhir.json")
    shutil.copy("tests/fixtures/tiny_lab.pdf", case / "docs" / "lab.pdf")
    from PIL import Image
    Image.new("RGB", (10, 10), "white").save(case / "images" / "fundus.png")

    (case / "manifest.json").write_text(json.dumps({
        "id": "tiny",
        "display_name": "Tiny",
        "fhir_bundle": "fhir.json",
        "docs": [{
            "file": "docs/lab.pdf",
            "date": "2022-03-14",
            "category": "lab",
            "title": "Lab",
        }],
        "images": [{
            "file": "images/fundus.png",
            "date": "2023-04-01",
            "category": "scan",
            "title": "Fundus",
        }],
        "demo_questions": [],
    }))

    p = load_case(str(tmp_path), "tiny")
    sorted_dates = sorted(e.date for e in p.events)
    assert sorted_dates == [e.date for e in sorted(p.events, key=lambda e: e.date)]
