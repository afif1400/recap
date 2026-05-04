"""Parse Synthea-style FHIR bundles into chronologically orderable Events."""

import json
from datetime import datetime
from pathlib import Path

from recap.models import Event


def _parse_date(s: str) -> datetime:
    if "T" not in s:
        s = f"{s}T00:00:00+00:00"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


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


_DISPATCH = {
    "Observation": _observation_to_event,
    "Encounter": _encounter_to_event,
    "MedicationRequest": _medication_to_event,
}


def load_bundle(path: str, source_id: str) -> list[Event]:
    """Read a FHIR Bundle JSON and return Events for known resource types."""
    with Path(path).open() as f:
        bundle = json.load(f)

    events: list[Event] = []
    for entry in bundle.get("entry", []):
        r = entry.get("resource", {})
        rtype = r.get("resourceType")
        handler = _DISPATCH.get(rtype)
        if handler is None:
            continue
        ev = handler(r, source_id)
        if ev is not None:
            events.append(ev)
    return events
