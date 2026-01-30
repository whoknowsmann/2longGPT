"""Summarize transcripts with Ollama."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from typing import Iterable, List

import requests

from config import settings


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


def summarize_transcript(title: str, transcript_text: str) -> SummaryResult:
    chunk_summaries = _summarize_chunks(_chunk_text(transcript_text))
    combined_prompt = textwrap.dedent(
        f"""
        Combine the following summaries into a single final note.
        Provide:
        - Title
        - Summary paragraph
        - Key Takeaways (bullets)
        - Timestamped transcript placeholder section

        Title: {title}
        Summaries:
        {"\n\n".join(chunk_summaries)}
        """
    ).strip()
    combined = _ollama_generate(combined_prompt)
    markdown = textwrap.dedent(
        f"""
        # {title}

        {combined}

        ## Transcript

        {transcript_text}
        """
    ).strip()
    return SummaryResult(markdown=markdown)
