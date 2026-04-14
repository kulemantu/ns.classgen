"""Parse Twilio MessagingResponse TwiML XML into structured messages."""

from __future__ import annotations

import xml.etree.ElementTree as ET


def parse_twiml(xml_text: str) -> list[dict]:
    """Parse TwiML XML and extract Message bodies and Media URLs.

    Returns a list of dicts: [{"body": str, "media": [str, ...]}]
    """
    root = ET.fromstring(xml_text)
    messages: list[dict] = []

    for msg_elem in root.iter("Message"):
        body = ""
        media: list[str] = []

        # Body can be direct text or in a <Body> child
        body_elem = msg_elem.find("Body")
        if body_elem is not None and body_elem.text:
            body = body_elem.text
        elif msg_elem.text and msg_elem.text.strip():
            body = msg_elem.text.strip()

        for media_elem in msg_elem.iter("Media"):
            if media_elem.text:
                media.append(media_elem.text.strip())

        messages.append({"body": body, "media": media})

    return messages


def format_messages(messages: list[dict], *, color: bool = True) -> str:
    """Format parsed TwiML messages for terminal display."""
    GREEN = "\033[0;32m" if color else ""
    CYAN = "\033[0;36m" if color else ""
    RESET = "\033[0m" if color else ""

    parts: list[str] = []
    for i, msg in enumerate(messages):
        if len(messages) > 1:
            parts.append(f"{GREEN}  Message {i + 1}:{RESET}")
        if msg["body"]:
            parts.append(f"  {msg['body']}")
        for url in msg["media"]:
            parts.append(f"  {CYAN}[media]{RESET} {url}")
    return "\n".join(parts)
