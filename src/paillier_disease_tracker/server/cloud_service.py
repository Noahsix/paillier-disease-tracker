from __future__ import annotations

from dataclasses import dataclass

from ..crypto import PublicKey, encrypt, homomorphic_add_many, homomorphic_mul_const
from ..db.repository import DiseaseRepository


@dataclass
class CloudAnalyticsService:
    """Server-side analytics running only on ciphertexts."""

    public_key: PublicKey
    repository: DiseaseRepository

    def encrypted_count_for_disease(self, disease_name: str) -> int:
        ciphertexts = self.repository.get_encrypted_values_for_disease(disease_name)
        if not ciphertexts:
            return encrypt(self.public_key, 0, r=1)
        return homomorphic_add_many(self.public_key, ciphertexts)

    def encrypted_scaled_count_for_disease(self, disease_name: str, scale: int) -> int:
        encrypted_count = self.encrypted_count_for_disease(disease_name)
        return homomorphic_mul_const(self.public_key, encrypted_count, scale)
