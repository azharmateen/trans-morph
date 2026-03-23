"""CLI for trans-morph: instant format converter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .detector import detect_format
from .converters.csv_converter import (
    csv_to_json, csv_to_yaml, json_to_csv, yaml_to_csv, csv_to_records, records_to_csv,
)
from .converters.xml_converter import (
    xml_to_json, xml_to_yaml, json_to_xml, yaml_to_xml,
)
from .converters.yaml_json import (
    json_to_yaml, yaml_to_json, yaml_to_toml, toml_to_yaml, json_to_toml, toml_to_json,
)
from .converters.toml_converter import parse_toml, dump_toml


# Conversion matrix: (from_format, to_format) -> converter function
_CONVERTERS = {
    ("csv", "json"): csv_to_json,
    ("csv", "yaml"): csv_to_yaml,
    ("json", "csv"): json_to_csv,
    ("yaml", "csv"): yaml_to_csv,
    ("xml", "json"): xml_to_json,
    ("xml", "yaml"): xml_to_yaml,
    ("json", "xml"): json_to_xml,
    ("yaml", "xml"): yaml_to_xml,
    ("json", "yaml"): json_to_yaml,
    ("yaml", "json"): yaml_to_json,
    ("yaml", "toml"): yaml_to_toml,
    ("toml", "yaml"): toml_to_yaml,
    ("json", "toml"): json_to_toml,
    ("toml", "json"): toml_to_json,
}

SUPPORTED_FORMATS = ("json", "csv", "xml", "yaml", "toml")


def _get_converter(from_fmt: str, to_fmt: str):
    """Get the converter function for a format pair, or chain through JSON."""
    key = (from_fmt.lower(), to_fmt.lower())

    if key in _CONVERTERS:
        return _CONVERTERS[key]

    # Try chaining through JSON as intermediate
    to_json_key = (from_fmt.lower(), "json")
    from_json_key = ("json", to_fmt.lower())
    if to_json_key in _CONVERTERS and from_json_key in _CONVERTERS:
        to_json = _CONVERTERS[to_json_key]
        from_json = _CONVERTERS[from_json_key]
        return lambda content: from_json(to_json(content))

    return None


@click.group()
@click.version_option(package_name="trans-morph")
def cli():
    """trans-morph: Instant CLI format converter.

    Convert between CSV, JSON, XML, YAML, and TOML with automatic format detection.
    """
    pass


@cli.command()
@click.argument("input_path")
@click.option("--to", "-t", "to_fmt", required=True, type=click.Choice(SUPPORTED_FORMATS), help="Target format")
@click.option("--from", "-f", "from_fmt", type=click.Choice(SUPPORTED_FORMATS), help="Source format (auto-detected if omitted)")
@click.option("--output", "-o", help="Output file path (default: stdout)")
def convert(input_path: str, to_fmt: str, from_fmt: str | None, output: str | None):
    """Convert a file from one format to another.

    Examples:
        trans-morph convert data.csv --to json
        trans-morph convert config.xml --to yaml --output config.yaml
        trans-morph convert input.toml --to json
    """
    path = Path(input_path)
    if not path.exists():
        click.secho(f"File not found: {input_path}", fg="red", err=True)
        sys.exit(1)

    content = path.read_text(encoding="utf-8")

    # Detect source format
    if from_fmt is None:
        try:
            from_fmt = detect_format(input_path, content)
        except ValueError as e:
            click.secho(str(e), fg="red", err=True)
            sys.exit(1)

    if from_fmt == to_fmt:
        click.secho(f"Source and target format are both '{from_fmt}'. Nothing to convert.", fg="yellow", err=True)
        if output:
            Path(output).write_text(content, encoding="utf-8")
        else:
            click.echo(content)
        return

    converter = _get_converter(from_fmt, to_fmt)
    if converter is None:
        click.secho(
            f"No converter available for {from_fmt} -> {to_fmt}.",
            fg="red", err=True,
        )
        sys.exit(1)

    try:
        result = converter(content)
    except Exception as e:
        click.secho(f"Conversion error: {e}", fg="red", err=True)
        sys.exit(1)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.secho(f"Converted {from_fmt} -> {to_fmt}: {input_path} -> {output}", fg="green")
    else:
        click.echo(result)


@cli.command()
@click.argument("directory")
@click.option("--from", "-f", "from_fmt", required=True, type=click.Choice(SUPPORTED_FORMATS), help="Source format")
@click.option("--to", "-t", "to_fmt", required=True, type=click.Choice(SUPPORTED_FORMATS), help="Target format")
@click.option("--output-dir", "-d", help="Output directory (default: same as source)")
@click.option("--recursive/--no-recursive", "-r", default=False, help="Search subdirectories")
def batch(directory: str, from_fmt: str, to_fmt: str, output_dir: str | None, recursive: bool):
    """Batch convert all files in a directory.

    Examples:
        trans-morph batch ./data/ --from csv --to json
        trans-morph batch ./configs/ --from yaml --to toml --output-dir ./converted/
    """
    src_dir = Path(directory)
    if not src_dir.is_dir():
        click.secho(f"Not a directory: {directory}", fg="red", err=True)
        sys.exit(1)

    dst_dir = Path(output_dir) if output_dir else src_dir
    dst_dir.mkdir(parents=True, exist_ok=True)

    converter = _get_converter(from_fmt, to_fmt)
    if converter is None:
        click.secho(f"No converter for {from_fmt} -> {to_fmt}", fg="red", err=True)
        sys.exit(1)

    ext_map = {"json": ".json", "csv": ".csv", "xml": ".xml", "yaml": ".yaml", "toml": ".toml"}
    src_ext = ext_map.get(from_fmt, f".{from_fmt}")
    dst_ext = ext_map.get(to_fmt, f".{to_fmt}")

    pattern = f"**/*{src_ext}" if recursive else f"*{src_ext}"
    files = list(src_dir.glob(pattern))

    if not files:
        click.secho(f"No {src_ext} files found in {directory}", fg="yellow")
        return

    success = 0
    errors = 0
    for src_file in files:
        try:
            content = src_file.read_text(encoding="utf-8")
            result = converter(content)
            # Preserve relative path structure
            rel = src_file.relative_to(src_dir)
            dst_file = dst_dir / rel.with_suffix(dst_ext)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            dst_file.write_text(result, encoding="utf-8")
            click.secho(f"  OK: {src_file.name} -> {dst_file.name}", fg="cyan")
            success += 1
        except Exception as e:
            click.secho(f"  FAIL: {src_file.name}: {e}", fg="red", err=True)
            errors += 1

    click.secho(f"\nBatch complete: {success} converted, {errors} errors", fg="green" if errors == 0 else "yellow")


@cli.command()
@click.argument("input_path")
@click.option("--schema", "-s", required=True, help="Path to JSON Schema file")
def validate(input_path: str, schema: str):
    """Validate a data file against a JSON Schema.

    Examples:
        trans-morph validate output.json --schema schema.json
        trans-morph validate data.yaml --schema rules.yaml
    """
    from .validator import validate_file

    try:
        result = validate_file(input_path, schema)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if result.valid:
        click.secho(f"VALID: {input_path} passes schema validation.", fg="green")
    else:
        click.secho(f"INVALID: {result.error_count} error(s) found in {input_path}:", fg="red")
        for err in result.errors:
            click.echo(f"  - {err}")
        sys.exit(1)


@cli.command("formats")
def list_formats():
    """List all supported format conversions."""
    click.secho("Supported conversions:", fg="cyan", bold=True)
    for (src, dst), _ in sorted(_CONVERTERS.items()):
        click.echo(f"  {src:6s} -> {dst}")

    # Also show chained conversions
    click.secho("\nAdditional conversions (via JSON intermediary):", fg="cyan")
    for src in SUPPORTED_FORMATS:
        for dst in SUPPORTED_FORMATS:
            if src != dst and (src, dst) not in _CONVERTERS:
                if _get_converter(src, dst) is not None:
                    click.echo(f"  {src:6s} -> {dst} (chained)")


if __name__ == "__main__":
    cli()
