"""OpenAI-compatible chat client.

This module sends chat completion requests to OpenAI-compatible endpoints.
It supports:
- plain text responses
- a simple "JSON mode" that tries to return a valid JSON object
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.core.config import ProviderConfig
from app.core.types import ChatMessage, EvalResponse
from app.providers.base import BaseProvider


_JSON_INSTRUCTION = (
    "You MUST respond with valid json.\n"
    "Return a single JSON object only (no markdown, no code fences, no extra text).\n"
    'If the user asks for plain text, still wrap it as {"answer": "..."}.\n'
)


def _system_first_single(messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Some OpenAI-compatible servers require:
    - system messages must be first
    - (sometimes) only one system message is allowed

    We merge all system contents into a single first system message.
    """
    systems = [m.content for m in messages if m.role == "system" and (m.content is not None)]
    others = [m for m in messages if m.role != "system"]
    if not systems:
        return others
    merged = "\n\n".join([s for s in systems if str(s).strip() != ""]).strip()
    if not merged:
        return others
    return [ChatMessage(role="system", content=merged), *others]


def _ensure_json_instruction(messages: List[ChatMessage]) -> List[ChatMessage]:
    """Ensure a single first system message includes the JSON instruction."""
    # Keep server constraints: single system at the very beginning.
    normalized = _system_first_single(messages)
    if normalized and normalized[0].role == "system":
        sys0 = (normalized[0].content or "").strip()
        merged = (_JSON_INSTRUCTION + ("\n\n" + sys0 if sys0 else "")).strip()
        return [ChatMessage(role="system", content=merged), *normalized[1:]]
    return [ChatMessage(role="system", content=_JSON_INSTRUCTION), *normalized]


def _coerce_to_json_object_text(text: str) -> str:
    """Return a JSON object string.

    If the input is not valid JSON, we wrap it as {"answer": "..."}.
    """
    s = (text or "").strip()
    if not s:
        return "{}"
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False)
        return json.dumps({"result": obj}, ensure_ascii=False)
    except Exception:
        # Try extracting the first JSON object in the string.
        start = s.find("{")
        end = s.rfind("}")
        if 0 <= start < end:
            cand = s[start : end + 1]
            try:
                obj = json.loads(cand)
                if isinstance(obj, dict):
                    return json.dumps(obj, ensure_ascii=False)
                return json.dumps({"result": obj}, ensure_ascii=False)
            except Exception:
                pass
        return json.dumps({"answer": s}, ensure_ascii=False)


async def openai_chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: List[ChatMessage],
    temperature: float,
    response_format: str,
) -> EvalResponse:
    """Call `/chat/completions` and return a normalized `EvalResponse`."""
    url = base_url.rstrip("/") + "/chat/completions"
    effective_messages = messages
    if response_format == "json":
        effective_messages = _ensure_json_instruction(messages)
    payload = {  # type: Dict[str, Any]
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in effective_messages if m.content is not None],
        "temperature": temperature,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {api_key}"}

    async def _post(json_payload: Dict[str, Any]) -> Tuple[httpx.Response, Any, int]:
        """Send one HTTP request and parse JSON if possible."""
        start = time.time()
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=json_payload)
            elapsed = int((time.time() - start) * 1000)
            try:
                d = resp.json()
            except Exception:
                d = {"raw_text": resp.text}
        return resp, d, elapsed

    r, data, elapsed_ms = await _post(payload)

    # Many OpenAI-compatible providers either don't support `response_format` or implement it differently.
    # If JSON mode was requested and the server rejects the parameter, retry without it but keep prompt instruction.
    if r.status_code >= 400 and response_format == "json":
        msg = ""
        if isinstance(data, dict):
            msg = (data.get("error") or {}).get("message") or data.get("message") or ""
        msg_l = (msg or "").lower()
        if r.status_code in (400, 404, 422) and (
            "response_format" in msg_l or "invalidparameter" in msg_l or "unsupported" in msg_l
        ):
            payload2 = dict(payload)
            payload2.pop("response_format", None)
            r2, data2, elapsed2 = await _post(payload2)
            r, data, elapsed_ms = r2, data2, elapsed2

    if r.status_code >= 400:
        msg = ""
        if isinstance(data, dict):
            msg = (data.get("error") or {}).get("message") or data.get("message") or ""
        return EvalResponse(
            model_key="",
            provider="openai",
            model=model,
            elapsed_ms=elapsed_ms,
            input_tokens=None,
            output_tokens=None,
            text=f"HTTP {r.status_code}: {msg or str(data)}",
            raw=data,
        )

    text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
    if response_format == "json":
        text = _coerce_to_json_object_text(text)
    usage = data.get("usage") or {}
    return EvalResponse(
        model_key="",
        provider="openai",
        model=model,
        elapsed_ms=elapsed_ms,
        input_tokens=usage.get("prompt_tokens"),
        output_tokens=usage.get("completion_tokens"),
        text=text,
        raw=data,
    )


class OpenAICompatProvider(BaseProvider):
    """Provider implementation for OpenAI-compatible chat APIs."""

    def __init__(self, config: ProviderConfig):
        # We keep the raw ProviderConfig so we can read base_url and api_key.
        super().__init__(config)

    async def chat(
        self,
        model: str,
        messages: List[ChatMessage],
        temperature: float,
        response_format: str,
    ) -> EvalResponse:
        """Call an OpenAI-compatible `/chat/completions` endpoint."""
        base_url = self.config.base_url or "https://api.openai.com/v1"
        return await openai_chat(
            base_url=base_url,
            api_key=self.config.api_key,
            model=model,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
        )

