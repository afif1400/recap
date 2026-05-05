"""Recap MI300X premium-mode backend. Runs on the AMD Developer Cloud droplet.

Deploy:
    cd backend
    pip install -r requirements.txt
    # ROCm torch installed separately on the droplet image.
    uvicorn backend.server:app --host 0.0.0.0 --port 8080

Then expose to the public Space via ngrok / cloudflared and set
RECAP_MI300X_URL in the Space's env to the public URL.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend import serve

EAGER_LOAD = os.getenv("RECAP_EAGER_LOAD", "1") == "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if EAGER_LOAD:
        # Load models at startup so the first /medgemma request is fast.
        # Set RECAP_EAGER_LOAD=0 if you want a fast boot for debugging.
        try:
            serve._ensure_loaded()
        except Exception as e:  # noqa: BLE001 — defer the failure to first request
            print(f"[server] eager load failed: {e}", flush=True)
    yield


app = FastAPI(title="Recap Premium Backend", version="0.1.0", lifespan=lifespan)


class GenRequest(BaseModel):
    system: str
    user: str
    max_new_tokens: int = 384


class GenResponse(BaseModel):
    text: str


@app.post("/medgemma", response_model=GenResponse)
def medgemma(req: GenRequest) -> GenResponse:
    try:
        text = serve.medgemma_extract(req.system, req.user, req.max_new_tokens)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return GenResponse(text=text)


@app.post("/qwen", response_model=GenResponse)
def qwen(req: GenRequest) -> GenResponse:
    try:
        text = serve.qwen_synthesize(req.system, req.user, req.max_new_tokens)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e)) from e
    return GenResponse(text=text)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "loaded": serve._state.get("loaded", False),
        "memory": serve.memory_stats(),
        "models": {
            "medgemma_id": serve.MEDGEMMA_ID,
            "qwen_id": serve.QWEN_ID,
        },
    }
