"""Repository factory for selecting SQLite or PostgreSQL persistence backends."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from src.storage.repository import SqliteRepository

logger = logging.getLogger(__name__)


def create_repository() -> Optional[Any]:
    backend = os.getenv("PERSISTENCE_BACKEND", "sqlite").strip().lower()
    if backend == "postgres":
        try:
            from src.storage.postgres_repository import PostgresRepository

            return PostgresRepository(os.getenv("POSTGRES_DSN", "").strip() or None)
        except Exception as exc:
            logger.warning("PostgreSQL repository unavailable; falling back to SQLite: %s", exc)

    sqlite_enabled = os.getenv("SQLITE_PERSISTENCE_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    if not sqlite_enabled:
        logger.warning("SQLite persistence disabled and PostgreSQL unavailable; persistence is disabled")
        return None

    return SqliteRepository(os.getenv("SQLITE_DB_PATH"))
