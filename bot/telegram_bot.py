"""Entrypoint for the Telegram bot."""

from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder, CommandHandler

from bot.commands import note_command, transcript_command
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in config/settings.py")

    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("transcript", transcript_command))
    application.add_handler(CommandHandler("note", note_command))

    logger.info("Starting OpenNote bot")
    application.run_polling()


if __name__ == "__main__":
    main()
