#!/usr/bin/env bash
# Tiny-model smoke test. Validates the whole path (HF auth, model download,
# bf16 load on ROCm, generate, decode, fastapi serve) before we commit to
# downloading 50+ GB of MedGemma-27B weights.
#
# Run after droplet_setup.sh.

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
source .venv/bin/activate

GREEN='\033[32m'; RED='\033[31m'; DIM='\033[2m'; RESET='\033[0m'
step() { echo -e "\n${GREEN}==>${RESET} $*"; }
warn() { echo -e "${RED}!! $*${RESET}"; }

if ! python -c "import huggingface_hub; assert huggingface_hub.HfApi().whoami()" 2>/dev/null; then
  warn "Not logged in to Hugging Face — run 'huggingface-cli login' first."
  warn "Token must have read access to gated MedGemma repos."
  exit 1
fi

step "Smoke test with tiny models (~6 GB total download)"
echo "  MedGemma-1.5-4b-it (vision-text)"
echo "  Qwen3-1.7B (causal LM)"

export MEDGEMMA_ID="google/medgemma-1.5-4b-it"
export QWEN_ID="Qwen/Qwen3-1.7B"
export RECAP_EAGER_LOAD=1

step "Boot backend on :8080 (logs follow; Ctrl-C when /health shows loaded=true)"
.venv/bin/uvicorn backend.server:app --host 0.0.0.0 --port 8080 &
SERVER_PID=$!
trap "kill ${SERVER_PID} 2>/dev/null; exit" INT TERM

# Wait for boot. Tail health until loaded=true or 5 min timeout.
for i in $(seq 1 30); do
  sleep 10
  if curl -sf http://localhost:8080/health 2>/dev/null | grep -q '"loaded":true'; then
    echo
    step "Smoke succeeded — health response:"
    curl -s http://localhost:8080/health | python -m json.tool
    echo
    step "Test inference round-trip"
    curl -s -X POST http://localhost:8080/medgemma \
      -H 'Content-Type: application/json' \
      -d '{"system":"Extract evidence from records","user":"records: [src:lab.pdf] Cr 1.4 mg/dL on 2022-03-14. Question: when was the first abnormal value?","max_new_tokens":128}' \
      | python -m json.tool
    echo
    kill ${SERVER_PID} 2>/dev/null || true
    step "All clear — ready for droplet_run.sh"
    exit 0
  fi
done

warn "Backend didn't reach loaded=true within 5 minutes."
warn "Tail backend.log or scroll up for errors."
kill ${SERVER_PID} 2>/dev/null || true
exit 1
