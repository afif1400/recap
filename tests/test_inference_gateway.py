"""Tests for the inference gateway. These exercise citation parsing and
backend routing without loading any model — the mock backend is enough.
"""

import os
from datetime import datetime

import pytest

import recap.inference.gateway as gw
from recap.models import Event


def _ev(src, date_iso="2022-03-14"):
    return Event(
        id=src,
        date=datetime.fromisoformat(date_iso),
        category="lab",
        title=f"Record from {src}",
        source=src,
    )


def test_parses_citations_from_model_output():
    text = (
        "Creatinine first crossed normal in March 2022 [src:lab_2022.pdf#p1]. "
        "eGFR was 52 [src:lab_2022.pdf]."
    )
    cites = gw._parse_citations(text, [_ev("lab_2022.pdf")])
    assert len(cites) == 2
    assert cites[0].page == 1
    assert cites[1].page is None


def test_dedupes_repeated_citations():
    text = "[src:a.pdf] said X [src:a.pdf]"
    cites = gw._parse_citations(text, [_ev("a.pdf")])
    assert len(cites) == 1


def test_drops_citations_to_unknown_sources():
    text = "[src:hallucinated.pdf]"
    cites = gw._parse_citations(text, [])
    assert cites == []


def test_dedupe_treats_different_pages_as_different_citations():
    text = "[src:a.pdf#p1] earlier [src:a.pdf#p2] later"
    cites = gw._parse_citations(text, [_ev("a.pdf")])
    assert len(cites) == 2
    assert {c.page for c in cites} == {1, 2}


def test_answer_end_to_end_with_mock_backend(monkeypatch):
    """Full pipeline: question -> retrieve -> mock -> cited answer."""
    monkeypatch.setenv("RECAP_BACKEND", "mock")
    events = [
        _ev("lab_2022.pdf", "2022-03-14"),
        _ev("visit_2023.pdf", "2023-01-01"),
    ]
    a = gw.answer("when did the lab change", events)
    assert "[mock answer]" in a.text
    assert any(c.source_id in {"lab_2022.pdf", "visit_2023.pdf"} for c in a.citations)
