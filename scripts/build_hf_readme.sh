#!/usr/bin/env bash
# Assemble the HF-Space-bound README by prepending the HF YAML frontmatter
# to the GitHub README. Outputs to space/README.md.
#
# Run before pushing to the HF Space remote.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HEADER="${REPO_ROOT}/space/header.md"
BODY="${REPO_ROOT}/README.md"
OUT="${REPO_ROOT}/space/README.md"

cat "${HEADER}" "${BODY}" > "${OUT}"
echo "Wrote ${OUT} ($(wc -l < "${OUT}") lines)"
