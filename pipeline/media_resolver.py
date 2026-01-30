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


def _download_from_url(url: str, download_dir: str) -> Path:
    if not download_dir:
        raise ValueError(
            "EXTERNAL_DOWNLOAD_DIR is not set. Provide a local path instead of a URL."
        )
    path = Path(download_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)

    existing_files = {p for p in path.iterdir() if p.is_file()}
    start_time = time.time()
    output_template = str(path / "%(title)s.%(ext)s")
    command = [settings.YTDLP_COMMAND, "-o", output_template, url]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed: {completed.stderr.strip() or 'unknown error'}"
        )

    return _poll_for_download(path, existing_files, start_time)


def _poll_for_download(
    download_dir: Path, existing_files: set[Path], start_time: float
) -> Path:
    logger.info("Polling %s for downloaded media", download_dir)
    while time.time() - start_time < settings.MEDIA_POLL_TIMEOUT_SECONDS:
        candidates = [
            p
            for p in download_dir.iterdir()
            if p.is_file()
            and p.suffix.lower() in _supported_extensions()
            and p not in existing_files
            and p.stat().st_mtime >= start_time
        ]
        if candidates:
            candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
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
        path = _download_from_url(input_value, settings.EXTERNAL_DOWNLOAD_DIR)
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
