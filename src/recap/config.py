import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    backend: str  # "zerogpu" | "mi300x" | "mock"
    mi300x_url: str
    medgemma_lite_id: str
    medgemma_premium_id: str
    qwen_id: str
    cases_dir: str


def load() -> Config:
    return Config(
        backend=os.getenv("RECAP_BACKEND", "zerogpu"),
        mi300x_url=os.getenv("RECAP_MI300X_URL", ""),
        medgemma_lite_id=os.getenv("RECAP_MEDGEMMA_LITE", "google/medgemma-1.5-4b-it"),
        medgemma_premium_id=os.getenv("RECAP_MEDGEMMA_PREMIUM", "google/medgemma-27b-it"),
        qwen_id=os.getenv("RECAP_QWEN", "Qwen/Qwen3.6-27B"),
        cases_dir=os.getenv("RECAP_CASES_DIR", "data/cases"),
    )
