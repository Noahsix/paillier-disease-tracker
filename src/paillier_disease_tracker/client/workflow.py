from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
        plain_count_reference = plain_sum_reference

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
