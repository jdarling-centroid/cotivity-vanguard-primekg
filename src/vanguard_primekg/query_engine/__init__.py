"""Query engine: single-SQL composition for categories A–D."""

from __future__ import annotations

from .engine import QueryEngine, QueryResult
from . import specs

__all__ = ["QueryEngine", "QueryResult", "specs"]
