"""Format markdown outputs."""

from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from opennote.adapters.types import IngestResult
from opennote.engine.summarize import SummaryContent


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_duration(duration_seconds: Optional[float]) -> Optional[str]:
    if duration_seconds is None:
        return None
    return _format_timestamp(duration_seconds)


def _format_segments(segments: Iterable[dict]) -> str:
    lines = []
    for segment in segments:
        start = segment.get("start")
        text = segment.get("text")
        if start is None or text is None:
            continue
        lines.append(f"[{_format_timestamp(float(start))}] {text}")
    return "\n".join(lines).strip()


def _frontmatter(metadata: dict, mode: str) -> str:
    title = metadata.get("title", "Untitled")
    source = metadata.get("source_type", "unknown")
    source_url = metadata.get("source_url") or ""
    duration = _format_duration(metadata.get("duration_seconds"))
    date_value = metadata.get("date") or date.today().isoformat()

    lines = [
        "---",
        f"title: {title}",
        f"source: {source}",
        f"source_url: {source_url}",
        f"date: {date_value}",
        f"duration: {duration or ''}",
        f"mode: {mode}",
        "---",
    ]
    return "\n".join(lines)


def _format_takeaways(takeaways: Optional[List[str]]) -> str:
    if not takeaways:
        return "Summary unavailable."
    return "\n".join(f"- {takeaway}" for takeaway in takeaways)


def build_transcript_text(ingest_result: IngestResult) -> str:
    transcript_text = _format_segments(ingest_result.segments)
    if not transcript_text:
        transcript_text = ingest_result.raw_text
    return transcript_text


def build_markdown(
    ingest_result: IngestResult,
    mode: str,
    summary: Optional[SummaryContent] = None,
) -> str:
    title = ingest_result.metadata.get("title", "Untitled")
    transcript_text = build_transcript_text(ingest_result)

    frontmatter = _frontmatter(ingest_result.metadata, mode)

    if mode == "transcript":
        return f"{frontmatter}\n\n# {title}\n\n{transcript_text}\n"

    if mode in {"note", "summary"}:
        summary_text = summary.summary if summary and summary.summary else "Summary unavailable."
        takeaways_text = _format_takeaways(summary.key_takeaways if summary else None)
        content_lines = [
            frontmatter,
            "",
            f"# {title}",
            "",
            "## Summary",
            summary_text,
            "",
            "## Key Takeaways",
            takeaways_text,
        ]
        if mode == "note":
            content_lines.extend(
                [
                    "",
                    "## Transcript",
                    "<details>",
                    "<summary>Show transcript</summary>",
                    "",
                    transcript_text,
                    "",
                    "</details>",
                ]
            )
        return "\n".join(content_lines).strip() + "\n"

    body = summary.body if summary and summary.body else "Summarization disabled."
    return "\n".join([frontmatter, "", f"# {title}", "", body]).strip() + "\n"
