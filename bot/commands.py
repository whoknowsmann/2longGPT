"""Telegram bot command handlers."""

from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from pipeline.runner import run_summary, run_transcription
from pipeline.writer import write_outputs

logger = logging.getLogger(__name__)


async def _handle_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    generate_summary: bool,
) -> None:
    if update.message is None:
        return
    if not context.args:
        await update.message.reply_text("Provide a file path or YouTube URL.")
        return

    input_value = " ".join(context.args)
    await update.message.reply_text("Processing media...")

    try:
        await update.message.reply_text("Transcribing...")
        media, transcript = await asyncio.to_thread(run_transcription, input_value)
    except Exception as exc:
        logger.exception("Pipeline failed")
        await update.message.reply_text(f"Failed: {exc}")
        return

    summary_markdown = None
    if generate_summary and settings.ENABLE_SUMMARY:
        await update.message.reply_text("Summarizing...")
        try:
            summary_markdown = await asyncio.to_thread(run_summary, media, transcript)
        except Exception as exc:
            logger.exception("Summarization failed")
            await update.message.reply_text(f"Summarization failed: {exc}")

    outputs = write_outputs(media.title, transcript, summary_markdown)
    transcript_path = outputs.get("transcript_path")
    note_path = outputs.get("note_path")

    message_lines = [f"Saved transcript: {transcript_path}"]
    if note_path:
        message_lines.append(f"Saved note: {note_path}")
    await update.message.reply_text("\n".join(message_lines))


async def transcript_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, generate_summary=False)


async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_command(update, context, generate_summary=True)
