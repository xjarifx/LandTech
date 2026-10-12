"""Canonical deed representation used for hashing and verification."""

import json
import unicodedata
from decimal import Decimal
from typing import Any


def _normal(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, float):
        return format(Decimal(str(value)).normalize(), "f")
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, dict):
        return {str(key): _normal(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_normal(item) for item in value]
    return value


def canonicalize(deed: dict[str, Any]) -> bytes:
    """Sort keys, normalize Bengali Unicode, and use stable JSON formatting."""
    return json.dumps(_normal(deed), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
