"""WhatsApp flow session engine.

Manages multi-turn conversational flows on WhatsApp. Each phone number
has at most one active flow at a time (e.g. lesson browsing, registration).

Uses Redis with a 1-hour TTL for production, in-memory dict for local dev.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from classgen.integrations.redis_queue import get_redis

_FLOW_TTL = 3600  # 1 hour
_FLOW_PREFIX = "wa_flow:"

# In-memory fallback
_mem_flows: dict[str, dict] = {}


@dataclass
class WAFlow:
    type: str  # "lesson_browse", "register", "homework_browse"
    step: str  # current step within the flow
    data: dict = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now


def set_flow(phone: str, flow: WAFlow) -> None:
    """Store an active flow for a phone number (replaces any existing flow)."""
    flow_dict = asdict(flow)
    redis = get_redis()
    if redis:
        redis.set(f"{_FLOW_PREFIX}{phone}", json.dumps(flow_dict), ex=_FLOW_TTL)
    else:
        _mem_flows[phone] = flow_dict


def get_flow(phone: str) -> WAFlow | None:
    """Retrieve the active flow for a phone number, or None if none/expired."""
    redis = get_redis()
    if redis:
        data = redis.get(f"{_FLOW_PREFIX}{phone}")
        if not data:
            return None
        return WAFlow(**json.loads(data))
    flow_dict = _mem_flows.get(phone)
    if not flow_dict:
        return None
    return WAFlow(**flow_dict)


def update_flow(phone: str, *, step: str | None = None, data: dict | None = None) -> None:
    """Partially update an active flow — merges data, updates step and timestamp."""
    flow = get_flow(phone)
    if not flow:
        return
    if step is not None:
        flow.step = step
    if data is not None:
        flow.data.update(data)
    flow.updated_at = datetime.now(timezone.utc).isoformat()
    set_flow(phone, flow)


def clear_flow(phone: str) -> None:
    """Explicitly end a flow."""
    redis = get_redis()
    if redis:
        redis.delete(f"{_FLOW_PREFIX}{phone}")
    else:
        _mem_flows.pop(phone, None)
