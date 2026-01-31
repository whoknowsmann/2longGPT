"""Entrypoint for the Telegram bot."""

from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from config import settings
from opennote.bot.commands import (
    note_command,
    outline_command,
    study_command,
    summary_command,
    transcript_command,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in config/settings.py")

    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("transcript", transcript_command))
    application.add_handler(CommandHandler("note", note_command))
    application.add_handler(CommandHandler("summary", summary_command))
    application.add_handler(CommandHandler("outline", outline_command))
    application.add_handler(CommandHandler("study", study_command))

    logger.info("Starting OpenNote bot")
    application.run_polling()


if __name__ == "__main__":
    main()
