from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from .database import PathLike, connect, initialize_database


class DiseaseRepository:
    def __init__(self, db_path: PathLike):
        self.db_path = Path(db_path)

    def initialize_catalog(self, disease_names: list[str]) -> None:
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

    def add_patient(
        self,
        pseudonym: str,
        diagnoses: Mapping[str, int],
        encrypt_fn: Callable[[int], int],
    ) -> int:
        if not diagnoses:
            raise ValueError("diagnoses cannot be empty")

        with connect(self.db_path) as connection:
            diseases = {
                name: disease_id
                for disease_id, name in connection.execute(
                    "SELECT id, name FROM diseases"
                ).fetchall()
            }

            if not diseases:
                raise RuntimeError("Disease catalog is empty. Run setup first.")

            unknown = sorted(set(diagnoses.keys()) - set(diseases.keys()))
            if unknown:
                raise ValueError(f"Unknown diseases: {', '.join(unknown)}")

            cursor = connection.execute(
                "INSERT INTO patients(pseudonym) VALUES (?)",
                (pseudonym,),
            )
            patient_id = int(cursor.lastrowid)

            for disease_name, value in diagnoses.items():
                if value not in (0, 1):
                    raise ValueError("Diagnosis value must be 0 or 1")

                encrypted_flag = encrypt_fn(value)
                connection.execute(
                    """
                    INSERT INTO diagnoses(patient_id, disease_id, has_disease, encrypted_flag)
                    VALUES (?, ?, ?, ?)
                    """,
                    (patient_id, diseases[disease_name], int(value), str(encrypted_flag)),
                )

            return patient_id

    def list_diseases(self) -> list[str]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT name FROM diseases ORDER BY numeric_code"
            ).fetchall()
            return [row[0] for row in rows]

    def disease_mapping(self) -> dict[str, int]:
        with connect(self.db_path) as connection:
            rows = connection.execute(
                "SELECT name, numeric_code FROM diseases ORDER BY numeric_code"
            ).fetchall()
            return {name: int(code) for name, code in rows}

    def get_encrypted_values_for_disease(self, disease_name: str) -> list[int]:
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

    def get_plain_count_for_disease(self, disease_name: str) -> int:
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
        with connect(self.db_path) as connection:
            row = connection.execute("SELECT COUNT(*) FROM patients").fetchone()
            return int(row[0]) if row else 0
