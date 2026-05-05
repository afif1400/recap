"""Synthetic Sarah Johnson — CKD progression over 8 years, generated in memory.

Used so the UI is functional before real Synthea data is curated. Once
`data/cases/sarah/` exists with a manifest, the case loader takes over
and this is no longer used.
"""

from datetime import datetime, timedelta, timezone

from recap.models import Event, Patient


def _ev(eid: str, date: datetime, category: str, title: str, source: str, body: str = "") -> Event:
    return Event(
        id=eid,
        date=date,
        category=category,
        title=title,
        source=source,
        body=body or title,
    )


def build_demo_patient() -> Patient:
    """Build a richly-populated synthetic patient for UI demo purposes."""
    base = datetime(2017, 1, 15, tzinfo=timezone.utc)
    events: list[Event] = []

    # Initial diagnosis (2017): T2DM
    events.append(_ev("dx-1", base, "diagnosis", "Type 2 diabetes mellitus",
                      "fhir.json", "Diagnosis: Type 2 diabetes mellitus, newly identified"))
    events.append(_ev("v-1", base, "visit", "Annual physical exam", "fhir.json"))
    events.append(_ev("med-1", base + timedelta(days=2), "med", "Metformin 500mg BID",
                      "fhir.json", "Prescribed: Metformin 500mg twice daily"))

    # Year 1-3: stable, occasional labs
    cr_values = [0.9, 0.95, 1.0, 1.0, 1.05, 1.1]  # creatinine slowly rising
    a1c_values = [7.4, 7.2, 7.0, 7.1, 6.9, 7.3]
    for i, (cr, a1c) in enumerate(zip(cr_values, a1c_values)):
        d = base + timedelta(days=180 * (i + 1))
        events.append(_ev(f"lab-cr-{i}", d, "lab", f"Creatinine: {cr} mg/dL",
                          f"lab_{d.date()}.pdf",
                          f"Creatinine value: {cr} mg/dL (Reference: 0.6-1.2)"))
        events.append(_ev(f"lab-a1c-{i}", d, "lab", f"HbA1c: {a1c}%",
                          f"lab_{d.date()}.pdf",
                          f"HbA1c value: {a1c}% (Target: <7.0)"))

    # Year 4 (2021): first abnormal Cr — kidney decline begins
    decline_start = datetime(2021, 3, 14, tzinfo=timezone.utc)
    events.append(_ev("lab-cr-abnormal", decline_start, "lab", "Creatinine: 1.4 mg/dL (high)",
                      f"lab_{decline_start.date()}.pdf",
                      "Creatinine value: 1.4 mg/dL (FIRST abnormal — reference 0.6-1.2)"))
    events.append(_ev("lab-egfr-abnormal", decline_start, "lab", "eGFR: 52 mL/min/1.73m²",
                      f"lab_{decline_start.date()}.pdf",
                      "eGFR value: 52 (low — stage 3 CKD threshold)"))
    events.append(_ev("rep-cmp-1", decline_start, "report",
                      "Comprehensive metabolic panel",
                      f"lab_{decline_start.date()}.pdf",
                      "Mildly elevated creatinine consistent with stage 3 CKD."))

    # Nephrology referral
    nephro = decline_start + timedelta(days=45)
    events.append(_ev("v-nephro-1", nephro, "visit", "Nephrology consultation",
                      "fhir.json", "Referred for evaluation of declining renal function."))
    events.append(_ev("dx-ckd", nephro, "diagnosis", "Chronic kidney disease, stage 3",
                      "fhir.json", "Diagnosis: CKD stage 3, likely diabetic nephropathy."))
    events.append(_ev("med-ace", nephro + timedelta(days=2), "med", "Lisinopril 10mg daily",
                      "fhir.json", "Prescribed: Lisinopril 10mg for renal protection."))

    # Renal ultrasound
    us = nephro + timedelta(days=10)
    events.append(_ev("proc-us", us, "procedure", "Renal ultrasound",
                      "fhir.json", "Bilateral kidneys imaged."))
    events.append(_ev("scan-us", us, "scan", "Renal ultrasound (bilateral)",
                      "kidney_us_2021.png",
                      "Imaging: bilateral renal cortices mildly thinned, no obstruction."))

    # Year 5 (2022): continued decline
    cr_2022 = [1.5, 1.6, 1.55]
    for i, cr in enumerate(cr_2022):
        d = datetime(2022, 3 + i * 4, 1, tzinfo=timezone.utc)
        events.append(_ev(f"lab-cr-22-{i}", d, "lab", f"Creatinine: {cr} mg/dL",
                          f"lab_{d.date()}.pdf",
                          f"Creatinine value: {cr} mg/dL (continued elevation)"))

    # Diabetic retinopathy screening (2023)
    eye = datetime(2023, 4, 1, tzinfo=timezone.utc)
    events.append(_ev("v-ophth-1", eye, "visit", "Diabetic retinopathy screening", "fhir.json"))
    events.append(_ev("scan-fundus", eye, "scan", "Right fundus photograph",
                      "fundus_2023.png",
                      "Mild non-proliferative diabetic retinopathy in right eye."))
    events.append(_ev("dx-dr", eye, "diagnosis", "Mild non-proliferative diabetic retinopathy",
                      "fhir.json", "Diagnosis: NPDR, mild — annual follow-up."))

    # Recent (2024-2025): stable on lisinopril
    for i, cr in enumerate([1.6, 1.55, 1.6, 1.7]):
        d = datetime(2024, 3 + i * 3, 1, tzinfo=timezone.utc)
        events.append(_ev(f"lab-cr-24-{i}", d, "lab", f"Creatinine: {cr} mg/dL",
                          f"lab_{d.date()}.pdf"))

    return Patient(
        id="demo",
        display_name="Sarah Johnson, 67 (demo)",
        age=67,
        gender="female",
        events=events,
    )
