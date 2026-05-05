#!/usr/bin/env bash
# Public tunnel from the droplet's :8080 to a stable https URL.
# Uses cloudflared trycloudflare.com (no signup, ephemeral URL).
# Run in a separate tmux pane from droplet_run.sh.

set -euo pipefail

GREEN='\033[32m'; YELLOW='\033[33m'; DIM='\033[2m'; RESET='\033[0m'

if ! command -v cloudflared >/dev/null; then
  echo -e "${YELLOW}cloudflared not installed — installing now...${RESET}"
  ARCH="$(uname -m)"
  case "${ARCH}" in
    x86_64)  PKG="cloudflared-linux-amd64" ;;
    aarch64) PKG="cloudflared-linux-arm64" ;;
    *)       echo "Unsupported arch: ${ARCH}"; exit 1 ;;
  esac
  curl -fL -o /usr/local/bin/cloudflared \
    "https://github.com/cloudflare/cloudflared/releases/latest/download/${PKG}"
  chmod +x /usr/local/bin/cloudflared
fi

echo -e "${GREEN}==>${RESET} Tunneling http://localhost:8080 → public https URL"
echo -e "${DIM}Watch for the line that prints '|  https://....trycloudflare.com  |'${RESET}"
echo -e "${DIM}Send that URL to the operator to set RECAP_MI300X_URL on the Space.${RESET}"
echo
exec cloudflared tunnel --url http://localhost:8080
