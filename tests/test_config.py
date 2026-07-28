"""Unit tests for config + the local-only DB guard (no live DB required)."""

from __future__ import annotations

import pytest

from vanguard_primekg import db
from vanguard_primekg.config import load_settings


def test_default_dsn_targets_local_host_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VPK_DB_DSN", raising=False)
    monkeypatch.delenv("VPK_DB_HOST", raising=False)
    monkeypatch.setenv("ORACLE_PORT", "1522")

    settings = load_settings()

    assert settings.database.dsn == "localhost:1522/FREEPDB1"
    assert settings.database.is_local


def test_assert_local_allows_local_hosts() -> None:
    for dsn in (
        "localhost:1522/FREEPDB1",
        "127.0.0.1:1521/FREEPDB1",
        "oracle:1521/FREEPDB1",
    ):
        db._assert_local(dsn)  # should not raise


def test_assert_local_refuses_remote(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VPK_ALLOW_REMOTE", raising=False)
    with pytest.raises(RuntimeError):
        db._assert_local("adb.us-ashburn-1.oraclecloud.com:1522/svc_high")


def test_assert_local_remote_allowed_with_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VPK_ALLOW_REMOTE", "1")
    db._assert_local("adb.us-ashburn-1.oraclecloud.com:1522/svc_high")
