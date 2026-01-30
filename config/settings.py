"""Application settings for OpenNote Bot."""

from __future__ import annotations

OBSIDIAN_YT_PATH = "/absolute/path/to/Obsidian/YouTube"
MAX_MEDIA_LENGTH_SECONDS = 7200
ENABLE_SUMMARY = False
OLLAMA_MODEL = "llama3:8b"
WHISPER_MODEL = "large-v3"
WHISPER_COMPUTE_TYPE = "int8"
OUTPUT_DATE_PREFIX = True

TELEGRAM_BOT_TOKEN = ""
EXTERNAL_DOWNLOAD_DIR = ""
YTDLP_COMMAND = "yt-dlp"
MEDIA_POLL_SECONDS = 5
MEDIA_POLL_TIMEOUT_SECONDS = 600
