"""Telegram bot command handlers."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from opennote.adapters import audio as audio_adapter
from opennote.adapters import document as document_adapter
from opennote.adapters import youtube as youtube_adapter
from opennote.engine.format import build_markdown, build_transcript_text
from opennote.engine.summarize import SummaryContent, summarize_text
from opennote.output.writer import write_outputs

logger = logging.getLogger(__name__)


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _detect_adapter(input_value: str) -> Callable[[str], object]:
    if _is_url(input_value):
        return youtube_adapter.ingest_youtube

    path = Path(input_value).expanduser()
    suffix = path.suffix.lower()
    if suffix in document_adapter.SUPPORTED_DOCUMENT_EXTENSIONS:
        return document_adapter.ingest_document
    if suffix in audio_adapter.SUPPORTED_AUDIO_EXTENSIONS | audio_adapter.SUPPORTED_VIDEO_EXTENSIONS:
        return audio_adapter.ingest_media_file

    raise ValueError(f"Unsupported input type: {suffix or 'unknown'}")


async def _handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str) -> None:
    if update.message is None:
        return
    if not context.args:
        await update.message.reply_text("Provide a file path or YouTube URL.")
        return

    input_value = " ".join(context.args)

    try:
        adapter = _detect_adapter(input_value)
    except ValueError as exc:
        await update.message.reply_text(str(exc))
        return

    try:
        if adapter is youtube_adapter.ingest_youtube:
            await update.message.reply_text("Downloading/locating YouTube media...")
        elif adapter is document_adapter.ingest_document:
            await update.message.reply_text("Extracting document text...")
        else:
            await update.message.reply_text("Transcribing media...")

        ingest_result = await asyncio.to_thread(adapter, input_value)
    except Exception as exc:
        logger.exception("Ingestion failed")
        await update.message.reply_text(f"Failed to ingest input: {exc}")
        return

    summary_content: Optional[SummaryContent] = None
    if mode != "transcript" and settings.ENABLE_SUMMARY:
        await update.message.reply_text("Summarizing...")
        try:
            summary_content = await asyncio.to_thread(
                summarize_text,
                ingest_result.raw_text,
                ingest_result.metadata.get("title", "Untitled"),
                mode,
            )
        except Exception as exc:
            logger.exception("Summarization failed")
            await update.message.reply_text(f"Summarization failed: {exc}")

    markdown = build_markdown(ingest_result, mode, summary_content)
    transcript_text = build_transcript_text(ingest_result)

    await update.message.reply_text("Writing output files...")
    outputs = await asyncio.to_thread(
        write_outputs,
        ingest_result.metadata.get("title", "Untitled"),
        transcript_text,
        ingest_result.segments,
        markdown,
        mode,
    )

    lines = [f"Saved transcript: {outputs.transcript_path}"]
    if outputs.markdown_path:
        lines.append(f"Saved note: {outputs.markdown_path}")
    await update.message.reply_text("\n".join(lines))


async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, "note")


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, "summary")


async def transcript_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, "transcript")


async def outline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, "outline")


async def study_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, "study")
