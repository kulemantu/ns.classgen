"""Channel adapters — render a LessonPack for different delivery channels."""

from __future__ import annotations

from .base import ChannelAdapter
from .pdf import PDFAdapter
from .web import WebAdapter
from .whatsapp import WhatsAppAdapter

__all__ = [
    "ChannelAdapter",
    "PDFAdapter",
    "WebAdapter",
    "WhatsAppAdapter",
    "get_adapter",
]


def get_adapter(channel: str) -> ChannelAdapter:
    """Factory: return the adapter for the given channel name."""
    adapters: dict[str, type[ChannelAdapter]] = {
        "web": WebAdapter,
        "whatsapp": WhatsAppAdapter,
        "pdf": PDFAdapter,
    }
    cls = adapters.get(channel)
    if cls is None:
        raise ValueError(f"Unknown channel: {channel!r}")
    return cls()
