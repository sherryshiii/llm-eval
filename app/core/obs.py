"""Small utilities for logging and prompt metadata."""

import json
import os
import time
import hashlib
from typing import Any, Dict


def _sha256(s: str) -> str:
    """Return a short sha256 hash for a string (first 16 hex chars)."""
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def log_request(event: Dict[str, Any]) -> None:
    """Append one JSON line event into `logs/requests.jsonl`."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    log_dir = os.path.join(root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, "requests.jsonl")
    event.setdefault("event_type", "run")
    event.setdefault("ts", int(time.time()))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def build_prompt_meta(sys_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Build small metadata that does not store raw prompts."""
    return {
        "sys_len": len(sys_prompt or ""),
        "user_len": len(user_prompt or ""),
        "sys_sha16": _sha256(sys_prompt or ""),
        "user_sha16": _sha256(user_prompt or ""),
    }

