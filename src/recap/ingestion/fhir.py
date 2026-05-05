"""Parse Synthea-style FHIR bundles into demographics + chronological Events.

Handles these FHIR resource types:
- Patient            → demographics (name, age, gender)
- Observation        → "lab" events
- Encounter          → "visit" events
- MedicationRequest  → "med" events
- Condition          → "diagnosis" events
- Procedure          → "procedure" events
- DiagnosticReport   → "report" events

Other Synthea-emitted types (Claim, ExplanationOfBenefit, CarePlan, Goal,
Immunization, AllergyIntolerance) are ignored for now — they're either
financial (no clinical value to the demo) or low-signal compared to the
above. We can add them if a showcase question needs them.
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from recap.models import Event

_TRAILING_DIGITS_RE = re.compile(r"\d+$")


@dataclass
class Demographics:
    display_name: str
    age: int | None
    gender: str | None  # "male" | "female" | "other"


def _parse_date(s: str) -> datetime:
    if "T" not in s:
        s = f"{s}T00:00:00+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _strip_synthea_digits(s: str) -> str:
    """Synthea suffixes names with digits (e.g. 'Sarah123 Smith45') so they look fake."""
    return _TRAILING_DIGITS_RE.sub("", s)


def _compute_age(birth_date: str, as_of: datetime | None = None) -> int | None:
    try:
        bd = _parse_date(birth_date)
    except Exception:
        return None
    now = as_of or datetime.now(timezone.utc)
    years = now.year - bd.year - ((now.month, now.day) < (bd.month, bd.day))
    return max(years, 0)


def _patient_to_demographics(r: dict) -> Demographics:
    names = r.get("name") or []
    family = ""
    given = ""
    if names:
        family = _strip_synthea_digits(names[0].get("family", ""))
        givens = names[0].get("given") or []
        if givens:
            given = _strip_synthea_digits(givens[0])
    full_name = f"{given} {family}".strip() or "Patient"

    age = _compute_age(r["birthDate"]) if r.get("birthDate") else None
    display = f"{full_name}, {age}" if age is not None else full_name
    return Demographics(display_name=display, age=age, gender=r.get("gender"))


def _observation_to_event(r: dict, source_id: str) -> Event | None:
    code = r.get("code", {}).get("text") or ""
    value = r.get("valueQuantity", {})
    v_str = ""
    if value:
        v_str = f"{value.get('value')} {value.get('unit', '')}".strip()
    date_str = r.get("effectiveDateTime") or r.get("issued")
    if not date_str:
        return None
    rid = r.get("id", "")
    title = f"{code}: {v_str}".strip(": ") if v_str else code or "Observation"
    return Event(
        id=f"obs-{rid}",
        date=_parse_date(date_str),
        category="lab",
        title=title,
        source=source_id,
        body=f"{code} value: {v_str}" if v_str else code,
        metadata={"resource_id": rid},
    )


def _encounter_to_event(r: dict, source_id: str) -> Event | None:
    reasons = r.get("reasonCode") or []
    reason = reasons[0].get("text", "Encounter") if reasons else "Encounter"
    start = r.get("period", {}).get("start")
    if not start:
        return None
    rid = r.get("id", "")
    return Event(
        id=f"enc-{rid}",
        date=_parse_date(start),
        category="visit",
        title=reason,
        source=source_id,
        body=reason,
        metadata={"resource_id": rid},
    )


def _medication_to_event(r: dict, source_id: str) -> Event | None:
    med = r.get("medicationCodeableConcept", {}).get("text", "Medication")
    authored = r.get("authoredOn")
    if not authored:
        return None
    rid = r.get("id", "")
    return Event(
        id=f"med-{rid}",
        date=_parse_date(authored),
        category="med",
        title=med,
        source=source_id,
        body=f"Prescribed: {med}",
        metadata={"resource_id": rid},
    )


def _condition_to_event(r: dict, source_id: str) -> Event | None:
    name = r.get("code", {}).get("text", "Condition")
    date_str = r.get("onsetDateTime") or r.get("recordedDate")
    if not date_str:
        return None
    rid = r.get("id", "")
    clinical = r.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
    return Event(
        id=f"cond-{rid}",
        date=_parse_date(date_str),
        category="diagnosis",
        title=name,
        source=source_id,
        body=f"Diagnosis: {name}" + (f" (status: {clinical})" if clinical else ""),
        metadata={"resource_id": rid, "clinical_status": clinical},
    )


def _procedure_to_event(r: dict, source_id: str) -> Event | None:
    name = r.get("code", {}).get("text", "Procedure")
    perf = r.get("performedDateTime") or r.get("performedPeriod", {}).get("start")
    if not perf:
        return None
    rid = r.get("id", "")
    return Event(
        id=f"proc-{rid}",
        date=_parse_date(perf),
        category="procedure",
        title=name,
        source=source_id,
        body=f"Procedure: {name}",
        metadata={"resource_id": rid},
    )


def _diagnostic_report_to_event(r: dict, source_id: str) -> Event | None:
    name = r.get("code", {}).get("text", "Report")
    date_str = r.get("effectiveDateTime") or r.get("issued")
    if not date_str:
        return None
    rid = r.get("id", "")
    conclusion = r.get("conclusion", "")
    return Event(
        id=f"rep-{rid}",
        date=_parse_date(date_str),
        category="report",
        title=name,
        source=source_id,
        body=f"{name}. {conclusion}".strip("."),
        metadata={"resource_id": rid},
    )


_DISPATCH = {
    "Observation": _observation_to_event,
    "Encounter": _encounter_to_event,
    "MedicationRequest": _medication_to_event,
    "Condition": _condition_to_event,
    "Procedure": _procedure_to_event,
    "DiagnosticReport": _diagnostic_report_to_event,
}


def _iter_resources(bundle: dict):
    for entry in bundle.get("entry", []):
        r = entry.get("resource", {})
        yield r.get("resourceType"), r


def load_bundle(path: str, source_id: str) -> list[Event]:
    """Parse a FHIR Bundle and return Events for known clinical resource types."""
    with Path(path).open() as f:
        bundle = json.load(f)

    events: list[Event] = []
    for rtype, r in _iter_resources(bundle):
        handler = _DISPATCH.get(rtype)
        if handler is None:
            continue
        ev = handler(r, source_id)
        if ev is not None:
            events.append(ev)
    return events


def load_demographics(path: str) -> Demographics | None:
    """Extract Patient demographics from a FHIR Bundle. Returns None if no Patient resource."""
    with Path(path).open() as f:
        bundle = json.load(f)

    for rtype, r in _iter_resources(bundle):
        if rtype == "Patient":
            return _patient_to_demographics(r)
    return None
