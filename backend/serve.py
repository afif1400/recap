"""Loads MedGemma-27B-MM + Qwen-32B co-resident on a single AMD MI300X.

Designed to run inside the FastAPI server on the droplet. Models are loaded
lazily (first request triggers load) so the health endpoint is responsive
even before the heavy weights touch GPU memory.
"""

from __future__ import annotations

import os
import time
from threading import Lock
from typing import Any

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoModelForImageTextToText,
    AutoProcessor,
    AutoTokenizer,
)

MEDGEMMA_ID = os.getenv("MEDGEMMA_ID", "google/medgemma-27b-it")
QWEN_ID = os.getenv("QWEN_ID", "Qwen/Qwen3.6-27B")

DEVICE = "cuda:0"
DTYPE = torch.bfloat16

_state: dict[str, Any] = {"loaded": False}
_lock = Lock()


def _ensure_loaded() -> None:
    """Load both models into GPU memory once. Idempotent + thread-safe."""
    if _state["loaded"]:
        return
    with _lock:
        if _state["loaded"]:  # double-checked
            return

        t0 = time.time()
        print(f"[serve] loading MedGemma: {MEDGEMMA_ID}", flush=True)
        _state["medgemma_proc"] = AutoProcessor.from_pretrained(MEDGEMMA_ID)
        _state["medgemma"] = AutoModelForImageTextToText.from_pretrained(
            MEDGEMMA_ID, torch_dtype=DTYPE, device_map=DEVICE,
        )
        torch.cuda.synchronize()
        peak_after_mg = torch.cuda.max_memory_allocated() / 1e9
        print(f"[serve] medgemma loaded in {time.time() - t0:.1f}s, peak {peak_after_mg:.1f} GB", flush=True)

        t1 = time.time()
        print(f"[serve] loading Qwen: {QWEN_ID}", flush=True)
        _state["qwen_tok"] = AutoTokenizer.from_pretrained(QWEN_ID)
        _state["qwen"] = AutoModelForCausalLM.from_pretrained(
            QWEN_ID, torch_dtype=DTYPE, device_map=DEVICE,
        )
        torch.cuda.synchronize()
        peak = torch.cuda.max_memory_allocated() / 1e9
        print(f"[serve] qwen loaded in {time.time() - t1:.1f}s, total peak {peak:.1f} GB", flush=True)

        _state["loaded"] = True
        _state["peak_after_load_gb"] = peak


def memory_stats() -> dict[str, float]:
    if not torch.cuda.is_available():
        return {"available": False}
    return {
        "available": True,
        "allocated_gb": torch.cuda.memory_allocated() / 1e9,
        "reserved_gb": torch.cuda.memory_reserved() / 1e9,
        "total_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
        "peak_after_load_gb": _state.get("peak_after_load_gb"),
        "device_name": torch.cuda.get_device_name(0),
    }


def medgemma_extract(system: str, user: str, max_new_tokens: int = 384) -> str:
    """First stage of the two-stage reasoner: read records, surface relevant findings."""
    _ensure_loaded()
    msgs = [
        {"role": "system", "content": [{"type": "text", "text": system}]},
        {"role": "user",   "content": [{"type": "text", "text": user}]},
    ]
    inputs = _state["medgemma_proc"].apply_chat_template(
        msgs, add_generation_prompt=True, tokenize=True,
        return_dict=True, return_tensors="pt",
    ).to(DEVICE)
    out = _state["medgemma"].generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
    )
    new_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return _state["medgemma_proc"].decode(new_tokens, skip_special_tokens=True)


def qwen_synthesize(system: str, user: str, max_new_tokens: int = 512) -> str:
    """Second stage: synthesize MedGemma's findings into the final cited answer."""
    _ensure_loaded()
    msgs = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]
    text = _state["qwen_tok"].apply_chat_template(
        msgs, add_generation_prompt=True, tokenize=False,
    )
    inputs = _state["qwen_tok"](text, return_tensors="pt").to(DEVICE)
    out = _state["qwen"].generate(
        **inputs, max_new_tokens=max_new_tokens, do_sample=False,
    )
    new_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return _state["qwen_tok"].decode(new_tokens, skip_special_tokens=True)
