"""End-to-end processing pipeline."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from config import settings
from pipeline.extract_audio import extract_audio
from pipeline.media_resolver import MediaInfo, resolve_media
from pipeline.normalize_audio import normalize_audio
from pipeline.summarize import summarize_transcript
from pipeline.transcribe import TranscriptResult, transcribe_audio
from pipeline.writer import write_outputs

logger = logging.getLogger(__name__)


class PipelineResult:
    def __init__(
        self,
        media: MediaInfo,
        transcript: TranscriptResult,
        outputs: dict,
        summary_markdown: Optional[str],
    ) -> None:
        self.media = media
        self.transcript = transcript
        self.outputs = outputs
        self.summary_markdown = summary_markdown


def run_transcription(input_value: str) -> tuple[MediaInfo, TranscriptResult]:
    media = resolve_media(input_value)
    work_dir = Path("/tmp/opennote")
    audio_path = extract_audio(media, work_dir)
    normalized_audio = normalize_audio(audio_path)
    transcript = transcribe_audio(normalized_audio)
    return media, transcript


def run_summary(media: MediaInfo, transcript: TranscriptResult) -> Optional[str]:
    if not settings.ENABLE_SUMMARY:
        return None
    return summarize_transcript(media.title, transcript.text).markdown


def run_pipeline(input_value: str, generate_summary: bool) -> PipelineResult:
    media, transcript = run_transcription(input_value)
    summary_markdown = run_summary(media, transcript) if generate_summary else None
    outputs = write_outputs(media.title, transcript, summary_markdown)
    return PipelineResult(media, transcript, outputs, summary_markdown)
