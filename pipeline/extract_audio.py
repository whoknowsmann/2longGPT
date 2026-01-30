"""Audio extraction for video files."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pipeline.media_resolver import MediaInfo


def extract_audio(media: MediaInfo, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    if not media.is_video:
        return media.path

    output_path = work_dir / f"{media.path.stem}.wav"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(media.path),
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
