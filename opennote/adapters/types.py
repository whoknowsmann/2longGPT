"""Shared types for adapter results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class IngestResult:
    raw_text: str
    segments: List[Dict[str, float | str]]
    metadata: Dict[str, str | float | None]
