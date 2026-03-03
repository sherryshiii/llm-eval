"""Configuration loading for the app.

This module loads provider settings from:
- `.env` (optional)
- `configs/providers.yaml` (recommended)
- `configs/providers.example.yaml` (fallback)

It also expands values like `${ENV_NAME}` inside YAML.
"""

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import yaml


_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _project_root() -> str:
    """Return the absolute path of the project root folder."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_dotenv() -> None:
    """Load key/value pairs from `.env` into environment variables.

    Notes:
    - This is a very small `.env` loader.
    - Existing environment variables are not overwritten.
    """
    root = _project_root()
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)


def _expand_env(v: Any) -> Any:
    """Replace `${ENV_NAME}` strings inside a nested object."""
    if isinstance(v, str):
        def repl(m) -> str:
            return os.getenv(m.group(1), "")
        return _ENV_RE.sub(repl, v)
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            out[k] = _expand_env(x)
        return out
    if isinstance(v, list):
        out_list = []
        for x in v:
            out_list.append(_expand_env(x))
        return out_list
    return v


@dataclass(frozen=True)
class ProviderModel:
    """A model entry under a provider."""

    provider: str
    id: str
    label: str


@dataclass(frozen=True)
class ProviderConfig:
    """Provider settings for one platform (OpenAI-compatible)."""

    name: str
    type: str
    api_key: str
    base_url: Optional[str]
    concurrent: int
    models: List[ProviderModel]


class Settings:
    """Parsed settings loaded from YAML."""

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw
        self.providers = {}  # type: Dict[str, ProviderConfig]
        platforms = raw.get("platforms") or raw.get("providers") or {}
        for name, p in platforms.items():
            models = []  # type: List[ProviderModel]
            for m in (p.get("models") or []):
                mid = m.get("model")
                if not mid:
                    continue
                label = m.get("showname") or mid
                models.append(ProviderModel(provider=name, id=mid, label=label))
            self.providers[name] = ProviderConfig(
                name=name,
                type=p.get("type", "openai_compat"),
                api_key=p.get("api_key", ""),
                base_url=p.get("url") or p.get("base_url"),
                concurrent=int(p.get("concurrent", 4)),
                models=models,
            )

    def list_models(self) -> List[Dict[str, Any]]:
        """Return a flat list of models for UI choices."""
        out = []
        for p in self.providers.values():
            for m in p.models:
                out.append(
                    {
                        "key": "%s:%s" % (p.name, m.id),
                        "provider": p.name,
                        "id": m.id,
                        "label": m.label,
                        "type": p.type,
                    }
                )
        return out

    def resolve_model(self, key: str) -> Tuple[ProviderConfig, ProviderModel]:
        """Return provider config and model info for a model key."""
        provider, mid = key.split(":", 1)
        p = self.providers[provider]
        m = next((x for x in p.models if x.id == mid), None)
        if not m:
            raise KeyError(key)
        return p, m


_CACHED = None  # type: Optional[Settings]


def get_settings() -> Settings:
    """Load settings once and return the cached object."""
    global _CACHED
    if _CACHED:
        return _CACHED
    _load_dotenv()
    root = _project_root()
    path = os.getenv("PROVIDERS_CONFIG", "configs/providers.yaml")
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    if not os.path.exists(path):
        path = os.path.join(root, "configs", "providers.example.yaml")
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    _CACHED = Settings(_expand_env(raw) or {})
    return _CACHED

