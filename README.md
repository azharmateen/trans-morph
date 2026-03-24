# trans-morph

**Instant CLI format converter: CSV, JSON, XML, YAML, TOML -- any direction.**

One command to convert between data formats. Auto-detects input, infers types, handles nested structures, and validates output. No more writing throwaway conversion scripts.

## Why trans-morph?

- **Any-to-any conversion** -- CSV, JSON, XML, YAML, TOML in any combination (direct or chained through JSON)
- **Smart type inference** -- CSV numbers become numbers, booleans become booleans, dates stay dates
- **Auto-detection** -- figures out the input format from extension or content sniffing
- **Batch mode** -- convert entire directories in one command
- **Schema validation** -- validate converted output against JSON Schema
- **Nested structure handling** -- XML attributes, repeated elements, embedded JSON in CSV cells

## Install

```bash
pip install trans-morph
```

## Quick Start

```bash
# CSV to JSON (auto-detects input format)
trans-morph convert data.csv --to json

# XML to YAML
trans-morph convert config.xml --to yaml --output config.yaml

# JSON to TOML
trans-morph convert settings.json --to toml

# YAML to CSV
trans-morph convert records.yaml --to csv --output records.csv

# Batch convert all CSV files in a directory to JSON
trans-morph batch ./data/ --from csv --to json --output-dir ./json-data/

# Validate output against a schema
trans-morph validate output.json --schema schema.json

# See all supported conversions
trans-morph formats
```

## Supported Conversions

| From \ To | JSON | CSV | XML | YAML | TOML |
|-----------|------|-----|-----|------|------|
| **JSON**  | --   | Yes | Yes | Yes  | Yes  |
| **CSV**   | Yes  | --  | *   | Yes  | *    |
| **XML**   | Yes  | *   | --  | Yes  | *    |
| **YAML**  | Yes  | Yes | Yes | --   | Yes  |
| **TOML**  | Yes  | *   | *   | Yes  | --   |

*Chained conversions go through JSON as intermediary.*

## Features

### Type Inference (CSV)
```csv
name,age,active,score
Alice,30,true,95.5
Bob,25,false,87.2
```
Becomes:
```json
[
  {"name": "Alice", "age": 30, "active": true, "score": 95.5},
  {"name": "Bob", "age": 25, "active": false, "score": 87.2}
]
```

### XML Handling
- Attributes become `@attribute` keys
- Repeated elements become arrays automatically
- Namespaces are stripped by default
- Text content uses `#text` key when mixed with attributes

### Multi-Document YAML
Multi-document YAML files (`---` separated) convert to a JSON array.

### Schema Validation
```bash
trans-morph validate output.json --schema schema.json
# VALID: output.json passes schema validation.

trans-morph validate bad-data.json --schema schema.json
# INVALID: 3 error(s) found in bad-data.json:
#   - [0.email] 'not-an-email' is not a 'email'
#   - [1.age] -5 is less than the minimum of 0
#   - [2] 'name' is a required property
```

## Python API

```python
from trans_morph.converters.csv_converter import csv_to_json, json_to_csv
from trans_morph.converters.xml_converter import xml_to_json, json_to_xml
from trans_morph.converters.yaml_json import yaml_to_json, json_to_yaml
from trans_morph.validator import validate_file

# Convert
json_str = csv_to_json(open("data.csv").read())
xml_str = json_to_xml(json_str)

# Validate
result = validate_file("output.json", "schema.json")
print(result.summary())
```

## License

MIT
