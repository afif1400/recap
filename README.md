# Recap

> *Reads the whole chart so you don't have to.*

Drop in a patient's scattered medical records — lab PDFs, scans, photos, discharge summaries — and Recap gives you back two things:

1. **A chronological timeline** of every event, color-coded by type
2. **A chat box** where you can ask plain-language questions, with every answer cited to the exact source page or lab row

No diagnosis. No treatment. Just *"read everything and answer questions about what's been read."*

## The hackathon angle

Recap is built for the [AMD x LabLab.ai Developer Hackathon](https://lablab.ai/ai-hackathons/amd-developer) (May 2026). The technical headline:

> **The only GPU with enough memory to keep a patient's whole record co-resident with the reasoner.**

The premium-mode backend runs **MedGemma-27B-MM** (medical multimodal specialist) and **Qwen-32B** (reasoning + multilingual orchestrator) **co-resident on a single AMD MI300X (192 GB HBM3)** along with cached imaging-foundation embeddings and a 128 K-token KV cache. Impossible on H100/A100 80 GB cards.

The public Hugging Face Space runs a lite version (MedGemma-4B-MM on ZeroGPU H200) so anyone can try it.

## Architecture

```
            ┌────────────── HF Space (Gradio) ──────────────┐
            │  3 preloaded showcase patients                │
            │  Plotly timeline + chat with citations        │
            └────────────────┬─────────────────┬────────────┘
                             │                 │
                  ┌──────────┴──────┐ ┌────────┴───────────┐
                  │ ZeroGPU (H200)  │ │ AMD MI300X (192GB) │
                  │ MedGemma-4B-MM  │ │ MedGemma-27B-MM    │
                  │ Always-on lite  │ │ + Qwen-32B reasoner│
                  │                 │ │ + foundation cache │
                  └─────────────────┘ └────────────────────┘
```

## Project structure

```
src/recap/
├── config.py             # env-driven config
├── models.py             # Event, Citation, Patient, Answer
├── ingestion/
│   ├── fhir.py           # Synthea bundles → events
│   ├── pdf.py            # lab PDFs → page records
│   └── image.py          # medical images → events
├── timeline.py           # chronological event view (TBD)
├── retrieval.py          # BM25 over events (TBD)
├── inference/            # gateway routing zerogpu vs mi300x (TBD)
├── reasoner.py           # two-stage MedGemma → Qwen (TBD)
└── ui/                   # Gradio components (TBD)

backend/                  # FastAPI on MI300X (TBD)
data/cases/               # showcase patients (Synthea + curated images)
scripts/                  # generators + smoke tests
space/                    # HF Space deploy artifacts
tests/                    # 13 passing unit tests
```

## Showcase cases

Built from [Synthea](https://github.com/synthetichealth/synthea) (Apache 2.0 synthetic patient generator) paired with condition-matched public imaging:

- **Sarah, 67** — kidney decline over 8 years (tests time-axis questions)
- **Marcus, 54** — suspicious lump → cancer journey (tests multimodal grounding)
- **Aisha, 29** — immigrant patient with foreign-language records (tests Qwen multilingual)

## Running locally

```bash
uv venv .venv --python 3.11
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m pytest tests/ -v       # 13 passing
.venv/bin/python app.py                    # local Gradio at :7860
```

Environment variables (all prefixed `RECAP_*`):

| Var | Default | Meaning |
|---|---|---|
| `RECAP_BACKEND` | `zerogpu` | One of `zerogpu`, `mi300x`, `mock` |
| `RECAP_MI300X_URL` | — | Premium-mode backend URL (set when the MI300X box is up) |
| `RECAP_MEDGEMMA_LITE` | `google/medgemma-1.5-4b-it` | Public-Space model |
| `RECAP_MEDGEMMA_PREMIUM` | `google/medgemma-27b-it` | MI300X model |
| `RECAP_QWEN` | `Qwen/Qwen3.6-27B` | Reasoner model — latest dense Qwen (Apr 2026), matched 27B class to MedGemma. Fallbacks: `Qwen/Qwen3-32B`, `Qwen/Qwen3-14B`, `Qwen/Qwen3.6-35B-A3B` |

## Hugging Face Space deployment

The HF Space requires YAML frontmatter at the top of its README, which GitHub renders as an ugly metadata table. To keep the GitHub README clean and the HF README correct, the frontmatter lives in `space/header.md` and the deploy script assembles a combined `space/README.md` before pushing to the HF Space remote:

```bash
./scripts/build_hf_readme.sh                # writes space/README.md
# then push space/README.md to the HF Space repo
```

## Tech stack

- **Models:** Google MedGemma 1.5 (4B-MM lite, 27B-MM premium), Alibaba **Qwen 3.6-27B** (latest, released 2026-04-22)
- **Serving:** vLLM-on-ROCm on MI300X, HF Transformers + ZeroGPU `@spaces.GPU` on the Space
- **Frontend:** Gradio 4.44, Plotly
- **Data:** Synthea synthetic FHIR + public CC0 imaging, packaged as an HF Dataset

## Disclaimer

**Not for clinical use.** Demo only. All patients are synthetic — no real PHI is touched, stored, or processed. The model card for MedGemma explicitly forbids unmodified clinical deployment.

## License

MIT (this repo). Upstream models retain their respective licenses (MedGemma → Google's Health AI Developer Foundations terms; Qwen → Tongyi Qianwen License).
