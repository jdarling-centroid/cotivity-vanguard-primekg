"""Settings loaded from the local ``.env``.

The harness runs on the host, so the default DSN targets the published host port
(``localhost:${ORACLE_PORT}/FREEPDB1``) rather than the container-internal
``oracle:1521`` DSN stored in ``.env`` for compose services.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_LOADED = False


def _load_env_once() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = _REPO_ROOT / ".env"
    if env_path.exists():
        # override=False: real process env wins over the file (test-friendly).
        load_dotenv(env_path, override=False)
    _ENV_LOADED = True


@dataclass(frozen=True)
class DatabaseConfig:
    user: str
    password: str
    dsn: str

    @property
    def host(self) -> str:
        return self.dsn.split("/", 1)[0].split(":", 1)[0]

    @property
    def is_local(self) -> bool:
        return self.host in {"localhost", "127.0.0.1", "oracle"}


@dataclass(frozen=True)
class Settings:
    database: DatabaseConfig
    admin_user: str
    admin_password: str
    repo_root: Path


def load_settings() -> Settings:
    """Build :class:`Settings` from the environment (loading ``.env`` once)."""
    _load_env_once()

    port = os.environ.get("ORACLE_PORT", "1522")
    host = os.environ.get("VPK_DB_HOST", "localhost")
    service = os.environ.get("VPK_DB_SERVICE", "FREEPDB1")
    dsn = os.environ.get("VPK_DB_DSN") or f"{host}:{port}/{service}"

    database = DatabaseConfig(
        user=os.environ.get("MC_DATABASE__USER", "MC"),
        password=os.environ.get("MC_DATABASE__PASSWORD", ""),
        dsn=dsn,
    )
    return Settings(
        database=database,
        admin_user=os.environ.get("ORACLE_ADMIN_USER", "SYSTEM"),
        admin_password=os.environ.get(
            "ORACLE_ADMIN_PASSWORD", os.environ.get("ORACLE_PWD", "")
        ),
        repo_root=_REPO_ROOT,
    )
