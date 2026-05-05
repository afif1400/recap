"""Load a Patient from a case directory (manifest.json + bundles + docs + images).

A case directory looks like:

    data/cases/<case_id>/
    ├── manifest.json        # required
    ├── fhir.json            # optional Synthea bundle
    ├── docs/                # optional PDF lab/discharge docs
    │   └── lab_2022.pdf
    └── images/              # optional scans/photos
        └── fundus.png

The manifest declares which files exist and provides the metadata
(date, category, title) for each non-FHIR source. FHIR resources carry
their own dates, so they're parsed directly.
"""

import json
from pathlib import Path

from recap.ingestion.fhir import load_bundle
from recap.ingestion.image import load_image_event
from recap.ingestion.pdf import load_pdf
from recap.models import Event, Patient


def _events_from_pdf(case_dir: Path, doc: dict) -> list[Event]:
    """Render each page of a PDF into its own Event for citation precision."""
    file = doc["file"]
    src = Path(file).name
    pages = load_pdf(str(case_dir / file), source_id=src)
    from datetime import datetime

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


def _normalize_date(s: str) -> str:
    if "T" not in s:
        s = f"{s}T00:00:00+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return s


def load_case(cases_dir: str, case_id: str) -> Patient:
    base = Path(cases_dir) / case_id
    manifest = json.loads((base / "manifest.json").read_text())
    events: list[Event] = []

    if manifest.get("fhir_bundle"):
        events.extend(load_bundle(
            str(base / manifest["fhir_bundle"]),
            source_id=manifest["fhir_bundle"],
        ))

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
        display_name=manifest["display_name"],
        events=events,
    )
