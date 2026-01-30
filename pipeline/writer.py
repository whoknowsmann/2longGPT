"""Write transcript and notes to Obsidian."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from config import settings
from pipeline.transcribe import TranscriptResult


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return safe or "untitled"


def _next_available_path(base: Path) -> Path:
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = base.with_name(f"{base.stem}_{counter}{base.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def write_outputs(
    title: str,
    transcript: TranscriptResult,
    summary_markdown: Optional[str] = None,
) -> dict:
    obsidian_path = Path(settings.OBSIDIAN_YT_PATH).expanduser().resolve()
    obsidian_path.mkdir(parents=True, exist_ok=True)

    safe_title = _sanitize_filename(title)
    transcript_path = _next_available_path(obsidian_path / f"{safe_title}.txt")
    transcript_json_path = transcript_path.with_suffix(".transcript.json")

    transcript_path.write_text(transcript.text, encoding="utf-8")
    transcript_json_path.write_text(
        json.dumps([asdict(segment) for segment in transcript.segments], indent=2),
        encoding="utf-8",
    )

    note_path = None
    if summary_markdown is not None:
        note_path = _next_available_path(obsidian_path / f"{safe_title}.md")
        note_path.write_text(summary_markdown, encoding="utf-8")

    return {
        "transcript_path": transcript_path,
        "transcript_json_path": transcript_json_path,
        "note_path": note_path,
    }
