"""Optional Oracle driver import used to keep offline unit tests importable.

The production package declares ``oracledb`` as a required dependency.  Some
review environments do not provide the binary/package and cannot reach the
local Oracle container.  Importing through this module lets non-database tests
run while every attempted connection still fails closed with a clear error.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - exercised in environments with python-oracledb
    import oracledb as oracledb  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover - behavior covered indirectly
    class _DatabaseError(Exception):
        pass

    class _MissingOracleDb:
        DatabaseError = _DatabaseError
        Connection = Any

        @staticmethod
        def connect(*args: Any, **kwargs: Any) -> Any:
            del args, kwargs
            raise RuntimeError(
                "python-oracledb is not installed; database operations are unavailable"
            )

    oracledb = _MissingOracleDb()  # type: ignore[assignment]

__all__ = ["oracledb"]
