#!/usr/bin/env bash
# Production launch: MedGemma-27B-MM + Qwen3.6-27B co-resident on the MI300X.
# Runs in foreground — wrap in `tmux new -s recap` so you can detach.

set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

GREEN='\033[32m'; DIM='\033[2m'; RESET='\033[0m'
step() { echo -e "\n${GREEN}==>${RESET} $*"; }

# Production model defaults (already in serve.py, set explicitly for clarity)
export MEDGEMMA_ID="${MEDGEMMA_ID:-google/medgemma-27b-it}"
export QWEN_ID="${QWEN_ID:-Qwen/Qwen3.6-27B}"
export RECAP_EAGER_LOAD=1

step "Models"
echo "  MedGemma: ${MEDGEMMA_ID}"
echo "  Qwen:     ${QWEN_ID}"
echo
step "Starting uvicorn on 0.0.0.0:8080"
echo -e "${DIM}First boot pulls ~50 GB of weights — go grab coffee.${RESET}"
echo -e "${DIM}Watch for 'total peak ~108 GB' to confirm both models loaded.${RESET}"
echo
exec .venv/bin/uvicorn backend.server:app --host 0.0.0.0 --port 8080
