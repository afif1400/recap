"""Smoke tests for BACKEND_FAKE=1 mode — the path used to validate plumbing
without GPU. These tests don't require torch."""

import importlib
import os
import sys


def _reload_serve():
    """Force re-import so module-level FAKE env is re-read."""
    if "backend.serve" in sys.modules:
        del sys.modules["backend.serve"]
    if "backend" in sys.modules:
        del sys.modules["backend"]
    return importlib.import_module("backend.serve")


def test_fake_mode_does_not_import_torch(monkeypatch):
    monkeypatch.setenv("BACKEND_FAKE", "1")
    serve = _reload_serve()
    assert serve.FAKE is True
    # Calling extract/synthesize must not raise even without torch.
    out = serve.medgemma_extract("sys", "[src:lab.pdf] something on 2022-03-14")
    assert "[src:lab.pdf]" in out
    out2 = serve.qwen_synthesize("sys", "Question: q\n\nEvidence: [src:lab.pdf]")
    assert "[src:lab.pdf]" in out2


def test_memory_stats_reports_fake_mode(monkeypatch):
    monkeypatch.setenv("BACKEND_FAKE", "1")
    serve = _reload_serve()
    stats = serve.memory_stats()
    assert stats["available"] is False
    assert stats["mode"] == "fake"


def test_fake_extracts_first_source_token(monkeypatch):
    monkeypatch.setenv("BACKEND_FAKE", "1")
    serve = _reload_serve()
    out = serve.medgemma_extract("sys", "records [src:lab_a.pdf] [src:lab_b.pdf]")
    assert "lab_a.pdf" in out
    assert "lab_b.pdf" not in out
