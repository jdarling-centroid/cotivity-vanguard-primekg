"""Stage 1 artifact naming and vendor/version validation."""

from __future__ import annotations

import re

_VENDOR_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,39}$")


def validate_vendor_id(vendor_id: str) -> str:
    value = vendor_id.strip().lower()
    if not _VENDOR_ID.fullmatch(value):
        raise ValueError(
            "vendor_id must be 2-40 lowercase letters, digits, underscores, or hyphens"
        )
    return value


def stage1_filename(vendor_id: str, kind: str, ext: str, *, version: int = 1) -> str:
    vendor = validate_vendor_id(vendor_id)
    if version < 1:
        raise ValueError("version must be >= 1")
    if kind not in {"qa-results", "reasoning-traces"}:
        raise ValueError(f"unsupported Track A artifact kind: {kind}")
    if ext not in {"jsonl", "json"}:
        raise ValueError(f"unsupported extension: {ext}")
    return f"vendor_{vendor}_stage1_{kind}_v{version}.{ext}"
