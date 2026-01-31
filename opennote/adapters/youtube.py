"""YouTube ingestion adapter."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from config import settings
from datetime import date

from opennote.adapters.audio import ingest_media_file
from opennote.adapters.types import IngestResult

SUPPORTED_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
}


def _poll_for_download(url: str, download_dir: str) -> Path:
    if not download_dir:
        raise ValueError(
            "EXTERNAL_DOWNLOAD_DIR is not set. Provide a local path instead of a URL."
        )
    path = Path(download_dir).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Download directory does not exist: {path}")

    start = time.time()
    while time.time() - start < settings.MEDIA_POLL_TIMEOUT_SECONDS:
        candidates = sorted(
            (p for p in path.iterdir() if p.suffix.lower() in _supported_extensions()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            return candidates[0]
        time.sleep(settings.MEDIA_POLL_SECONDS)

    raise TimeoutError("Timed out waiting for external download to complete.")


def _supported_extensions() -> Iterable[str]:
    return SUPPORTED_EXTENSIONS


def ingest_youtube(url: str) -> IngestResult:
    media_path = _poll_for_download(url, settings.EXTERNAL_DOWNLOAD_DIR)
    ingest_result = ingest_media_file(str(media_path))
    metadata = dict(ingest_result.metadata)
    metadata["source_type"] = "youtube"
    metadata["source_url"] = url
    metadata["date"] = metadata.get("date") or date.today().isoformat()
    return IngestResult(
        raw_text=ingest_result.raw_text,
        segments=ingest_result.segments,
        metadata=metadata,
    )
