"""Provider implementations (OpenAI-compatible).

`BaseProvider` is the small interface used by `Runner`.
"""

from app.providers.base import BaseProvider
from app.providers.openai_provider import OpenAICompatProvider

__all__ = ["BaseProvider", "OpenAICompatProvider"]


