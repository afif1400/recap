"""Parse PDFs into per-page records with source metadata for citation grounding."""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PdfPage:
    source_id: str
    page_number: int  # 1-indexed
    text: str


def load_pdf(path: str, source_id: str | None = None) -> list[PdfPage]:
    src = source_id or Path(path).name
    reader = PdfReader(path)
    return [
        PdfPage(source_id=src, page_number=i, text=page.extract_text() or "")
        for i, page in enumerate(reader.pages, start=1)
    ]
