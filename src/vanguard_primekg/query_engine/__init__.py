"""Query engine: single-SQL composition for categories A-D."""

from __future__ import annotations

from .engine import NodeEvidence, QueryEngine, QueryResult, SupportPath
from . import specs

__all__ = ["NodeEvidence", "QueryEngine", "QueryResult", "SupportPath", "specs"]
