from __future__ import annotations

from dataclasses import dataclass

from ..crypto import PublicKey, encrypt, homomorphic_add_many, homomorphic_mul_const
from ..db.repository import DiseaseRepository


@dataclass(frozen=True)
class EncryptedCountSum:
    disease: str
    encrypted_count: int
    encrypted_sum: int
    row_count: int


@dataclass
class CloudAnalyticsService:
    """Server-side analytics running only on ciphertexts."""

    public_key: PublicKey
    repository: DiseaseRepository

    def encrypted_count_sum_for_disease(self, disease_name: str) -> EncryptedCountSum:
        ciphertexts = self.repository.get_encrypted_values_for_disease(disease_name)
        if not ciphertexts:
            encrypted_zero = encrypt(self.public_key, 0, r=1)
            return EncryptedCountSum(
                disease=disease_name,
                encrypted_count=encrypted_zero,
                encrypted_sum=encrypted_zero,
                row_count=0,
            )

        encrypted_sum = homomorphic_add_many(self.public_key, ciphertexts)
        return EncryptedCountSum(
            disease=disease_name,
            encrypted_count=encrypted_sum,
            encrypted_sum=encrypted_sum,
            row_count=len(ciphertexts),
        )

    def encrypted_count_for_disease(self, disease_name: str) -> int:
        return self.encrypted_count_sum_for_disease(disease_name).encrypted_count

    def encrypted_sum_for_disease(self, disease_name: str) -> int:
        return self.encrypted_count_sum_for_disease(disease_name).encrypted_sum

    def encrypted_scaled_count_for_disease(self, disease_name: str, scale: int) -> int:
        encrypted_count = self.encrypted_count_for_disease(disease_name)
        return homomorphic_mul_const(self.public_key, encrypted_count, scale)
