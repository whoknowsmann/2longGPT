"""Write transcript and notes to Obsidian."""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from config import settings
from pipeline.transcribe import TranscriptResult


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]+", "", name)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe or "untitled"


def _next_available_stem(output_dir: Path, base_name: str, extensions: list[str]) -> str:
    stem = base_name
    counter = 1
    while True:
        if all(not (output_dir / f"{stem}{ext}").exists() for ext in extensions):
            return stem
        stem = f"{base_name} ({counter})"
        counter += 1


def write_outputs(
    output_dir: Path,
    base_filename: str,
    transcript: TranscriptResult,
    summary_markdown: Optional[str] = None,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_title = _sanitize_filename(base_filename)
    date_prefix = dt.datetime.now().strftime("%Y-%m-%d")
    if settings.OUTPUT_DATE_PREFIX:
        base_name = f"{date_prefix} – {safe_title}" if safe_title else date_prefix
    else:
        base_name = safe_title or date_prefix

    extensions = [".txt", ".transcript.json", ".md"]
    final_stem = _next_available_stem(output_dir, base_name, extensions)

    transcript_path = output_dir / f"{final_stem}.txt"
    transcript_json_path = output_dir / f"{final_stem}.transcript.json"
    transcript_path.write_text(transcript.text, encoding="utf-8")
    transcript_json_path.write_text(
        json.dumps([asdict(segment) for segment in transcript.segments], indent=2),
        encoding="utf-8",
    )

    note_path = None
    if summary_markdown is not None:
        note_path = output_dir / f"{final_stem}.md"
        note_path.write_text(summary_markdown, encoding="utf-8")

    return {
        "transcript_path": transcript_path,
        "transcript_json_path": transcript_json_path,
        "note_path": note_path,
    }
