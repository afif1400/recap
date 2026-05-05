"""Deploy current working tree to the HF Space via HfApi.upload_folder.

Bypasses git push (and macOS keychain credential issues). Uses the locally
configured HF token. Run after committing locally if you want git history
on GitHub to match what's on the Space.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

REPO_ID = "lablab-ai-amd-developer-hackathon/recap"
ROOT = Path(__file__).resolve().parent.parent

IGNORE = {
    ".git", ".venv", "venv", "env",
    "__pycache__", ".pytest_cache",
    "docs", "node_modules",
    ".DS_Store",
}


def _build_hf_readme(staging: Path) -> None:
    """Concatenate space/header.md + README.md into staging/README.md."""
    header = (ROOT / "space" / "header.md").read_text()
    body = (ROOT / "README.md").read_text()
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        body = body[end + 5:].lstrip() if end != -1 else body
    (staging / "README.md").write_text(header + body)


def _copy_to_staging(staging: Path) -> None:
    for entry in ROOT.iterdir():
        if entry.name in IGNORE:
            continue
        dst = staging / entry.name
        if entry.is_dir():
            shutil.copytree(entry, dst, ignore=shutil.ignore_patterns(*IGNORE))
        else:
            shutil.copy2(entry, dst)


def main() -> None:
    api = HfApi()

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        _copy_to_staging(staging)
        _build_hf_readme(staging)

        rev_short = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        ).stdout.strip()
        commit_msg = f"deploy: sync from {rev_short or 'local'}"

        print(f"Uploading {len(list(staging.rglob('*')))} entries to {REPO_ID}…")
        api.upload_folder(
            folder_path=str(staging),
            repo_id=REPO_ID,
            repo_type="space",
            commit_message=commit_msg,
        )

    print(f"Done. https://huggingface.co/spaces/{REPO_ID}")


if __name__ == "__main__":
    main()
