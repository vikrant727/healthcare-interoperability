import sqlite3
from pathlib import Path
from datetime import datetime, timezone


DEFAULT_DB_PATH = Path("data/enroute.db")


class ResourceCrosswalk:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize_database(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS resource_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    source_system TEXT NOT NULL,
                    resource_type TEXT NOT NULL,

                    source_identifier_system TEXT,
                    source_identifier_value TEXT,

                    source_resource_id TEXT,

                    destination_system TEXT NOT NULL,
                    destination_resource_type TEXT NOT NULL,
                    destination_resource_id TEXT NOT NULL,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,

                   UNIQUE (
                    source_system,
                    resource_type,
                    source_resource_id,
                    destination_system
                   )
                )
                """
            )

    def upsert(
        self,
        *,
        source_system,
        resource_type,
        destination_system,
        destination_resource_id,
        source_identifier_system=None,
        source_identifier_value=None,
        source_resource_id=None,
        destination_resource_type=None,
    ):
        destination_resource_type = (
            destination_resource_type or resource_type
        )

        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO resource_mapping (
                    source_system,
                    resource_type,
                    source_identifier_system,
                    source_identifier_value,
                    source_resource_id,
                    destination_system,
                    destination_resource_type,
                    destination_resource_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT (
                    source_system,
                    resource_type,
                    source_resource_id,
                    destination_system
                )
                DO UPDATE SET
                    source_identifier_system = excluded.source_identifier_system,
                    source_identifier_value = excluded.source_identifier_value,
                    destination_resource_type = excluded.destination_resource_type,
                    destination_resource_id = excluded.destination_resource_id,
                    updated_at = excluded.updated_at
                """,
                (
                    source_system,
                    resource_type,
                    source_identifier_system,
                    source_identifier_value,
                    source_resource_id,
                    destination_system,
                    destination_resource_type,
                    destination_resource_id,
                    now,
                    now,
                ),
            )

    def lookup(
        self,
        *,
        source_system,
        resource_type,
        destination_system,
        source_identifier_system,
        source_identifier_value,
    ):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                """
                SELECT *
                FROM resource_mapping
                WHERE source_system = ?
                  AND resource_type = ?
                  AND destination_system = ?
                  AND source_identifier_system = ?
                  AND source_identifier_value = ?
                """,
                (
                    source_system,
                    resource_type,
                    destination_system,
                    source_identifier_system,
                    source_identifier_value,
                ),
            ).fetchone()

            return dict(row) if row else None

    def list_all(self):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """
                SELECT *
                FROM resource_mapping
                ORDER BY resource_type, source_identifier_value
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def lookup_by_source_resource_id(
        self,
        *,
        source_system,
        resource_type,
        source_resource_id,
        destination_system,
    ):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                """
                SELECT *
                FROM resource_mapping
                WHERE source_system = ?
                AND resource_type = ?
                AND source_resource_id = ?
                AND destination_system = ?
                """,
                (
                    source_system,
                    resource_type,
                    source_resource_id,
                    destination_system,
                ),
            ).fetchone()

            return dict(row) if row else None    