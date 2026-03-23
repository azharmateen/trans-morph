"""XML conversion with attribute handling, namespace stripping, and array detection."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from typing import Any
from collections import Counter

import yaml


def _strip_namespace(tag: str) -> str:
    """Remove namespace prefix from XML tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _element_to_dict(element: ET.Element, strip_ns: bool = True) -> dict[str, Any] | str:
    """Convert an XML element to a dictionary.

    Handles attributes (prefixed with @), text content (#text),
    and detects repeated child elements as arrays.
    """
    tag = _strip_namespace(element.tag) if strip_ns else element.tag
    result: dict[str, Any] = {}

    # Attributes
    for attr_name, attr_value in element.attrib.items():
        clean_name = _strip_namespace(attr_name) if strip_ns else attr_name
        result[f"@{clean_name}"] = attr_value

    # Count child tag occurrences to detect arrays
    child_tags = Counter(
        _strip_namespace(child.tag) if strip_ns else child.tag
        for child in element
    )

    # Process children
    children_by_tag: dict[str, list] = {}
    for child in element:
        child_tag = _strip_namespace(child.tag) if strip_ns else child.tag
        child_val = _element_to_dict(child, strip_ns)

        if child_tag not in children_by_tag:
            children_by_tag[child_tag] = []
        if isinstance(child_val, dict) and len(child_val) == 1 and child_tag in child_val:
            children_by_tag[child_tag].append(child_val[child_tag])
        else:
            children_by_tag[child_tag].append(child_val)

    for child_tag, values in children_by_tag.items():
        if child_tags[child_tag] > 1:
            # Multiple elements with same tag -> array
            result[child_tag] = values
        else:
            result[child_tag] = values[0]

    # Text content
    text = (element.text or "").strip()
    if text:
        if result:
            result["#text"] = text
        else:
            return text

    # Tail text (usually whitespace, ignore)
    return {tag: result} if result else {tag: text or ""}


def xml_to_dict(content: str, strip_ns: bool = True) -> dict[str, Any]:
    """Parse XML string into a dictionary."""
    # Remove XML declaration if present
    content = re.sub(r'<\?xml[^?]*\?>', '', content).strip()
    root = ET.fromstring(content)
    return _element_to_dict(root, strip_ns)


def _dict_to_element(tag: str, data: Any, parent: ET.Element | None = None) -> ET.Element:
    """Convert a dictionary back to an XML element."""
    elem = ET.SubElement(parent, tag) if parent is not None else ET.Element(tag)

    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith("@"):
                elem.set(key[1:], str(value))
            elif key == "#text":
                elem.text = str(value)
            elif isinstance(value, list):
                for item in value:
                    _dict_to_element(key, item, elem)
            elif isinstance(value, dict):
                _dict_to_element(key, value, elem)
            else:
                child = ET.SubElement(elem, key)
                child.text = str(value) if value is not None else ""
    elif isinstance(data, list):
        for item in data:
            _dict_to_element("item", item, elem)
    else:
        elem.text = str(data) if data is not None else ""

    return elem


def dict_to_xml(data: dict[str, Any], indent: int = 2) -> str:
    """Convert a dictionary to an XML string."""
    if len(data) == 1:
        root_tag = list(data.keys())[0]
        root_data = data[root_tag]
    else:
        root_tag = "root"
        root_data = data

    root = _dict_to_element(root_tag, root_data)
    ET.indent(root, space=" " * indent)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def xml_to_json(content: str) -> str:
    """Convert XML to JSON string."""
    data = xml_to_dict(content)
    return json.dumps(data, indent=2, default=str, ensure_ascii=False)


def xml_to_yaml(content: str) -> str:
    """Convert XML to YAML string."""
    data = xml_to_dict(content)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def json_to_xml(content: str) -> str:
    """Convert JSON to XML string."""
    data = json.loads(content)
    if isinstance(data, list):
        data = {"root": {"items": data}}
    return dict_to_xml(data)


def yaml_to_xml(content: str) -> str:
    """Convert YAML to XML string."""
    data = yaml.safe_load(content)
    if isinstance(data, list):
        data = {"root": {"items": data}}
    elif not isinstance(data, dict):
        data = {"root": {"value": data}}
    return dict_to_xml(data)
