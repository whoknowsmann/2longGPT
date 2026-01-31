"""Document ingestion adapter."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pypdf import PdfReader

from opennote.adapters.types import IngestResult

SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".md"}


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages).strip()


def ingest_document(path: str) -> IngestResult:
    doc_path = Path(path).expanduser().resolve()
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found at {doc_path}")

    suffix = doc_path.suffix.lower()
    if suffix not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise ValueError(f"Unsupported document format: {suffix}")

    if suffix == ".pdf":
        raw_text = _read_pdf(doc_path)
    else:
        raw_text = doc_path.read_text(encoding="utf-8")

    metadata = {
        "title": doc_path.stem,
        "source_url": None,
        "duration_seconds": None,
        "source_type": "document",
        "date": date.today().isoformat(),
    }
    return IngestResult(raw_text=raw_text, segments=[], metadata=metadata)
