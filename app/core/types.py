"""Data structures used by the app.

This file defines simple request/response objects used across the project.
"""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class ChatMessage:
    """A single chat message."""

    role: str
    content: str


@dataclass(frozen=True)
class EvalRequest:
    """A request to run one model on one prompt."""

    model_key: str
    messages: List[ChatMessage]
    response_format: str = "text"
    temperature: float = 0.0
    state: int = 0


@dataclass(frozen=True)
class EvalResponse:
    """A response returned by a model run."""

    model_key: str
    provider: str
    model: str
    elapsed_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    text: str
    raw: Optional[Any] = None

