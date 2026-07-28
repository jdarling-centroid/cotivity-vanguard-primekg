"""Milestone 0 gate: prove the app can reach the local Oracle container.

Runs ``SELECT 1 FROM dual`` as the non-privileged app user.
"""

from __future__ import annotations

import sys

from vanguard_primekg.config import load_settings
from vanguard_primekg.db import connect
from vanguard_primekg.logging import get_logger

log = get_logger("smoke")


def main() -> int:
    settings = load_settings()
    log.info(
        "Connecting as %s to %s", settings.database.user, settings.database.dsn
    )
    with connect(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM dual")
            row = cur.fetchone()

    if row and row[0] == 1:
        log.info("OK: SELECT 1 FROM dual -> %s", row[0])
        print("SMOKE OK")
        return 0

    log.error("Unexpected result from SELECT 1 FROM dual: %r", row)
    print("SMOKE FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
