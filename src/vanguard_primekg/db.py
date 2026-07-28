"""Thin oracledb connection helpers with a hard local-only guard.

Enforces the local-first invariant: connecting to a non-local DSN raises unless
``VPK_ALLOW_REMOTE=1`` is set explicitly (Milestone 8, with user approval).
"""

from __future__ import annotations

import os

from .oracle_compat import oracledb

from .config import Settings, load_settings

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "oracle"}


def _assert_local(dsn: str) -> None:
    if os.environ.get("VPK_ALLOW_REMOTE") == "1":
        return
    host = dsn.split("/", 1)[0].split(":", 1)[0]
    if host not in _LOCAL_HOSTS:
        raise RuntimeError(
            f"Refusing to connect to non-local DSN host {host!r}. "
            "Local-first invariant is in force; set VPK_ALLOW_REMOTE=1 only with "
            "explicit approval (Milestone 8)."
        )


def connect(
    settings: Settings | None = None, *, admin: bool = False
) -> oracledb.Connection:
    """Open a connection as the app user (default) or the admin user."""
    settings = settings or load_settings()
    _assert_local(settings.database.dsn)

    if admin:
        return oracledb.connect(
            user=settings.admin_user,
            password=settings.admin_password,
            dsn=settings.database.dsn,
        )
    db = settings.database
    return oracledb.connect(user=db.user, password=db.password, dsn=db.dsn)
