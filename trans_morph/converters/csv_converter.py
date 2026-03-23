"""CSV conversion with type inference and header detection."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

import yaml


def _infer_type(value: str) -> Any:
    """Infer the Python type from a string value."""
    if not value or value.strip() == "":
        return None

    v = value.strip()

    # Boolean
    if v.lower() in ("true", "yes", "1"):
        return True
    if v.lower() in ("false", "no", "0"):
        return False

    # Integer
    try:
        if "." not in v and "e" not in v.lower():
            return int(v)
    except ValueError:
        pass

    # Float
    try:
        return float(v)
    except ValueError:
        pass

    # Date patterns (ISO format)
    if re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?", v):
        return v  # Keep as string but recognized

    # JSON embedded (arrays, objects)
    if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            pass

    return v


def _detect_delimiter(content: str) -> str:
    """Detect the CSV delimiter (comma, tab, semicolon, pipe)."""
    first_lines = content.split("\n", 5)[:3]
    delimiters = {",": 0, "\t": 0, ";": 0, "|": 0}

    for line in first_lines:
        for d in delimiters:
            delimiters[d] += line.count(d)

    best = max(delimiters, key=delimiters.get)
    return best if delimiters[best] > 0 else ","


def csv_to_records(content: str) -> list[dict[str, Any]]:
    """Parse CSV content into a list of dictionaries with type inference.

    Auto-detects delimiter and infers types for each value.
    """
    delimiter = _detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    records = []
    for row in reader:
        record = {}
        for key, value in row.items():
            if key is None:
                continue
            key = key.strip()
            record[key] = _infer_type(value) if value is not None else None
        records.append(record)
    return records


def records_to_csv(records: list[dict[str, Any]], delimiter: str = ",") -> str:
    """Convert a list of dictionaries to CSV string."""
    if not records:
        return ""

    # Gather all keys in order
    all_keys: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    for record in records:
        row = {}
        for k in all_keys:
            v = record.get(k)
            if isinstance(v, (list, dict)):
                row[k] = json.dumps(v, default=str)
            elif v is None:
                row[k] = ""
            else:
                row[k] = str(v)
        writer.writerow(row)
    return output.getvalue()


def csv_to_json(content: str) -> str:
    """Convert CSV to JSON string."""
    records = csv_to_records(content)
    return json.dumps(records, indent=2, default=str, ensure_ascii=False)


def csv_to_yaml(content: str) -> str:
    """Convert CSV to YAML string."""
    records = csv_to_records(content)
    return yaml.dump(records, default_flow_style=False, allow_unicode=True, sort_keys=False)


def json_to_csv(content: str) -> str:
    """Convert JSON array to CSV string."""
    data = json.loads(content)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON must be an array of objects or a single object for CSV conversion")
    return records_to_csv(data)


def yaml_to_csv(content: str) -> str:
    """Convert YAML to CSV string."""
    data = yaml.safe_load(content)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("YAML must be a list of mappings for CSV conversion")
    return records_to_csv(data)
