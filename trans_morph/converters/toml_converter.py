"""TOML conversion to/from JSON and YAML."""

from __future__ import annotations

import json
import sys
from typing import Any

import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None


def _ensure_tomllib():
    if tomllib is None:
        raise ImportError("tomli is required for TOML input on Python <3.11: pip install tomli")


def _ensure_tomli_w():
    if tomli_w is None:
        raise ImportError("tomli-w is required for TOML output: pip install tomli-w")


def _sanitize_for_toml(data: Any) -> Any:
    """Remove None values and ensure TOML compatibility."""
    if isinstance(data, dict):
        return {k: _sanitize_for_toml(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_sanitize_for_toml(item) for item in data if item is not None]
    return data


def toml_to_json(content: str, indent: int = 2) -> str:
    """Convert TOML to JSON string."""
    _ensure_tomllib()
    data = tomllib.loads(content)
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)


def toml_to_yaml(content: str) -> str:
    """Convert TOML to YAML string."""
    _ensure_tomllib()
    data = tomllib.loads(content)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def json_to_toml(content: str) -> str:
    """Convert JSON to TOML string."""
    _ensure_tomli_w()
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("TOML requires a top-level table/mapping")
    return tomli_w.dumps(_sanitize_for_toml(data))


def yaml_to_toml(content: str) -> str:
    """Convert YAML to TOML string."""
    _ensure_tomli_w()
    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("TOML requires a top-level table/mapping")
    return tomli_w.dumps(_sanitize_for_toml(data))


def parse_toml(content: str) -> dict:
    """Parse TOML content and return dict."""
    _ensure_tomllib()
    return tomllib.loads(content)


def dump_toml(data: dict) -> str:
    """Serialize a dict to TOML string."""
    _ensure_tomli_w()
    return tomli_w.dumps(_sanitize_for_toml(data))
