"""Summarize raw text with Ollama using map/reduce."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

from config import settings
from opennote.engine.prompts import prompt_for_mode


@dataclass(frozen=True)
class SummaryContent:
    summary: Optional[str]
    key_takeaways: Optional[List[str]]
    body: Optional[str]


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
            Summarize the following transcript chunk in 3-5 sentences and include 3 bullet takeaways.

            Transcript chunk:
            {chunk}
            """
        ).strip()
        summaries.append(_ollama_generate(prompt))
    return summaries


def _parse_summary(response: str) -> SummaryContent:
    summary_match = re.search(r"summary:\s*(.+?)(?:\n\s*key takeaways:|$)", response, re.I | re.S)
    takeaways_match = re.search(r"key takeaways:\s*(.+)$", response, re.I | re.S)

    summary_text = summary_match.group(1).strip() if summary_match else response.strip()
    takeaways_text = takeaways_match.group(1).strip() if takeaways_match else ""

    takeaways = []
    for line in takeaways_text.splitlines():
        cleaned = line.strip().lstrip("-*").strip()
        if cleaned:
            takeaways.append(cleaned)

    if not takeaways:
        return SummaryContent(summary=summary_text, key_takeaways=None, body=None)
    return SummaryContent(summary=summary_text, key_takeaways=takeaways, body=None)


def summarize_text(raw_text: str, title: str, mode: str) -> SummaryContent:
    chunks = list(_chunk_text(raw_text))
    chunk_summaries = _summarize_chunks(chunks)
    combined_prompt = textwrap.dedent(
        f"""
        You are combining summaries of a single source titled "{title}".

        {prompt_for_mode(mode)}

        Summaries:
        {"\n\n".join(chunk_summaries)}
        """
    ).strip()
    combined = _ollama_generate(combined_prompt)

    if mode in {"note", "summary"}:
        return _parse_summary(combined)

    return SummaryContent(summary=None, key_takeaways=None, body=combined.strip())
