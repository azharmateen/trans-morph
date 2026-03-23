"""Validate converted output against JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml


class ValidationError:
    """A single validation error with path information."""

    def __init__(self, message: str, path: str, schema_path: str = ""):
        self.message = message
        self.path = path
        self.schema_path = schema_path

    def __str__(self) -> str:
        loc = self.path if self.path else "(root)"
        return f"[{loc}] {self.message}"

    def __repr__(self) -> str:
        return f"ValidationError({self.path!r}, {self.message!r})"


class ValidationResult:
    """Result of a validation check."""

    def __init__(self, errors: list[ValidationError] | None = None):
        self.errors = errors or []

    @property
    def valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def summary(self) -> str:
        if self.valid:
            return "Validation passed: no errors found."
        lines = [f"Validation failed: {self.error_count} error(s) found."]
        for err in self.errors:
            lines.append(f"  - {err}")
        return "\n".join(lines)


def load_schema(schema_path: str) -> dict:
    """Load a JSON Schema from a file (JSON or YAML)."""
    p = Path(schema_path)
    content = p.read_text(encoding="utf-8")
    if p.suffix in (".yaml", ".yml"):
        return yaml.safe_load(content)
    return json.loads(content)


def validate_data(data: Any, schema: dict) -> ValidationResult:
    """Validate data against a JSON Schema.

    Args:
        data: The data to validate (dict, list, or primitive).
        schema: The JSON Schema to validate against.

    Returns:
        ValidationResult with any errors found.
    """
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema)

    errors: list[ValidationError] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in error.absolute_path)
        schema_path = ".".join(str(p) for p in error.schema_path)
        errors.append(ValidationError(
            message=error.message,
            path=path,
            schema_path=schema_path,
        ))

    return ValidationResult(errors)


def validate_file(data_path: str, schema_path: str) -> ValidationResult:
    """Validate a data file against a JSON Schema file.

    Auto-detects data format from extension.

    Args:
        data_path: Path to data file (JSON or YAML).
        schema_path: Path to JSON Schema file.

    Returns:
        ValidationResult.
    """
    schema = load_schema(schema_path)

    p = Path(data_path)
    content = p.read_text(encoding="utf-8")

    if p.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(content)
    elif p.suffix == ".json":
        data = json.loads(content)
    else:
        # Try JSON first, then YAML
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = yaml.safe_load(content)

    return validate_data(data, schema)
