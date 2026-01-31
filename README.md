# OpenNote Bot (MVP)

Local Telegram bot that turns YouTube URLs, local media, and documents into Obsidian-friendly notes.

## What it does

- Accepts a **YouTube URL**, **local audio/video path**, or **local PDF/TXT/MD document**.
- Extracts/transcribes audio with faster-whisper.
- Optionally summarizes via Ollama (map/reduce chunking).
- Saves Markdown and transcript outputs into a single Obsidian folder.

## Requirements

- **WSL Ubuntu** (Windows host)
- **FFmpeg** installed in WSL (`ffmpeg` + `ffprobe` on PATH)
- **Python 3.10+**
- **Ollama** running locally (for summaries)
- **External downloader** for YouTube URLs (writes to `EXTERNAL_DOWNLOAD_DIR`)

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
DATE_PREFIX_FILENAMES = True

TELEGRAM_BOT_TOKEN = "<your-telegram-bot-token>"
EXTERNAL_DOWNLOAD_DIR = "/path/to/your/downloader/output"
```

## Usage

Run the bot:

```bash
python -m bot.telegram_bot
```

In Telegram:

- `/transcript /path/to/video.mp4`
- `/note /path/to/video.mp4`
- `/summary /path/to/video.mp4`
- `/outline /path/to/document.pdf`
- `/study /path/to/document.md`
- `/note https://youtube.com/watch?v=...` (requires external downloader that saves into `EXTERNAL_DOWNLOAD_DIR`)

## Supported Inputs

- **YouTube URL** (downloaded externally into `EXTERNAL_DOWNLOAD_DIR`)
- **Audio**: `wav`, `mp3`, `m4a`, `aac`, `flac`, `ogg`
- **Video**: `mp4`, `mkv`, `webm`, `mov`, `avi`
- **Documents**: `pdf`, `txt`, `md`

## Output Modes

- `note`: summary + key takeaways + collapsible transcript
- `summary`: summary + key takeaways
- `transcript`: transcript only (no LLM)
- `outline`: hierarchical outline
- `study`: headings + key points + definitions

## Outputs

- `YYYY-MM-DD – title.txt` — full transcript
- `YYYY-MM-DD – title.transcript.json` — segments + timestamps
- `YYYY-MM-DD – title.md` — Markdown note (when applicable)

## Notes

- Summaries only run when `ENABLE_SUMMARY = True`.
- If a filename already exists, a numeric suffix is appended.
- Outputs are always flat (no per-item subfolders).
