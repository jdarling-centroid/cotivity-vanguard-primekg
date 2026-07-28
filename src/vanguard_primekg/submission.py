"""Stage 1 submission filename convention (reused from ../ai-proposal design §8).

The vendored ``finalizer.py`` imports ``stage1_filename`` from here; keeping the
convention identical means the existing report/validator grades our runs
unchanged.
"""

from __future__ import annotations


def stage1_filename(vendor_id: str, kind: str, ext: str) -> str:
    """``vendor_<vendor_id>_stage1_<kind>_v1.<ext>`` (e.g. results/jsonl)."""
    return f"vendor_{vendor_id}_stage1_{kind}_v1.{ext}"
