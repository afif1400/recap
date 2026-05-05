# Deploying the Recap MI300X backend

Steps from a freshly-provisioned AMD Developer Cloud droplet to a working
backend talking to the live HF Space.

## 0. Prerequisites

- AMD GPU Droplet (1× MI300X, 192 GB) up and SSHable — image: ROCm 7.2
- HF token with `read` on the gated MedGemma repo (accept terms at
  https://huggingface.co/google/medgemma-27b-it)
- Cloudflared installed on your laptop (or the droplet) for tunneling

## 1. SSH and clone

```bash
ssh root@<DROPLET_IP>

# Sanity check the GPU
rocminfo | grep "Marketing Name" | head -1     # should show MI300X
python3 --version                               # 3.10+ expected on ROCm image

git clone https://github.com/afif1400/recap.git
cd recap
```

## 2. Python env

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
```

## 3. ROCm-flavored torch (this is the only ROCm-specific install)

```bash
pip install --pre torch --index-url https://download.pytorch.org/whl/nightly/rocm6.2
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.hip)"
# expect: 2.x+rocm6.2 True 6.x.x
```

## 4. Backend deps

```bash
pip install -r backend/requirements.txt
```

## 5. Authenticate to HF

```bash
huggingface-cli login   # paste write-scope token
```

## 6. Pre-flight smoke test (cheap, ~2 min)

```bash
# Tiny model first to validate the path before pulling 50 GB
MEDGEMMA_ID=google/medgemma-1.5-4b-it \
QWEN_ID=Qwen/Qwen3-1.7B \
RECAP_EAGER_LOAD=1 \
uvicorn backend.server:app --host 0.0.0.0 --port 8080
```

In another shell:
```bash
curl http://localhost:8080/health
# expect: loaded=true, allocated_gb < 10
```

If that works, the import + serving path is clean. Kill it and move on.

## 7. Production launch

```bash
# Default IDs are MedGemma-27B-MM and Qwen3.6-27B
RECAP_EAGER_LOAD=1 uvicorn backend.server:app --host 0.0.0.0 --port 8080
```

Watch the log — should print:
```
[serve] loading MedGemma: google/medgemma-27b-it
[serve] medgemma loaded in <T>s, peak ~54 GB
[serve] loading Qwen: Qwen/Qwen3.6-27B
[serve] qwen loaded in <T>s, total peak ~108 GB
```

`/health` should now report `loaded: true`.

## 8. Public tunnel (cloudflared)

On the droplet (or your laptop, forwarding via ssh):

```bash
cloudflared tunnel --url http://localhost:8080
# → prints a https URL like https://random-words.trycloudflare.com
```

That URL is the address the HF Space will hit.

## 9. Point the HF Space at the backend

In the HF Space's Settings → Variables and Secrets, add:

| name | value |
|---|---|
| `RECAP_BACKEND` | `mi300x` |
| `RECAP_MI300X_URL` | `https://<your-cloudflared>.trycloudflare.com` |

Restart the Space. Now `/api/answer` calls go through the cloudflared
tunnel to the droplet's `/medgemma` and `/qwen`.

## 10. Verify

```bash
curl -X POST https://lablab-ai-amd-developer-hackathon-recap.hf.space/api/answer \
  -H 'Content-Type: application/json' \
  -d '{"patient_id":"demo","question":"When did kidney function decline?"}'
```

Should return a real Qwen-synthesized answer with `[src:...]` citations
resolved against the showcase events.

## Common gotchas

- **`torch.cuda.is_available() == False`** on ROCm: You installed CPU torch
  by accident. `pip uninstall torch && pip install --pre torch --index-url
  https://download.pytorch.org/whl/nightly/rocm6.2`.
- **OOM on Qwen3.6-27B**: fall back via `QWEN_ID=Qwen/Qwen3-14B`.
- **ngrok/cloudflared cold start**: tunnel may take 5-15s to register.
  First request can time out — retry once.
- **HF token expired**: re-run `huggingface-cli login` on the droplet.

## Tear-down (preserve credits)

```bash
# Kill the backend process
pkill -f uvicorn
# Stop cloudflared tunnel (Ctrl+C in its terminal)
# In DigitalOcean / AMD Cloud console: power off the droplet
# (snapshot first if you want to skip step 1-4 next time)
```
