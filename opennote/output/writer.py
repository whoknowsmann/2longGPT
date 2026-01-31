"""Write outputs to the Obsidian vault."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

from config import settings


@dataclass(frozen=True)
class OutputPaths:
    transcript_path: Path
    transcript_json_path: Optional[Path]
    markdown_path: Optional[Path]


def _sanitize_filename(name: str) -> str:
    safe = re.sub(r"[\\/:*?\"<>|]+", "-", name)
    safe = re.sub(r"\s+", " ", safe).strip()
    return safe or "untitled"


def _next_available_path(base: Path) -> Path:
    if not base.exists():
        return base
    counter = 1
    while True:
        candidate = base.with_name(f"{base.stem} ({counter}){base.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _build_base_filename(title: str) -> str:
    safe_title = _sanitize_filename(title)
    if settings.DATE_PREFIX_FILENAMES:
        prefix = date.today().isoformat()
        return f"{prefix} – {safe_title}"
    return safe_title


def write_outputs(
    title: str,
    transcript_text: str,
    segments: Iterable[dict],
    markdown_text: Optional[str],
    mode: str,
) -> OutputPaths:
    obsidian_path = Path(settings.OBSIDIAN_YT_PATH).expanduser().resolve()
    obsidian_path.mkdir(parents=True, exist_ok=True)

    base_name = _build_base_filename(title)
    transcript_path = _next_available_path(obsidian_path / f"{base_name}.txt")
    transcript_json_path = transcript_path.with_suffix(".transcript.json")

    transcript_path.write_text(transcript_text, encoding="utf-8")
    transcript_json_path.write_text(
        json.dumps(list(segments), indent=2),
        encoding="utf-8",
    )

    markdown_path = None
    if markdown_text and mode != "transcript":
        markdown_path = _next_available_path(obsidian_path / f"{base_name}.md")
        markdown_path.write_text(markdown_text, encoding="utf-8")

    return OutputPaths(
        transcript_path=transcript_path,
        transcript_json_path=transcript_json_path,
        markdown_path=markdown_path,
    )
