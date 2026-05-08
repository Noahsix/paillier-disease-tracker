from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from .database import PathLike, connect, initialize_database
from .lock import acquire_db_lock


class DiseaseRepository:
    def __init__(self, db_path: PathLike):
        self.db_path = Path(db_path)

    def _load_disease_ids(self, connection) -> dict[str, int]:
        diseases = {
            name: disease_id
            for disease_id, name in connection.execute(
                "SELECT id, name FROM diseases"
            ).fetchall()
        }

        if not diseases:
            raise RuntimeError("Disease catalog is empty. Run setup first.")

        return diseases

    def _validate_diagnoses(self, diagnoses: Mapping[str, int], diseases: Mapping[str, int]) -> None:
        if not diagnoses:
            raise ValueError("diagnoses cannot be empty")

        unknown = sorted(set(diagnoses.keys()) - set(diseases.keys()))
        if unknown:
            raise ValueError(f"Unknown diseases: {', '.join(unknown)}")

        for value in diagnoses.values():
            if value not in (0, 1):
                raise ValueError("Diagnosis value must be 0 or 1")

    def _insert_patient(
        self,
        connection,
        diseases: Mapping[str, int],
        pseudonym: str,
        diagnoses: Mapping[str, int],
        encrypt_fn: Callable[[int], int],
    ) -> int:
        self._validate_diagnoses(diagnoses, diseases)

        cursor = connection.execute(
            "INSERT INTO patients(pseudonym) VALUES (?)",
            (pseudonym,),
        )
        patient_id = int(cursor.lastrowid)

        for disease_name, value in diagnoses.items():
            encrypted_flag = encrypt_fn(value)
            connection.execute(
                """
                INSERT INTO diagnoses(patient_id, disease_id, has_disease, encrypted_flag)
                VALUES (?, ?, ?, ?)
                """,
                (patient_id, diseases[disease_name], int(value), str(encrypted_flag)),
            )

        return patient_id

    def initialize_catalog(self, disease_names: list[str]) -> None:
        with acquire_db_lock(self.db_path):
            initialize_database(self.db_path)
            with connect(self.db_path) as connection:
                for numeric_code, name in enumerate(disease_names, start=1):
                    connection.execute(
                        """
                        INSERT INTO diseases(name, numeric_code)
                        VALUES (?, ?)
                        ON CONFLICT(name) DO UPDATE SET numeric_code=excluded.numeric_code
                        """,
                        (name, numeric_code),
                    )

    def add_disease(self, disease_name: str, encrypt_fn: Callable[[int], int]) -> None:
        name = disease_name.strip()
        if not name:
            raise ValueError("Disease name cannot be empty")

        with acquire_db_lock(self.db_path):
            initialize_database(self.db_path)
            with connect(self.db_path) as connection:
                existing = connection.execute(
                    "SELECT id FROM diseases WHERE name = ?",
                    (name,),
                ).fetchone()
                if existing:
                    raise ValueError(f"Disease already exists: {name}")

                row = connection.execute(
                    "SELECT COALESCE(MAX(numeric_code), 0) FROM diseases"
                ).fetchone()
                next_code = int(row[0]) + 1

                cursor = connection.execute(
                    "INSERT INTO diseases(name, numeric_code) VALUES (?, ?)",
                    (name, next_code),
                )
                disease_id = int(cursor.lastrowid)

                patient_rows = connection.execute(
                    "SELECT id FROM patients ORDER BY id"
                ).fetchall()
                for (patient_id,) in patient_rows:
                    encrypted_flag = encrypt_fn(0)
                    connection.execute(
                        """
                        INSERT INTO diagnoses(patient_id, disease_id, has_disease, encrypted_flag)
                        VALUES (?, ?, ?, ?)
                        """,
                        (patient_id, disease_id, 0, str(encrypted_flag)),
                    )

    def reset_catalog(self, disease_names: list[str]) -> None:
        seen: set[str] = set()
        normalized: list[str] = []
        for name in disease_names:
            cleaned = name.strip()
            if not cleaned or cleaned in seen:
                continue
            normalized.append(cleaned)
            seen.add(cleaned)

        if not normalized:
            raise ValueError("disease_names cannot be empty")

        with acquire_db_lock(self.db_path):
            initialize_database(self.db_path)
            with connect(self.db_path) as connection:
                existing_rows = connection.execute(
                    "SELECT id, name FROM diseases"
                ).fetchall()
                to_remove_ids = [row[0] for row in existing_rows if row[1] not in normalized]

                if to_remove_ids:
                    placeholder = ",".join("?" for _ in to_remove_ids)
                    connection.execute(
                        f"DELETE FROM diagnoses WHERE disease_id IN ({placeholder})",
                        to_remove_ids,
                    )
                    connection.execute(
                        f"DELETE FROM diseases WHERE id IN ({placeholder})",
                        to_remove_ids,
                    )

                for numeric_code, name in enumerate(normalized, start=1):
                    connection.execute(
                        """
                        INSERT INTO diseases(name, numeric_code)
                        VALUES (?, ?)
                        ON CONFLICT(name) DO UPDATE SET numeric_code=excluded.numeric_code
                        """,
                        (name, numeric_code),
                    )

    def add_patient(
        self,
        pseudonym: str,
        diagnoses: Mapping[str, int],
        encrypt_fn: Callable[[int], int],
    ) -> int:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                diseases = self._load_disease_ids(connection)
                return self._insert_patient(connection, diseases, pseudonym, diagnoses, encrypt_fn)

    def add_patients_bulk(
        self,
        records: list[tuple[str, Mapping[str, int]]],
        encrypt_fn: Callable[[int], int],
    ) -> int:
        if not records:
            return 0

        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                diseases = self._load_disease_ids(connection)
                inserted = 0
                for pseudonym, diagnoses in records:
                    self._insert_patient(connection, diseases, pseudonym, diagnoses, encrypt_fn)
                    inserted += 1
                return inserted

    def list_diseases(self) -> list[str]:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                rows = connection.execute(
                    "SELECT name FROM diseases ORDER BY numeric_code"
                ).fetchall()
                return [row[0] for row in rows]

    def disease_mapping(self) -> dict[str, int]:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                rows = connection.execute(
                    "SELECT name, numeric_code FROM diseases ORDER BY numeric_code"
                ).fetchall()
                return {name: int(code) for name, code in rows}

    def get_encrypted_values_for_disease(self, disease_name: str) -> list[int]:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                rows = connection.execute(
                    """
                    SELECT dg.encrypted_flag
                    FROM diagnoses dg
                    JOIN diseases d ON d.id = dg.disease_id
                    WHERE d.name = ?
                    ORDER BY dg.id
                    """,
                    (disease_name,),
                ).fetchall()
                return [int(row[0]) for row in rows]

    def get_encrypted_rows_for_disease(self, disease_name: str) -> list[tuple[str, int]]:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                rows = connection.execute(
                    """
                    SELECT p.pseudonym, dg.encrypted_flag
                    FROM diagnoses dg
                    JOIN diseases d ON d.id = dg.disease_id
                    JOIN patients p ON p.id = dg.patient_id
                    WHERE d.name = ?
                    ORDER BY p.id
                    """,
                    (disease_name,),
                ).fetchall()
                return [(str(pseudonym), int(ciphertext)) for pseudonym, ciphertext in rows]

    def get_plain_and_encrypted_rows_for_disease(
        self,
        disease_name: str,
    ) -> list[tuple[str, int, int]]:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                rows = connection.execute(
                    """
                    SELECT p.pseudonym, dg.has_disease, dg.encrypted_flag
                    FROM diagnoses dg
                    JOIN diseases d ON d.id = dg.disease_id
                    JOIN patients p ON p.id = dg.patient_id
                    WHERE d.name = ?
                    ORDER BY p.id
                    """,
                    (disease_name,),
                ).fetchall()
                return [
                    (str(pseudonym), int(plain_value), int(ciphertext))
                    for pseudonym, plain_value, ciphertext in rows
                ]

    def get_plain_count_for_disease(self, disease_name: str) -> int:
        return self.get_plain_sum_for_disease(disease_name)

    def get_plain_sum_for_disease(self, disease_name: str) -> int:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                row = connection.execute(
                    """
                    SELECT COALESCE(SUM(dg.has_disease), 0)
                    FROM diagnoses dg
                    JOIN diseases d ON d.id = dg.disease_id
                    WHERE d.name = ?
                    """,
                    (disease_name,),
                ).fetchone()
                return int(row[0]) if row else 0

    def total_patients(self) -> int:
        with acquire_db_lock(self.db_path):
            initialize_database(self.db_path)
            with connect(self.db_path) as connection:
                row = connection.execute("SELECT COUNT(*) FROM patients").fetchone()
                return int(row[0]) if row else 0

    def clear_patient_data(self) -> None:
        with acquire_db_lock(self.db_path):
            with connect(self.db_path) as connection:
                connection.execute("DELETE FROM diagnoses")
                connection.execute("DELETE FROM patients")

    def get_db_preview(
        self,
        limit: int = 50,
    ) -> tuple[list[str], list[tuple[str, dict[str, int]]], int, int]:
        if limit <= 0:
            raise ValueError("limit must be positive")

        with acquire_db_lock(self.db_path):
            initialize_database(self.db_path)
            with connect(self.db_path) as connection:
                disease_rows = connection.execute(
                    "SELECT name FROM diseases ORDER BY numeric_code"
                ).fetchall()
                disease_names = [row[0] for row in disease_rows]

                total_patients_row = connection.execute("SELECT COUNT(*) FROM patients").fetchone()
                total_patients = int(total_patients_row[0]) if total_patients_row else 0

                total_diagnoses_row = connection.execute(
                    "SELECT COUNT(*) FROM diagnoses"
                ).fetchone()
                total_diagnoses = int(total_diagnoses_row[0]) if total_diagnoses_row else 0

                patient_rows = connection.execute(
                    "SELECT id, pseudonym FROM patients ORDER BY id LIMIT ?",
                    (limit,),
                ).fetchall()

                if not patient_rows:
                    return disease_names, [], total_patients, total_diagnoses

                patient_ids = [row[0] for row in patient_rows]
                placeholder = ",".join("?" for _ in patient_ids)
                diagnoses_rows = connection.execute(
                    f"""
                    SELECT p.id, d.name, dg.has_disease
                    FROM diagnoses dg
                    JOIN diseases d ON d.id = dg.disease_id
                    JOIN patients p ON p.id = dg.patient_id
                    WHERE p.id IN ({placeholder})
                    ORDER BY p.id, d.numeric_code
                    """,
                    patient_ids,
                ).fetchall()

                patient_index: dict[int, dict[str, int]] = {
                    patient_id: {name: 0 for name in disease_names}
                    for patient_id in patient_ids
                }
                for patient_id, disease_name, has_disease in diagnoses_rows:
                    patient_index[int(patient_id)][str(disease_name)] = int(has_disease)

                rows: list[tuple[str, dict[str, int]]] = []
                for patient_id, pseudonym in patient_rows:
                    rows.append((str(pseudonym), patient_index.get(int(patient_id), {})))

                return disease_names, rows, total_patients, total_diagnoses
