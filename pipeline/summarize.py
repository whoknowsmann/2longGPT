"""Summarize transcripts with Ollama."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Iterable, List

import requests

from config import settings
from pipeline.transcribe import TranscriptSegment


@dataclass(frozen=True)
class SummaryResult:
    markdown: str


def _chunk_text(text: str, max_chars: int = 4000) -> Iterable[str]:
    start = 0
    while start < len(text):
        yield text[start : start + max_chars]
        start += max_chars


def _ollama_generate(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=180,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()


def _summarize_chunks(chunks: Iterable[str]) -> List[str]:
    summaries = []
    for chunk in chunks:
        prompt = textwrap.dedent(
            f"""
            You are summarizing a transcript chunk from a video. Provide a concise summary
            and 3-5 bullet key takeaways.

            Transcript chunk:
            {chunk}
            """
        ).strip()
        summaries.append(_ollama_generate(prompt))
    return summaries


def _parse_summary_and_takeaways(text: str) -> tuple[str, List[str]]:
    summary = ""
    takeaways: List[str] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current = None
    for line in lines:
        if line.upper().startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
            current = "summary"
            continue
        if line.upper().startswith("TAKEAWAYS"):
            current = "takeaways"
            continue
        if current == "summary" and not summary:
            summary = line
            continue
        if current == "takeaways" and line.startswith("-"):
            takeaways.append(line.lstrip("-").strip())

    if not summary:
        summary = text.strip()
    if not takeaways:
        takeaways = [line.lstrip("-").strip() for line in lines if line.startswith("-")]
    return summary, takeaways


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_timestamped_transcript(segments: Iterable[TranscriptSegment]) -> str:
    lines = []
    for segment in segments:
        start = _format_timestamp(segment.start)
        end = _format_timestamp(segment.end)
        lines.append(f"[{start} - {end}] {segment.text.strip()}")
    return "\n".join(lines).strip()


def summarize_transcript(
    title: str,
    transcript_text: str,
    segments: Iterable[TranscriptSegment],
) -> SummaryResult:
    chunk_summaries = _summarize_chunks(_chunk_text(transcript_text))
    combined_prompt = textwrap.dedent(
        f"""
        Combine the following summaries into a single final summary.
        Respond with the exact format:
        SUMMARY: <one paragraph summary>
        TAKEAWAYS:
        - bullet 1
        - bullet 2
        - bullet 3

        Title: {title}
        Summaries:
        {"\n\n".join(chunk_summaries)}
        """
    ).strip()
    combined = _ollama_generate(combined_prompt)
    summary_text, takeaways = _parse_summary_and_takeaways(combined)
    takeaways_markdown = "\n".join(f"- {item}" for item in takeaways) if takeaways else ""
    transcript_block = _format_timestamped_transcript(segments)

    markdown = textwrap.dedent(
        f"""
        # {title}

        ## Summary

        {summary_text}

        ## Key Takeaways

        {takeaways_markdown}

        ## Transcript

        <details>
        <summary>Show transcript</summary>

        {transcript_block}

        </details>
        """
    ).strip()
    return SummaryResult(markdown=markdown)
