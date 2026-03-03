"""Provider abstraction layer.

The app can talk to different LLM platforms (providers).
We keep a small interface here so `Runner` does not depend on any specific API.
"""

from typing import List

from app.core.config import ProviderConfig
from app.core.types import ChatMessage, EvalResponse


class BaseProvider:
    """Base provider interface.

    Each provider should implement `chat()` and return an `EvalResponse`.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    async def chat(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float,
        response_format: str,
    ) -> EvalResponse:
        """Send a chat request.

        Subclasses must implement this.
        """
        raise NotImplementedError("Provider must implement chat().")

