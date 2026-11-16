
from __future__ import annotations

import os
import sqlite3

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "healthinsight.db"


def get_db_path() -> Path:
    configured = os.getenv("DATABASE_PATH", "").strip()

    path = (
        Path(configured).expanduser()
        if configured
        else DEFAULT_DB_PATH
    )

    if not path.is_absolute():
        path = BASE_DIR / path

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        get_db_path(),
        timeout=15,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    connection = get_connection()

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def reset_sequence_when_empty(
    connection: sqlite3.Connection,
) -> None:
    has_records = connection.execute(
        "SELECT EXISTS(SELECT 1 FROM patients)"
    ).fetchone()[0]

    if not has_records:
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'patients'"
        )


def init_db() -> None:
    with database_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL,
                glucose REAL NOT NULL CHECK (glucose > 0),
                haemoglobin REAL NOT NULL CHECK (haemoglobin > 0),
                cholesterol REAL NOT NULL CHECK (cholesterol > 0),
                remarks TEXT NOT NULL DEFAULT '',
                ai_status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        reset_sequence_when_empty(connection)


def add_patient(
    data: dict[str, Any],
    remarks: str,
    ai_status: str,
) -> int:

    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO patients (
                full_name,
                dob,
                email,
                glucose,
                haemoglobin,
                cholesterol,
                remarks,
                ai_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["full_name"],
                data["dob"],
                data["email"],
                float(data["glucose"]),
                float(data["haemoglobin"]),
                float(data["cholesterol"]),
                remarks,
                ai_status,
            ),
        )

        return int(cursor.lastrowid)


def list_patients() -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM patients ORDER BY id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


def get_patient(
    patient_id: int,
) -> dict[str, Any] | None:

    with database_connection() as connection:
        row = connection.execute(
            "SELECT * FROM patients WHERE id = ?",
            (int(patient_id),),
        ).fetchone()

        return dict(row) if row else None


def update_patient_email(
    patient_id: int,
    new_email: str,
) -> None:

    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE patients
            SET email = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_email, int(patient_id)),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Patient record {patient_id} was not found."
            )


def update_patient_remarks(
    patient_id: int,
    remarks: str,
    ai_status: str,
) -> None:

    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE patients
            SET remarks = ?,
                ai_status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (remarks, ai_status, int(patient_id)),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Patient record {patient_id} was not found."
            )


def delete_patient(patient_id: int) -> None:

    with database_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM patients WHERE id = ?",
            (int(patient_id),),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Patient record {patient_id} was not found."
            )

        reset_sequence_when_empty(connection)
