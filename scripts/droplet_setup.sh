#!/usr/bin/env bash
# One-shot setup for a fresh AMD Developer Cloud MI300X droplet (ROCm 7.x image).
# Idempotent — safe to re-run.
#
# Usage on the droplet:
#   git clone https://github.com/afif1400/recap.git
#   cd recap
#   bash scripts/droplet_setup.sh

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
GREEN='\033[32m'; RED='\033[31m'; DIM='\033[2m'; RESET='\033[0m'

step() { echo -e "\n${GREEN}==>${RESET} $*"; }
warn() { echo -e "${RED}!! $*${RESET}"; }
info() { echo -e "${DIM}   $*${RESET}"; }

step "Pre-flight: check GPU + Python"
if ! command -v rocminfo >/dev/null; then
  warn "rocminfo not found — is this a ROCm image?"
  exit 1
fi
GPU_NAME="$(rocminfo | awk -F': ' '/Marketing Name/ {print $2; exit}')"
info "GPU: ${GPU_NAME}"
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
info "Python: ${PY_VER}"

if [[ "${PY_VER}" < "3.10" ]]; then
  warn "Python ${PY_VER} too old; need 3.10+"
  exit 1
fi

step "Create virtualenv"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  info "Created .venv"
else
  info ".venv already exists — reusing"
fi
source .venv/bin/activate
pip install --upgrade pip wheel --quiet

step "Install ROCm-flavored torch (this is the slow step, ~3-5 min)"
if python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
  info "torch already installed and CUDA-available — skipping"
else
  pip install --pre torch \
    --index-url https://download.pytorch.org/whl/nightly/rocm6.2 \
    --quiet
fi
python -c "import torch; print(f'   torch {torch.__version__} | hip {torch.version.hip} | cuda_avail={torch.cuda.is_available()}')"

step "Install backend requirements"
pip install -r backend/requirements.txt --quiet
info "fastapi, uvicorn, transformers, accelerate ready"

step "Setup complete"
info "Next:"
info "  bash scripts/droplet_smoke.sh   # validates with a tiny model first"
info "  bash scripts/droplet_run.sh     # production launch (27B + 27B)"
info "  bash scripts/droplet_tunnel.sh  # public URL via cloudflared"
