"""Recap — FastAPI app entry point. Serves the React UI + JSON inference API.

GET  /                  → static index.html (React via CDN, Babel-compiled JSX in browser)
GET  /static/*          → static assets (app.jsx, css)
GET  /api/patients      → list of patients with full event timelines
POST /api/answer        → run the inference gateway and return a cited answer
GET  /api/health        → liveness + backend selection
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from recap.cases import load_case
from recap.config import load as load_config
from recap.demo_patient import build_demo_patient
from recap.inference import answer as answer_question
from recap.models import Patient


CFG = load_config()
ROOT = Path(__file__).parent
STATIC_DIR = ROOT / "static"


def _discover_cases() -> dict[str, Patient]:
    cases: dict[str, Patient] = {}
    cases_dir = Path(CFG.cases_dir)
    if cases_dir.exists():
        for d in sorted(cases_dir.iterdir()):
            if (d / "manifest.json").exists():
                try:
                    cases[d.name] = load_case(CFG.cases_dir, d.name)
                except Exception as e:  # noqa: BLE001 — keep one bad case from breaking the whole API
                    print(f"[recap] failed to load case {d.name}: {e}")
    if not cases:
        cases["demo"] = build_demo_patient()
    return cases


PATIENTS: dict[str, Patient] = _discover_cases()


app = FastAPI(title="Recap", version="0.1.0")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class AnswerRequest(BaseModel):
    patient_id: str
    question: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/patients")
def list_patients() -> JSONResponse:
    """Serialize all loaded patients in a shape the React app expects."""
    out = []
    for pid, p in PATIENTS.items():
        out.append({
            "id": p.id,
            "display_name": p.display_name,
            "age": p.age,
            "gender": p.gender,
            "mrn": getattr(p, "mrn", None) or f"MRN-{abs(hash(p.id)) % 9999999:07d}",
            "summary": _patient_summary(p),
            "hook": _patient_hook(p),
            "tags": _patient_tags(p),
            "events": [_event_to_dict(e) for e in p.events],
        })
    return JSONResponse(out)


@app.post("/api/answer")
def answer(req: AnswerRequest) -> JSONResponse:
    if req.patient_id not in PATIENTS:
        return JSONResponse({"error": f"unknown patient {req.patient_id}"}, status_code=404)
    p = PATIENTS[req.patient_id]
    a = answer_question(req.question, p.events)
    return JSONResponse({
        "text": a.text,
        "citations": [
            {"source_id": c.source_id, "page": c.page, "snippet": c.snippet}
            for c in a.citations
        ],
    })


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({
        "ok": True,
        "backend": CFG.backend,
        "patient_count": len(PATIENTS),
        "patient_ids": list(PATIENTS.keys()),
    })


# ─── Helpers ───────────────────────────────────────────────────────────


def _event_to_dict(e) -> dict:
    return {
        "id": e.id,
        "date": e.date.date().isoformat(),
        "category": e.category,
        "title": e.title,
        "source": e.source,
        "body": e.body,
        "page": e.metadata.get("page"),
        "snippet": e.metadata.get("snippet"),
        "flag": e.metadata.get("flag"),
    }


def _patient_summary(p: Patient) -> str:
    """One-sentence dossier summary. Real cases override via manifest.summary later."""
    n = len(p.events)
    years = sorted({e.date.year for e in p.events})
    span = f"{years[0]}–{years[-1]}" if years else "no record"
    return f"{n} clinical events on file from {span}."


def _patient_hook(p: Patient) -> str:
    return ""


def _patient_tags(p: Patient) -> list[str]:
    """Surface the most recent diagnosis titles as tag chips."""
    dx = [e.title for e in sorted(p.events, key=lambda e: e.date, reverse=True) if e.category == "diagnosis"]
    return dx[:3]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
