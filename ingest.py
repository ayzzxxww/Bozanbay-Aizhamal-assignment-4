
import os
import re
import json
import logging
from pathlib import Path


def _parse_telegram_html(path: str) -> list[str]:
    """Parse Telegram Desktop HTML export (result.html)."""
    try:
        from bs4 import BeautifulSoup
        with open(path, encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
        posts = []
        for div in soup.select("div.text"):
            text = div.get_text(" ", strip=True)
            if len(text) > 20:
                posts.append(text)
        return posts
    except ImportError:
        logging.warning("beautifulsoup4 not installed — falling back to regex parser")
        return _parse_telegram_html_regex(path)


def _parse_telegram_html_regex(path: str) -> list[str]:
    """Fallback HTML parser using regex (no bs4 needed)."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # Extract text between <div class="text"> tags
    matches = re.findall(r'<div class="text[^"]*">(.*?)</div>', content, re.DOTALL)
    posts = []
    for m in matches:
        text = re.sub(r"<[^>]+>", " ", m).strip()
        if len(text) > 20:
            posts.append(text)
    return posts


def _parse_telegram_json(path: str) -> list[str]:
    """Parse Telegram Desktop JSON export (result.json)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    posts = []
    for msg in data.get("messages", []):
        if msg.get("type") != "message":
            continue
        text = msg.get("text", "")
        if isinstance(text, list):
            # text can be a list of text entities
            text = " ".join(
                t["text"] if isinstance(t, dict) else t for t in text
            )
        text = text.strip()
        if len(text) > 20:
            posts.append(text)
    return posts


def _parse_plain_text(path: str) -> dict[str, list[str]]:
    """
    Parse a plain text file.
    Channels are separated by headers like:  === @channelname ===
    If no headers found, entire file is treated as one channel named 'channel'.
    """
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    channels: dict[str, list[str]] = {}
    current_channel = "channel"
    buffer: list[str] = []

    for line in lines:
        header = re.match(r"^===\s*(@?\S+)\s*===", line.strip())
        if header:
            if buffer:
                text = " ".join(buffer).strip()
                if len(text) > 20:
                    channels.setdefault(current_channel, []).append(text)
                buffer = []
            current_channel = header.group(1).lstrip("@")
        elif line.strip() == "---":
            # Post separator
            text = " ".join(buffer).strip()
            if len(text) > 20:
                channels.setdefault(current_channel, []).append(text)
            buffer = []
        else:
            buffer.append(line.strip())

    # Flush last buffer
    if buffer:
        text = " ".join(buffer).strip()
        if len(text) > 20:
            channels.setdefault(current_channel, []).append(text)

    return channels


def load_posts(channels_file: str, max_posts_per_channel: int = 30) -> dict[str, list[str]]:
    """
    Main entry point for Node 1.
    
    Accepts:
      - A directory containing result.html or result.json  (Telegram Desktop export)
      - A single .html file
      - A single .json file
      - A plain .txt file with === @channel === separators

    Returns:
        {channel_name: [post_text, ...]}
    """
    path = Path(channels_file)

    if not path.exists():
        raise FileNotFoundError(f"Input not found: {channels_file}")

    result: dict[str, list[str]] = {}

    # ── Directory (Telegram Desktop export folder) ──────────────────────────
    if path.is_dir():
        channel_name = path.name
        json_file = path / "result.json"
        html_file = path / "result.html"

        if json_file.exists():
            logging.info(f"[ingest] Parsing JSON export: {json_file}")
            posts = _parse_telegram_json(str(json_file))
        elif html_file.exists():
            logging.info(f"[ingest] Parsing HTML export: {html_file}")
            posts = _parse_telegram_html(str(html_file))
        else:
            # Try to load every .json inside
            posts = []
            for f in sorted(path.glob("*.json")):
                posts.extend(_parse_telegram_json(str(f)))

        result[channel_name] = posts[:max_posts_per_channel]

    # ── Single JSON file ─────────────────────────────────────────────────────
    elif path.suffix == ".json":
        channel_name = path.stem
        logging.info(f"[ingest] Parsing JSON: {path}")
        posts = _parse_telegram_json(str(path))
        result[channel_name] = posts[:max_posts_per_channel]

    # ── Single HTML file ─────────────────────────────────────────────────────
    elif path.suffix == ".html":
        channel_name = path.stem
        logging.info(f"[ingest] Parsing HTML: {path}")
        posts = _parse_telegram_html(str(path))
        result[channel_name] = posts[:max_posts_per_channel]

    # ── Plain text file ──────────────────────────────────────────────────────
    elif path.suffix == ".txt":
        logging.info(f"[ingest] Parsing plain text: {path}")
        channels = _parse_plain_text(str(path))
        for ch, posts in channels.items():
            result[ch] = posts[:max_posts_per_channel]

    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    total = sum(len(v) for v in result.values())
    logging.info(f"[ingest] Loaded {total} posts from {len(result)} channel(s)")
    return result
