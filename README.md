# OpenNote Bot (MVP)

Local Telegram bot that turns already-downloaded media files into Obsidian notes.

## What it does

- Accepts a **local media path** or **YouTube URL** (URL expects an external downloader to place the file on disk).
- Extracts audio (if video), normalizes it, transcribes with faster-whisper, and optionally summarizes via Ollama.
- Saves outputs directly into a single Obsidian folder, named after the video title (flat list).

## Requirements

- **WSL Ubuntu** (Windows host)
- **FFmpeg** installed in WSL (`ffmpeg` + `ffprobe` on PATH)
- **Python 3.10+**
- **Ollama** running locally (for summaries)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install FFmpeg inside WSL:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

## Configuration

Edit `config/settings.py`:

```python
OBSIDIAN_YT_PATH = "/absolute/path/to/Obsidian/YouTube"
MAX_MEDIA_LENGTH_SECONDS = 7200
ENABLE_SUMMARY = False
OLLAMA_MODEL = "llama3:8b"
WHISPER_MODEL = "large-v3"
WHISPER_COMPUTE_TYPE = "int8"
OUTPUT_DATE_PREFIX = True

TELEGRAM_BOT_TOKEN = "<your-telegram-bot-token>"
EXTERNAL_DOWNLOAD_DIR = "/path/to/your/downloader/output"
YTDLP_COMMAND = "yt-dlp"
```

## Usage

Run the bot:

```bash
python -m bot.telegram_bot
```

In Telegram:

- `/transcript /path/to/video.mp4`
- `/note /path/to/video.mp4`
- `/note https://youtube.com/watch?v=...` (downloads via `yt-dlp` into `EXTERNAL_DOWNLOAD_DIR`)

## Outputs

- `video_title.txt` — full transcript
- `video_title.transcript.json` — segments + timestamps
- `video_title.md` — summary + transcript (when enabled)

## Notes

- Summaries only run when `ENABLE_SUMMARY = True`.
- Outputs are written into a flat Obsidian folder and include a date prefix like `YYYY-MM-DD – Video Title.md`.
- If a filename already exists, a numeric suffix is appended (for example, `Video Title (1).md`).
