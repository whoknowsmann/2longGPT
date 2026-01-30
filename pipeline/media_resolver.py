"""Resolve media paths and metadata for processing."""

from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from config import settings

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _probe_media(path: Path) -> dict:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:format_tags=title",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed: {completed.stderr.strip() or 'unknown error'}"
        )
    if not completed.stdout:
        raise RuntimeError("ffprobe returned no output; ensure ffmpeg is installed.")
    return json.loads(completed.stdout)


def _extract_title(path: Path, probe_data: dict) -> str:
    tags = probe_data.get("format", {}).get("tags", {})
    title = tags.get("title") if isinstance(tags, dict) else None
    return title or path.stem


def _extract_duration(probe_data: dict) -> float:
    duration = probe_data.get("format", {}).get("duration")
    if duration is None:
        raise ValueError("Unable to determine media duration via ffprobe.")
    return float(duration)


def _poll_for_download(url: str, download_dir: str) -> Path:
    if not download_dir:
        raise ValueError(
            "EXTERNAL_DOWNLOAD_DIR is not set. Provide a local path instead of a URL."
        )
    path = Path(download_dir).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Download directory does not exist: {path}")

    logger.info("Polling %s for media download from %s", path, url)
    start = time.time()
    while time.time() - start < settings.MEDIA_POLL_TIMEOUT_SECONDS:
        candidates = sorted(
            (p for p in path.iterdir() if p.suffix.lower() in _supported_extensions()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            logger.info("Using downloaded media: %s", candidates[0])
            return candidates[0]
        time.sleep(settings.MEDIA_POLL_SECONDS)

    raise TimeoutError("Timed out waiting for external download to complete.")


def _supported_extensions() -> Iterable[str]:
    return SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    title: str
    duration_seconds: float
    is_video: bool


def resolve_media(input_value: str) -> MediaInfo:
    if _is_url(input_value):
        path = _poll_for_download(input_value, settings.EXTERNAL_DOWNLOAD_DIR)
    else:
        path = Path(input_value).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"Media not found at {path}")

    suffix = path.suffix.lower()
    if suffix not in _supported_extensions():
        raise ValueError(f"Unsupported media format: {suffix}")

    probe_data = _probe_media(path)
    duration = _extract_duration(probe_data)
    if duration > settings.MAX_MEDIA_LENGTH_SECONDS:
        raise ValueError("Media exceeds max length configured in settings.")

    title = _extract_title(path, probe_data)
    is_video = suffix in SUPPORTED_VIDEO_EXTENSIONS
    return MediaInfo(path=path, title=title, duration_seconds=duration, is_video=is_video)
