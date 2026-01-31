"""Local audio/video ingestion."""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import List

from faster_whisper import WhisperModel

from config import settings
from opennote.adapters.types import IngestResult

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi"}


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


def _extract_duration_seconds(probe_data: dict) -> float:
    duration = probe_data.get("format", {}).get("duration")
    if duration is None:
        raise ValueError("Unable to determine media duration via ffprobe.")
    return float(duration)


def _extract_audio(input_path: Path, work_dir: Path) -> Path:
    output_path = work_dir / f"{input_path.stem}.wav"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"ffmpeg audio extract failed: {completed.stderr.strip() or 'unknown error'}"
        )
    return output_path


def _normalize_audio(audio_path: Path) -> Path:
    output_path = audio_path.with_suffix(".normalized.wav")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"ffmpeg normalize failed: {completed.stderr.strip() or 'unknown error'}"
        )
    return output_path


def _transcribe_audio(audio_path: Path) -> tuple[str, List[dict]]:
    model = WhisperModel(settings.WHISPER_MODEL, compute_type=settings.WHISPER_COMPUTE_TYPE)
    segments_iter, _info = model.transcribe(str(audio_path))

    segments: List[dict] = []
    texts: List[str] = []
    for segment in segments_iter:
        segments.append(
            {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": segment.text.strip(),
            }
        )
        texts.append(segment.text.strip())

    return "\n".join(texts).strip(), segments


def ingest_media_file(path: str) -> IngestResult:
    media_path = Path(path).expanduser().resolve()
    if not media_path.exists():
        raise FileNotFoundError(f"Media not found at {media_path}")

    suffix = media_path.suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported media format: {suffix}")

    probe_data = _probe_media(media_path)
    duration_seconds = _extract_duration_seconds(probe_data)
    if duration_seconds > settings.MAX_MEDIA_LENGTH_SECONDS:
        raise ValueError("Media exceeds max length configured in settings.")

    title = _extract_title(media_path, probe_data)
    source_type = "audio"

    with tempfile.TemporaryDirectory(prefix="opennote_") as work_dir_name:
        work_dir = Path(work_dir_name)
        audio_path = media_path
        if suffix in SUPPORTED_VIDEO_EXTENSIONS:
            audio_path = _extract_audio(media_path, work_dir)
        normalized_audio = _normalize_audio(audio_path)
        raw_text, segments = _transcribe_audio(normalized_audio)

    metadata = {
        "title": title,
        "source_url": None,
        "duration_seconds": duration_seconds,
        "source_type": source_type,
        "date": date.today().isoformat(),
    }
    return IngestResult(raw_text=raw_text, segments=segments, metadata=metadata)
