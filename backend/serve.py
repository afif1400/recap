"""MedGemma + Qwen co-resident loader for the AMD MI300X.

Set BACKEND_FAKE=1 to skip model loading entirely and return canned text —
useful for testing the HTTP plumbing on a Mac without torch installed.
"""

from __future__ import annotations

import os
import time
from threading import Lock
from typing import Any

MEDGEMMA_ID = os.getenv("MEDGEMMA_ID", "google/medgemma-27b-it")
QWEN_ID = os.getenv("QWEN_ID", "Qwen/Qwen3.6-27B")
FAKE = os.getenv("BACKEND_FAKE", "0") == "1"

_state: dict[str, Any] = {"loaded": False}
_lock = Lock()


def _ensure_loaded() -> None:
    if FAKE or _state["loaded"]:
        return
    with _lock:
        if _state["loaded"]:
            return

        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoModelForImageTextToText,
            AutoProcessor,
            AutoTokenizer,
        )

        device = "cuda:0"
        dtype = torch.bfloat16

        t0 = time.time()
        print(f"[serve] loading MedGemma: {MEDGEMMA_ID}", flush=True)
        _state["medgemma_proc"] = AutoProcessor.from_pretrained(MEDGEMMA_ID)
        _state["medgemma"] = AutoModelForImageTextToText.from_pretrained(
            MEDGEMMA_ID, torch_dtype=dtype, device_map=device,
        )
        torch.cuda.synchronize()
        peak_after_mg = torch.cuda.max_memory_allocated() / 1e9
        print(f"[serve] medgemma loaded in {time.time() - t0:.1f}s, peak {peak_after_mg:.1f} GB", flush=True)

        t1 = time.time()
        print(f"[serve] loading Qwen: {QWEN_ID}", flush=True)
        _state["qwen_tok"] = AutoTokenizer.from_pretrained(QWEN_ID)
        _state["qwen"] = AutoModelForCausalLM.from_pretrained(
            QWEN_ID, torch_dtype=dtype, device_map=device,
        )
        torch.cuda.synchronize()
        peak = torch.cuda.max_memory_allocated() / 1e9
        print(f"[serve] qwen loaded in {time.time() - t1:.1f}s, total peak {peak:.1f} GB", flush=True)

        _state["torch"] = torch
        _state["device"] = device
        _state["loaded"] = True
        _state["peak_after_load_gb"] = peak


def memory_stats() -> dict[str, Any]:
    if FAKE:
        return {"available": False, "mode": "fake"}
    try:
        import torch
    except ImportError:
        return {"available": False, "mode": "no-torch"}
    if not torch.cuda.is_available():
        return {"available": False, "mode": "no-cuda"}
    return {
        "available": True,
        "allocated_gb": torch.cuda.memory_allocated() / 1e9,
        "reserved_gb": torch.cuda.memory_reserved() / 1e9,
        "total_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
        "peak_after_load_gb": _state.get("peak_after_load_gb"),
        "device_name": torch.cuda.get_device_name(0),
    }


def _fake_medgemma(user: str) -> str:
    import re
    sources = re.findall(r"\[src:([^\]]+)\]", user)
    src = sources[0] if sources else "fhir.json"
    dates = re.findall(r"(\d{4}-\d{2}-\d{2})", user)
    earliest = min(dates) if dates else "2022-03-14"
    return (
        f"Earliest relevant finding: {earliest} — entry surfaced by retrieval "
        f"[src:{src}]. (BACKEND_FAKE=1; real medgemma extraction would identify "
        f"specific values, units, and reference ranges.)"
    )


def _fake_qwen(user: str) -> str:
    import re
    cite = re.search(r"\[src:[^\]]+\]", user) or "[src:fhir.json]"
    cite_str = cite.group() if hasattr(cite, "group") else str(cite)
    return (
        f"Based on the records, the earliest signal in the timeline points to "
        f"a finding around the dates retrieved {cite_str}. This is a fake "
        f"response from BACKEND_FAKE=1 — when the MI300X backend is up with "
        f"BACKEND_FAKE=0, this answer comes from Qwen 3.6-27B synthesizing "
        f"MedGemma-27B-MM's evidence extraction."
    )


def medgemma_extract(system: str, user: str, max_new_tokens: int = 384) -> str:
    if FAKE:
        return _fake_medgemma(user)
    _ensure_loaded()
    torch = _state["torch"]
    device = _state["device"]
    msgs = [
        {"role": "system", "content": [{"type": "text", "text": system}]},
        {"role": "user",   "content": [{"type": "text", "text": user}]},
    ]
    inputs = _state["medgemma_proc"].apply_chat_template(
        msgs, add_generation_prompt=True, tokenize=True,
        return_dict=True, return_tensors="pt",
    ).to(device)
    out = _state["medgemma"].generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
    )
    new_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return _state["medgemma_proc"].decode(new_tokens, skip_special_tokens=True)


def qwen_synthesize(system: str, user: str, max_new_tokens: int = 512) -> str:
    if FAKE:
        return _fake_qwen(user)
    _ensure_loaded()
    torch = _state["torch"]
    device = _state["device"]
    msgs = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    text = _state["qwen_tok"].apply_chat_template(
        msgs, add_generation_prompt=True, tokenize=False,
    )
    inputs = _state["qwen_tok"](text, return_tensors="pt").to(device)
    out = _state["qwen"].generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
    )
    new_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return _state["qwen_tok"].decode(new_tokens, skip_special_tokens=True)
