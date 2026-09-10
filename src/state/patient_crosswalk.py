from __future__ import annotations

import sqlite3
from pathlib import Path


class PatientCrosswalkError(Exception):
    """Raised when Patient crosswalk operations fail."""


def initialize_patient_crosswalk(
    database_path: str | Path,
) -> None:
    """
    Create the Patient crosswalk database/table if needed.
    """

    database_path = Path(
        database_path
    )

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with sqlite3.connect(
            database_path
        ) as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS patient_crosswalk (
                    source_system TEXT NOT NULL,
                    source_patient_id TEXT NOT NULL,
                    source_mrn TEXT,
                    source_mrn_system TEXT,

                    destination_system TEXT NOT NULL,
                    destination_base_url TEXT NOT NULL,
                    destination_patient_id TEXT NOT NULL,

                    created_utc TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    updated_utc TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP,

                    PRIMARY KEY (
                        source_system,
                        source_patient_id,
                        destination_system,
                        destination_base_url
                    )
                )
                """
            )

            connection.commit()

    except sqlite3.Error as exc:
        raise PatientCrosswalkError(
            f"Unable to initialize Patient crosswalk: {exc}"
        ) from exc


def record_patient_crosswalk(
    database_path: str | Path,
    *,
    source_system: str,
    source_patient_id: str,
    source_mrn: str,
    source_mrn_system: str,
    destination_system: str,
    destination_base_url: str,
    destination_patient_id: str,
) -> None:
    """
    Insert or update a Patient source-to-destination mapping.
    """

    initialize_patient_crosswalk(
        database_path
    )

    try:
        with sqlite3.connect(
            database_path
        ) as connection:

            connection.execute(
                """
                INSERT INTO patient_crosswalk (
                    source_system,
                    source_patient_id,
                    source_mrn,
                    source_mrn_system,
                    destination_system,
                    destination_base_url,
                    destination_patient_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT (
                    source_system,
                    source_patient_id,
                    destination_system,
                    destination_base_url
                )
                DO UPDATE SET
                    source_mrn =
                        excluded.source_mrn,

                    source_mrn_system =
                        excluded.source_mrn_system,

                    destination_patient_id =
                        excluded.destination_patient_id,

                    updated_utc =
                        CURRENT_TIMESTAMP
                """,
                (
                    source_system,
                    source_patient_id,
                    source_mrn,
                    source_mrn_system,
                    destination_system,
                    destination_base_url.rstrip("/"),
                    destination_patient_id,
                ),
            )

            connection.commit()

    except sqlite3.Error as exc:
        raise PatientCrosswalkError(
            f"Unable to record Patient crosswalk: {exc}"
        ) from exc


def get_destination_patient_id(
    database_path: str | Path,
    *,
    source_system: str,
    source_patient_id: str,
    destination_system: str,
    destination_base_url: str,
) -> str | None:
    """
    Return an existing destination Patient.id when present.
    """

    database_path = Path(
        database_path
    )

    if not database_path.exists():
        return None

    try:
        with sqlite3.connect(
            database_path
        ) as connection:

            cursor = connection.execute(
                """
                SELECT destination_patient_id
                FROM patient_crosswalk
                WHERE source_system = ?
                  AND source_patient_id = ?
                  AND destination_system = ?
                  AND destination_base_url = ?
                """,
                (
                    source_system,
                    source_patient_id,
                    destination_system,
                    destination_base_url.rstrip("/"),
                ),
            )

            row = cursor.fetchone()

    except sqlite3.Error as exc:
        raise PatientCrosswalkError(
            f"Unable to read Patient crosswalk: {exc}"
        ) from exc

    if row:
        return str(row[0])

    return None