"""Two-stage reasoner: MedGemma extracts evidence, Qwen writes the answer."""

from __future__ import annotations

from typing import Callable, Protocol


EXTRACT_SYSTEM = (
    "You are a medical evidence extractor. Given a patient's records and a "
    "question, identify the most relevant data points and quote them verbatim. "
    "Always include the source citation in [src:source_id] or "
    "[src:source_id#p<page>] format. Do not synthesize, interpret, or speculate "
    "— extract only."
)

SYNTHESIZE_SYSTEM = (
    "You are a careful medical reading assistant. You will be given:\n"
    "1. A user question\n"
    "2. Evidence extracted from the patient's records, with citations\n\n"
    "Synthesize a 2-4 sentence answer using only the evidence. Preserve every "
    "[src:...] citation exactly as given. If the evidence is insufficient, say "
    "so. Never give medical advice or recommend treatment changes."
)


class GenerateFn(Protocol):
    def __call__(self, system: str, user: str) -> str: ...


def two_stage(
    question: str,
    retrieved_block: str,
    *,
    extract_fn: GenerateFn,
    synthesize_fn: GenerateFn,
) -> str:
    extract_user = (
        f"Patient records:\n{retrieved_block}\n\n"
        f"Question: {question}\n\n"
        "Extract the most relevant data points with citations:"
    )
    evidence = extract_fn(EXTRACT_SYSTEM, extract_user).strip()

    synth_user = f"Question: {question}\n\nEvidence:\n{evidence}\n\nAnswer:"
    return synthesize_fn(SYNTHESIZE_SYSTEM, synth_user).strip()
