"""Recap — Gradio app entry point. HF Spaces boots from this file."""

from pathlib import Path

import gradio as gr

from recap.cases import load_case
from recap.config import load as load_config
from recap.demo_patient import build_demo_patient
from recap.inference import answer as answer_question
from recap.models import Patient
from recap.ui import build_timeline_figure


CFG = load_config()


def _discover_cases() -> dict[str, Patient]:
    cases: dict[str, Patient] = {}
    cases_dir = Path(CFG.cases_dir)
    if cases_dir.exists():
        for d in sorted(cases_dir.iterdir()):
            if (d / "manifest.json").exists():
                try:
                    cases[d.name] = load_case(CFG.cases_dir, d.name)
                except Exception as e:  # noqa: BLE001 — keep one bad case from breaking the whole UI
                    print(f"[recap] failed to load case {d.name}: {e}")
    if not cases:
        cases["demo"] = build_demo_patient()
    return cases


PATIENTS = _discover_cases()
DEFAULT_CASE = next(iter(PATIENTS))


DISCLAIMER = (
    "⚠️ **Demo only.** Not a clinical tool. Synthetic patients only — no real PHI. "
    "Outputs may be wrong; do not use for medical decisions."
)

ABOUT = """\
**Recap** is a longitudinal patient-records copilot built for the
[AMD x LabLab.ai Developer Hackathon](https://lablab.ai/ai-hackathons/amd-developer).

Drop in a patient's scattered records — labs, scans, photos, discharge summaries —
and Recap shows you a chronological timeline plus a chat where every answer is
cited back to the exact source. The premium-mode backend runs MedGemma + Qwen
co-resident on a single AMD MI300X (192 GB).
"""


def render_for(case_id: str):
    p = PATIENTS[case_id]
    fig = build_timeline_figure(p)
    bio = (
        f"### {p.display_name}\n"
        f"{len(p.events)} events across {len({e.date.year for e in p.events})} year(s).  "
        f"Gender: {p.gender or 'unknown'}.  Age: {p.age if p.age is not None else 'unknown'}."
    )
    return fig, bio


def chat_fn(message: str, history, case_id: str, backend: str):
    import os
    os.environ["RECAP_BACKEND"] = backend
    p = PATIENTS[case_id]
    a = answer_question(message, p.events)
    if a.citations:
        cite_lines = []
        for c in a.citations:
            ref = f"`{c.source_id}`"
            if c.page is not None:
                ref += f" p.{c.page}"
            if c.snippet:
                ref += f" — *{c.snippet}*"
            cite_lines.append(ref)
        return a.text + "\n\n**Sources:**\n- " + "\n- ".join(cite_lines)
    return a.text


def example_questions(case_id: str) -> list[list[str]]:
    p = PATIENTS[case_id]
    if p.id == "demo" or "Sarah" in p.display_name:
        return [
            ["When did her kidney function start declining?"],
            ["What was her first abnormal creatinine reading?"],
            ["What medications was she on when CKD was diagnosed?"],
        ]
    return [["Summarize this patient's history in 3 sentences."]]


with gr.Blocks(title="Recap", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🩺 Recap")
    gr.Markdown("*Reads the whole chart so you don't have to.*")
    gr.Markdown(DISCLAIMER)

    with gr.Accordion("About", open=False):
        gr.Markdown(ABOUT)

    with gr.Row():
        case_dropdown = gr.Dropdown(
            choices=list(PATIENTS.keys()),
            value=DEFAULT_CASE,
            label="Showcase patient",
            scale=2,
        )
        backend_choice = gr.Radio(
            choices=["mock", "zerogpu", "mi300x"],
            value=CFG.backend,
            label="Inference backend",
            scale=1,
            info="mock = offline canned reply; zerogpu = MedGemma-4B on H200; mi300x = full premium mode",
        )

    summary = gr.Markdown()
    plot = gr.Plot()

    chat = gr.ChatInterface(
        fn=chat_fn,
        additional_inputs=[case_dropdown, backend_choice],
        examples=example_questions(DEFAULT_CASE),
        chatbot=gr.Chatbot(height=320),
    )

    case_dropdown.change(fn=render_for, inputs=case_dropdown, outputs=[plot, summary])
    demo.load(fn=render_for, inputs=case_dropdown, outputs=[plot, summary])


if __name__ == "__main__":
    demo.launch()
