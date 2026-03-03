"""Async runner that executes model requests.

This module runs multiple `EvalRequest` objects concurrently and returns results
in the original order.
"""

import asyncio
from typing import Dict, List, Tuple

from app.core.config import ProviderConfig
from app.core.types import EvalRequest, EvalResponse
from app.providers.openai_provider import openai_chat


class Runner:
    """Run requests against multiple providers with simple concurrency control."""

    def __init__(self, providers: Dict[str, ProviderConfig]):
        """Create a runner with per-provider semaphores."""
        self.providers = providers
        self.semaphores = {}  # type: Dict[str, asyncio.Semaphore]
        for k, v in providers.items():
            self.semaphores[k] = asyncio.Semaphore(max(1, int(v.concurrent)))

    async def run_one(self, req: EvalRequest) -> EvalResponse:
        """Run a single request and return one response."""
        provider_name, model_id = req.model_key.split(":", 1)
        p = self.providers[provider_name]
        async with self.semaphores[provider_name]:
            r = await openai_chat(
                base_url=p.base_url or "https://api.openai.com/v1",
                api_key=p.api_key,
                model=model_id,
                messages=req.messages,
                temperature=req.temperature,
                response_format=req.response_format,
            )
        return EvalResponse(
            model_key=req.model_key,
            provider=provider_name,
            model=model_id,
            elapsed_ms=r.elapsed_ms,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            text=r.text,
            raw=r.raw,
        )

    async def run_many(self, reqs: List[EvalRequest]) -> List[EvalResponse]:
        """Run many requests and return responses in the same order."""
        if not reqs:
            return []
        async def _wrap(state: int, coro):
            return state, await coro

        tasks = []
        for r in reqs:
            tasks.append(_wrap(r.state, self.run_one(r)))

        out = []  # type: List[Tuple[int, EvalResponse]]
        for fut in asyncio.as_completed(tasks):
            out.append(await fut)
        out.sort(key=lambda x: x[0])
        return [r for _, r in out]

