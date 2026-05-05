from __future__ import annotations

import time

import httpx

from recap.config import load
from recap.reasoner import two_stage


def _post(endpoint: str, system: str, user: str, *, timeout: float = 180.0) -> str:
    cfg = load()
    if not cfg.mi300x_url:
        raise RuntimeError(
            "RECAP_MI300X_URL is not set. Point it at the backend, e.g. "
            "RECAP_MI300X_URL=https://abc-123.ngrok-free.app"
        )
    url = f"{cfg.mi300x_url.rstrip('/')}/{endpoint}"
    payload = {"system": system, "user": user}

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = httpx.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()["text"]
        except (httpx.HTTPStatusError, httpx.TransportError) as e:
            last_err = e
            if attempt < 2:
                time.sleep(1.5 ** attempt)
    raise RuntimeError(f"MI300X backend call failed after 3 attempts: {last_err}")


def generate_premium(system: str, user: str) -> str:
    if "Question:" in user:
        block, question = user.rsplit("Question:", 1)
        retrieved_block = block.strip()
        question = question.strip()
    else:
        retrieved_block = user
        question = "Summarize what's in these records."

    return two_stage(
        question,
        retrieved_block,
        extract_fn=lambda s, u: _post("medgemma", s, u),
        synthesize_fn=lambda s, u: _post("qwen", s, u),
    )
