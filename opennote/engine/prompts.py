"""Prompt templates for summarization modes."""

from __future__ import annotations

PROMPTS = {
    "note": (
        "You are creating study notes from summarized content. Return two sections:\n"
        "Summary: a concise paragraph.\n"
        "Key Takeaways: 3-7 bullet points.\n"
    ),
    "summary": (
        "Provide a concise summary paragraph and 3-7 bullet key takeaways.\n"
        "Return in the format:\nSummary: ...\nKey Takeaways:\n- ...\n"
    ),
    "outline": (
        "Create a hierarchical outline with headings and nested bullets.\n"
        "Use Markdown headings and bullets.\n"
    ),
    "study": (
        "Create study notes with headings for Key Points, Definitions, and Examples (if any).\n"
        "Use Markdown headings and bullet points.\n"
    ),
}


def prompt_for_mode(mode: str) -> str:
    if mode not in PROMPTS:
        raise ValueError(f"Unsupported mode: {mode}")
    return PROMPTS[mode]
