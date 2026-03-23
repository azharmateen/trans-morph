"""YAML and JSON conversion with multi-document YAML support."""

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


def json_to_yaml(content: str) -> str:
    """Convert JSON to YAML string."""
    data = json.loads(content)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def yaml_to_json(content: str, indent: int = 2) -> str:
    """Convert YAML to JSON string.

    Handles multi-document YAML by returning a JSON array.
    """
    docs = list(yaml.safe_load_all(content))
    if len(docs) == 1:
        return json.dumps(docs[0], indent=indent, default=str, ensure_ascii=False)
    return json.dumps(docs, indent=indent, default=str, ensure_ascii=False)


def yaml_to_toml(content: str) -> str:
    """Convert YAML to TOML string."""
    if tomli_w is None:
        raise ImportError("tomli-w is required for TOML output: pip install tomli-w")

    data = yaml.safe_load(content)
    if not isinstance(data, dict):
        raise ValueError("TOML requires a top-level mapping/table. Got: " + type(data).__name__)
    return tomli_w.dumps(_sanitize_for_toml(data))


def toml_to_yaml(content: str) -> str:
    """Convert TOML to YAML string."""
    if tomllib is None:
        raise ImportError("tomli is required for TOML input on Python <3.11: pip install tomli")

    data = tomllib.loads(content)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def json_to_toml(content: str) -> str:
    """Convert JSON to TOML string."""
    if tomli_w is None:
        raise ImportError("tomli-w is required for TOML output: pip install tomli-w")

    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("TOML requires a top-level mapping/table. Got: " + type(data).__name__)
    return tomli_w.dumps(_sanitize_for_toml(data))


def toml_to_json(content: str, indent: int = 2) -> str:
    """Convert TOML to JSON string."""
    if tomllib is None:
        raise ImportError("tomli is required for TOML input on Python <3.11: pip install tomli")

    data = tomllib.loads(content)
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)


def _sanitize_for_toml(data: Any) -> Any:
    """Sanitize data for TOML serialization (TOML doesn't support None)."""
    if isinstance(data, dict):
        return {k: _sanitize_for_toml(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_sanitize_for_toml(item) for item in data if item is not None]
    return data
