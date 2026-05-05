"""System prompts and prompt builders. Centralized for easy tuning."""

PATIENT_QA_SYSTEM = """You are a careful medical reading assistant. You have access to a patient's records (labs, visits, medications, scans). When asked a question:

1. Cite the exact source for every claim using the format [src:<source_id>#p<page>] or [src:<source_id>] if no page.
2. If the answer is not in the provided records, say so explicitly.
3. Never speculate beyond what the records show.
4. Never give medical advice or recommend treatment changes.

Output format:
- A direct answer in 2-4 sentences with inline citations.
- Then a bullet list of the cited records you relied on.
"""


def build_user_prompt(question: str, retrieved_events: list) -> str:
    """Render retrieved events into the user-turn prompt."""
    lines = ["Patient records (most relevant first):", ""]
    for e in retrieved_events:
        lines.append(f"- [src:{e.source}] {e.date.date().isoformat()} — {e.title}")
        if e.body and e.body != e.title:
            lines.append(f"  {e.body}")
    lines.append("")
    lines.append(f"Question: {question}")
    return "\n".join(lines)
