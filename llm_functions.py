# LLM functions using Google Gemini (free tier) with Pydantic Structured Outputs

import os
import json
import logging
from langsmith import traceable
from google import genai
from google.genai import types

from models import PostAnalysis, ChannelReport
from prompts import PROMPT_CLASSIFY_POST, PROMPT_CHANNEL_REPORT

_GEMINI_MODEL = "gemini-2.0-flash"
_client = None  # lazy init — created on first LLM call


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client


def _call_llm(prompt: str) -> dict:
    """Raw Gemini call — returns parsed JSON dict."""
    client = _get_client()
    response = client.models.generate_content(
        model=_GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


# ============================================================================
# LLM Call #1 — Classify a single post
# ============================================================================

@traceable(name="classify_post")
def classify_post(post_text: str) -> PostAnalysis:
    """LLM Call #1: Classify a single Telegram post."""
    prompt = PROMPT_CLASSIFY_POST.format(post_text=post_text[:1500])
    raw = _call_llm(prompt)
    result = PostAnalysis(**raw)
    logging.debug(f"[classify_post] topic={result.topic} sentiment={result.sentiment}")
    return result


# ============================================================================
# LLM Call #2 — Generate channel-level report
# ============================================================================

@traceable(name="generate_channel_report")
def generate_channel_report(channel_name: str, analyses: list) -> ChannelReport:
    """LLM Call #2: Aggregate post analyses into a channel intelligence report."""
    from collections import Counter

    topics     = [a["topic"]     for a in analyses]
    sentiments = [a["sentiment"] for a in analyses]
    emotions   = [a["emotion"]   for a in analyses]
    breaking   = sum(1 for a in analyses if a["is_breaking"] == "Yes")
    all_keywords = []
    for a in analyses:
        all_keywords.extend([k.strip() for k in a["keywords"].split(",")])

    def fmt_dist(counter: Counter) -> str:
        total = sum(counter.values())
        return ", ".join(f"{k}: {v} ({v*100//total}%)" for k, v in counter.most_common())

    prompt = PROMPT_CHANNEL_REPORT.format(
        channel_name=channel_name,
        post_count=len(analyses),
        topic_distribution=fmt_dist(Counter(topics)),
        sentiment_distribution=fmt_dist(Counter(sentiments)),
        emotion_distribution=fmt_dist(Counter(emotions)),
        breaking_count=breaking,
        top_keywords=", ".join(k for k, _ in Counter(all_keywords).most_common(10)),
    )

    raw = _call_llm(prompt)
    result = ChannelReport(**raw)
    logging.info(f"[generate_channel_report] {channel_name}: mood={result.overall_mood} score={result.mood_score}")
    return result
