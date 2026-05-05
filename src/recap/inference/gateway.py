"""Gateway: question in, cited Answer out.

This is the only place the rest of the codebase talks to. The UI calls
`answer(...)`; the gateway handles retrieval, prompt assembly, backend
routing, and citation parsing. Backends (mock/zerogpu/mi300x) are imported
lazily so importing this module doesn't drag in torch on a CPU laptop.
"""

import re

from recap.config import load
from recap.models import Answer, Citation, Event
from recap.prompts import PATIENT_QA_SYSTEM, build_user_prompt
from recap.retrieval import retrieve

_CITATION_RE = re.compile(r"\[src:([^\]#]+)(?:#p(\d+))?\]")


def answer(question: str, events: list[Event], top_k: int = 6) -> Answer:
    """Run the full question→retrieved→generated→cited pipeline."""
    cfg = load()
    retrieved = retrieve(question, events, top_k=top_k)
    user_prompt = build_user_prompt(question, retrieved)
    text = _generate(cfg.backend, PATIENT_QA_SYSTEM, user_prompt)
    citations = _parse_citations(text, retrieved)
    return Answer(text=text, citations=citations)


def _generate(backend: str, system: str, user: str) -> str:
    if backend == "mi300x":
        from recap.inference.mi300x_client import generate_premium

        return generate_premium(system=system, user=user)
    if backend == "mock":
        from recap.inference.mock import generate_mock

        return generate_mock(system=system, user=user)
    # default: zerogpu
    from recap.inference.zerogpu import generate_lite

    return generate_lite(system=system, user=user)


def _parse_citations(text: str, retrieved: list[Event]) -> list[Citation]:
    """Extract `[src:foo#p2]` markers and resolve each to a Citation.

    Drops citations to sources that weren't in the retrieved set (defensive
    against the model hallucinating a source name it never saw).
    """
    by_source: dict[str, Event] = {e.source: e for e in retrieved}
    seen: set[tuple[str, int | None]] = set()
    out: list[Citation] = []
    for m in _CITATION_RE.finditer(text):
        src = m.group(1)
        page = int(m.group(2)) if m.group(2) else None
        if src not in by_source:
            continue
        key = (src, page)
        if key in seen:
            continue
        seen.add(key)
        out.append(Citation(source_id=src, page=page, snippet=by_source[src].title))
    return out
