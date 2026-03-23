"""Auto-detect input format from file extension and content sniffing."""

from __future__ import annotations

from pathlib import Path


# Extension to format mapping
_EXT_MAP = {
    ".json": "json",
    ".csv": "csv",
    ".tsv": "csv",
    ".xml": "xml",
    ".html": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
}


def detect_format_from_extension(path: str) -> str | None:
    """Detect format from file extension."""
    ext = Path(path).suffix.lower()
    return _EXT_MAP.get(ext)


def detect_format_from_content(content: str) -> str | None:
    """Detect format by sniffing content."""
    stripped = content.strip()

    if not stripped:
        return None

    # JSON: starts with { or [
    if stripped[0] in ("{", "["):
        return "json"

    # XML: starts with < (including <?xml)
    if stripped[0] == "<":
        return "xml"

    # TOML: has [section] headers and key = value pairs
    lines = stripped.split("\n", 20)
    toml_score = 0
    for line in lines:
        line = line.strip()
        if line.startswith("[") and line.endswith("]") and not line.startswith("[["):
            toml_score += 2
        elif "=" in line and not line.startswith("#"):
            parts = line.split("=", 1)
            key = parts[0].strip()
            if key and " " not in key and not key.startswith("-"):
                toml_score += 1

    # YAML: has key: value pairs, often starts with --- or has indentation
    yaml_score = 0
    for line in lines:
        line_s = line.strip()
        if line_s == "---":
            yaml_score += 3
        elif ": " in line_s and not line_s.startswith("#"):
            yaml_score += 1
        elif line_s.startswith("- "):
            yaml_score += 1

    # CSV: has commas in most lines, consistent column count
    csv_score = 0
    comma_counts = []
    for line in lines:
        if line.strip():
            count = line.count(",")
            comma_counts.append(count)
    if comma_counts and len(comma_counts) >= 2:
        # Consistent comma counts suggest CSV
        if comma_counts[0] > 0 and all(c == comma_counts[0] for c in comma_counts[:5]):
            csv_score = len(comma_counts) * 2

    # Pick highest score
    scores = {"toml": toml_score, "yaml": yaml_score, "csv": csv_score}
    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    return None


def detect_format(path: str, content: str | None = None) -> str:
    """Detect format from file path and/or content.

    Args:
        path: File path (used for extension detection).
        content: File content (used for content sniffing).

    Returns:
        Detected format string.

    Raises:
        ValueError: If format cannot be detected.
    """
    # Try extension first
    fmt = detect_format_from_extension(path)
    if fmt:
        return fmt

    # Try content sniffing
    if content is None:
        content = Path(path).read_text(encoding="utf-8")

    fmt = detect_format_from_content(content)
    if fmt:
        return fmt

    raise ValueError(
        f"Cannot detect format for '{path}'. "
        "Supported formats: json, csv, xml, yaml, toml. "
        "Use --from to specify explicitly."
    )
