from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS diseases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    numeric_code INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pseudonym TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    disease_id INTEGER NOT NULL,
    has_disease INTEGER NOT NULL CHECK (has_disease IN (0, 1)),
    encrypted_flag TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
    FOREIGN KEY (disease_id) REFERENCES diseases (id) ON DELETE CASCADE,
    UNIQUE (patient_id, disease_id)
);
"""


def connect(db_path: PathLike) -> sqlite3.Connection:
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_file, timeout=10)
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA busy_timeout = 5000;")
    return connection


def initialize_database(db_path: PathLike) -> None:
    with connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
