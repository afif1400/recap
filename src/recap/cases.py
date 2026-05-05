"""Load a Patient from a case directory (manifest.json + bundles + docs + images).

A case directory looks like:

    data/cases/<case_id>/
    ├── manifest.json        # required
    ├── fhir.json            # optional Synthea bundle
    ├── docs/                # optional PDF lab/discharge docs
    │   └── lab_2022.pdf
    └── images/              # optional scans/photos
        └── fundus.png

If a FHIR bundle is present, the patient's display name, age, and gender
are pulled from it automatically — manifest can omit `display_name`.
"""

import json
from datetime import datetime
from pathlib import Path

from recap.ingestion.fhir import load_bundle, load_demographics
from recap.ingestion.image import load_image_event
from recap.ingestion.pdf import load_pdf
from recap.models import Event, Patient


def _normalize_date(s: str) -> str:
    if "T" not in s:
        s = f"{s}T00:00:00+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return s


def _events_from_pdf(case_dir: Path, doc: dict) -> list[Event]:
    file = doc["file"]
    src = Path(file).name
    pages = load_pdf(str(case_dir / file), source_id=src)
    date = datetime.fromisoformat(_normalize_date(doc["date"]))
    return [
        Event(
            id=f"pdf-{src}-p{p.page_number}",
            date=date,
            category=doc.get("category", "note"),
            title=doc.get("title", src),
            source=src,
            body=p.text,
            metadata={"page": p.page_number},
        )
        for p in pages
    ]


def load_case(cases_dir: str, case_id: str) -> Patient:
    base = Path(cases_dir) / case_id
    manifest = json.loads((base / "manifest.json").read_text())
    events: list[Event] = []

    # Default demographics from manifest (used as fallback or override).
    display_name = manifest.get("display_name")
    age: int | None = manifest.get("age")
    gender: str | None = manifest.get("gender")

    if manifest.get("fhir_bundle"):
        bundle_path = str(base / manifest["fhir_bundle"])
        events.extend(load_bundle(bundle_path, source_id=manifest["fhir_bundle"]))

        # Pull demographics from FHIR Patient resource — manifest values, if any, win.
        demo = load_demographics(bundle_path)
        if demo is not None:
            display_name = display_name or demo.display_name
            age = age if age is not None else demo.age
            gender = gender or demo.gender

    for doc in manifest.get("docs", []):
        events.extend(_events_from_pdf(base, doc))

    for img in manifest.get("images", []):
        events.append(load_image_event(
            str(base / img["file"]),
            category=img.get("category", "scan"),
            title=img.get("title", img["file"]),
            date_iso=img["date"],
            source_id=Path(img["file"]).name,
        ))

    return Patient(
        id=manifest["id"],
        display_name=display_name or manifest["id"],  # final fallback: case_id
        age=age,
        gender=gender,
        events=events,
    )
