from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

ENV_PREFIX = "CTI__"


def _deep_update(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def _env_overrides(prefix: str = ENV_PREFIX) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].split("__")
        cursor = overrides
        for part in path[:-1]:
            cursor = cursor.setdefault(part.lower(), {})
        cursor[path[-1].lower()] = _coerce_value(value)
    return overrides


def _coerce_value(raw: str) -> Any:
    lower = raw.strip().lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        if "." in lower:
            return float(lower)
        return int(lower)
    except ValueError:
        return raw


def _default_config_path() -> Path:
    # WHY: resolve path relative to repo root to avoid hardcoding and CWD dependence.
    base_dir = Path(__file__).resolve().parents[3]
    return base_dir / "config" / "defaults.yaml"


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    # WHY: environment-first approach keeps secrets and deployment details out of code.
    load_dotenv()

    resolved_path = Path(config_path) if config_path else None
    if not resolved_path:
        env_path = os.getenv("CTI_CONFIG_PATH")
        resolved_path = Path(env_path) if env_path else _default_config_path()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")

    with resolved_path.open("r", encoding="utf-8") as handle:
        config: Dict[str, Any] = yaml.safe_load(handle) or {}

    overrides = _env_overrides()
    if overrides:
        config = _deep_update(config, overrides)

    return config
