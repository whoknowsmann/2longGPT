"""Normalize audio to 16kHz mono."""

from __future__ import annotations

import subprocess
from pathlib import Path


def normalize_audio(audio_path: Path) -> Path:
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
