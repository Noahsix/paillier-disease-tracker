from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random

from ..config import DEFAULT_DISEASES
from ..crypto import PrivateKey, PublicKey, decrypt, encrypt, generate_keypair
from ..data_samples import get_demo_patients
from ..db.repository import DiseaseRepository
from ..server import CloudAnalyticsService


@dataclass
class CountResult:
    disease: str
    encrypted_result: int
    decrypted_result: int
    plain_reference: int


@dataclass
class CountSumResult:
    disease: str
    encrypted_count: int
    encrypted_sum: int
    decrypted_count: int
    decrypted_sum: int
    plain_count_reference: int
    plain_sum_reference: int
    row_count: int


@dataclass
class FlowRow:
    pseudonym: str
    plain_value: int
    ciphertext: int


@dataclass
class DiseaseCountFlow:
    disease: str
    rows: list[FlowRow]
    encrypted_homomorphic_result: int
    decrypted_result: int
    plain_reference: int


@dataclass
class DiseaseValidationResult:
    disease: str
    homomorphic_sum: int
    plain_sum: int
    homomorphic_count: int
    plain_count: int
    is_valid: bool


@dataclass
class ValidationReport:
    results: list[DiseaseValidationResult]
    total_diseases: int
    passed_diseases: int
    all_valid: bool


class ClientApplication:
    def __init__(
        self,
        db_path: str | Path,
        public_key: PublicKey,
        private_key: PrivateKey,
    ):
        self.public_key = public_key
        self.private_key = private_key
        self.repository = DiseaseRepository(db_path)
        self.server = CloudAnalyticsService(public_key, self.repository)

    @classmethod
    def create_new(
        cls,
        db_path: str | Path,
        disease_names: list[str] | None = None,
        key_size: int = 512,
    ) -> tuple["ClientApplication", PublicKey, PrivateKey]:
        public_key, private_key = generate_keypair(key_size)
        app = cls(db_path=db_path, public_key=public_key, private_key=private_key)
        app.initialize_catalog(disease_names or list(DEFAULT_DISEASES))
        return app, public_key, private_key

    def initialize_catalog(self, disease_names: list[str] | None = None) -> None:
        self.repository.initialize_catalog(disease_names or list(DEFAULT_DISEASES))

    def encrypt_value(self, value: int) -> int:
        return encrypt(self.public_key, value)

    def decrypt_value(self, ciphertext: int) -> int:
        return decrypt(self.public_key, self.private_key, ciphertext)

    def add_patient(self, pseudonym: str, diagnoses: dict[str, int]) -> int:
        return self.repository.add_patient(pseudonym, diagnoses, self.encrypt_value)

    def seed_demo_data(self) -> int:
        added = 0
        offset = self.repository.total_patients()
        for index, (pseudonym, diagnoses) in enumerate(get_demo_patients(), start=1):
            unique_pseudonym = f"{pseudonym}_{offset + index:04d}"
            self.add_patient(unique_pseudonym, diagnoses)
            added += 1
        return added

    def seed_bulk_data(
        self,
        patient_count: int,
        seed: int = 42,
        pseudonym_prefix: str = "bulk_patient",
        batch_size: int = 1000,
    ) -> int:
        if patient_count < 0:
            raise ValueError("patient_count cannot be negative")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if patient_count == 0:
            return 0

        disease_names = self.list_diseases()
        if not disease_names:
            raise RuntimeError("Disease catalog is empty. Run setup first.")

        randomizer = Random(seed)
        offset = self.repository.total_patients()
        inserted = 0

        while inserted < patient_count:
            current_batch_size = min(batch_size, patient_count - inserted)
            records: list[tuple[str, dict[str, int]]] = []

            for index in range(current_batch_size):
                absolute_index = offset + inserted + index + 1
                pseudonym = f"{pseudonym_prefix}_{absolute_index:08d}"
                diagnoses = {name: randomizer.randint(0, 1) for name in disease_names}
                records.append((pseudonym, diagnoses))

            self.repository.add_patients_bulk(records, self.encrypt_value)
            inserted += current_batch_size

        return inserted

    def count_disease(self, disease_name: str) -> CountResult:
        count_sum = self.count_and_sum_disease(disease_name)
        return CountResult(
            disease=disease_name,
            encrypted_result=count_sum.encrypted_count,
            decrypted_result=count_sum.decrypted_count,
            plain_reference=count_sum.plain_count_reference,
        )

    def count_and_sum_disease(self, disease_name: str) -> CountSumResult:
        encrypted_count_sum = self.server.encrypted_count_sum_for_disease(disease_name)

        decrypted_count = self.decrypt_value(encrypted_count_sum.encrypted_count)
        decrypted_sum = self.decrypt_value(encrypted_count_sum.encrypted_sum)

        plain_sum_reference = self.repository.get_plain_sum_for_disease(disease_name)
        plain_count_reference = self.repository.get_plain_count_for_disease(disease_name)

        return CountSumResult(
            disease=disease_name,
            encrypted_count=encrypted_count_sum.encrypted_count,
            encrypted_sum=encrypted_count_sum.encrypted_sum,
            decrypted_count=decrypted_count,
            decrypted_sum=decrypted_sum,
            plain_count_reference=plain_count_reference,
            plain_sum_reference=plain_sum_reference,
            row_count=encrypted_count_sum.row_count,
        )

    def build_count_flow(self, disease_name: str) -> DiseaseCountFlow:
        count_sum = self.count_and_sum_disease(disease_name)
        rows = [
            FlowRow(
                pseudonym=pseudonym,
                plain_value=plain_value,
                ciphertext=ciphertext,
            )
            for pseudonym, plain_value, ciphertext in self.repository.get_plain_and_encrypted_rows_for_disease(
                disease_name
            )
        ]

        return DiseaseCountFlow(
            disease=disease_name,
            rows=rows,
            encrypted_homomorphic_result=count_sum.encrypted_sum,
            decrypted_result=count_sum.decrypted_sum,
            plain_reference=count_sum.plain_sum_reference,
        )

    def list_diseases(self) -> list[str]:
        return self.repository.list_diseases()

    def validate_disease_sum(self, disease_name: str) -> DiseaseValidationResult:
        count_sum = self.count_and_sum_disease(disease_name)
        is_valid = (
            count_sum.decrypted_sum == count_sum.plain_sum_reference
            and count_sum.decrypted_count == count_sum.plain_count_reference
        )

        return DiseaseValidationResult(
            disease=disease_name,
            homomorphic_sum=count_sum.decrypted_sum,
            plain_sum=count_sum.plain_sum_reference,
            homomorphic_count=count_sum.decrypted_count,
            plain_count=count_sum.plain_count_reference,
            is_valid=is_valid,
        )

    def validate_all_disease_sums(self) -> ValidationReport:
        disease_names = self.list_diseases()
        results = [self.validate_disease_sum(name) for name in disease_names]
        passed_diseases = sum(1 for result in results if result.is_valid)
        total_diseases = len(results)

        return ValidationReport(
            results=results,
            total_diseases=total_diseases,
            passed_diseases=passed_diseases,
            all_valid=passed_diseases == total_diseases,
        )
