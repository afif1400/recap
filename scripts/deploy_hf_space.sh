#!/usr/bin/env bash
set -euo pipefail

# Deploy current master to the HF Space, swapping README.md for the
# frontmatter-prefixed version. master stays clean for GitHub.
#
# Usage:  ./scripts/deploy_hf_space.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${REPO_ROOT}"

SPACE_REMOTE="space"
SPACE_URL="https://huggingface.co/spaces/lablab-ai-amd-developer-hackathon/recap"

git remote get-url "${SPACE_REMOTE}" >/dev/null 2>&1 || git remote add "${SPACE_REMOTE}" "${SPACE_URL}"

./scripts/build_hf_readme.sh

CURRENT_BRANCH="$(git symbolic-ref --short HEAD)"
git checkout -B hf-deploy
cp space/README.md README.md
git add README.md
git commit -q -m "deploy: hf space readme with sdk frontmatter" || echo "no readme change"
git push -f "${SPACE_REMOTE}" hf-deploy:master
git checkout "${CURRENT_BRANCH}"
git checkout -- README.md

echo
echo "Pushed to ${SPACE_URL}"
echo "Watch the build at: ${SPACE_URL}?logs=build"
