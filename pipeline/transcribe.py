"""Transcription via faster-whisper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from faster_whisper import WhisperModel

from config import settings


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    segments: List[TranscriptSegment]


def transcribe_audio(audio_path: Path) -> TranscriptResult:
    model = WhisperModel(settings.WHISPER_MODEL, compute_type=settings.WHISPER_COMPUTE_TYPE)
    segments_iter, _info = model.transcribe(str(audio_path))

    segments: List[TranscriptSegment] = []
    texts: List[str] = []
    for segment in segments_iter:
        segments.append(
            TranscriptSegment(start=segment.start, end=segment.end, text=segment.text)
        )
        texts.append(segment.text.strip())

    return TranscriptResult(text="\n".join(texts).strip(), segments=segments)
