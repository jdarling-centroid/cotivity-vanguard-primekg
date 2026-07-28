"""select_ai backend (Oracle Select AI / DBMS_CLOUD_AI).

Comparison backend for M7. It is faithfully scaffolded but intentionally NOT run
locally: the ``gvenzl/oracle-free`` image does not expose ``DBMS_CLOUD_AI`` (see
docs/DECISIONS.md #4), so this backend reports unavailability rather than
fabricating results. On an Autonomous DB (M8, with approval) it would register a
profile over pk_nodes/pk_edges and issue ``SELECT AI`` for each question.
"""

from __future__ import annotations

import oracledb

from ..logging import get_logger

log = get_logger("backend.select_ai")


def is_available(conn: oracledb.Connection) -> bool:
    """True only if DBMS_CLOUD_AI is present and callable for this user."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM all_objects WHERE object_name = 'DBMS_CLOUD_AI'"
            )
            (n,) = cur.fetchone()
        return n > 0
    except oracledb.DatabaseError:
        return False


class SelectAiUnavailable(RuntimeError):
    pass


class SelectAiBackend:
    name = "select_ai"

    def __init__(self, conn: oracledb.Connection) -> None:
        if not is_available(conn):
            raise SelectAiUnavailable(
                "DBMS_CLOUD_AI is not available on this local image; the Select AI "
                "comparison is deferred to an Autonomous DB (M8). The pgq backend "
                "is the local proof path."
            )
        self._conn = conn  # pragma: no cover - not reachable on the local image
