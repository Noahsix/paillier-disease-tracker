from __future__ import annotations

from typing import Iterable

from .config import DEFAULT_DISEASES


def _build_record(pseudonym: str, positive_diseases: Iterable[str]) -> tuple[str, dict[str, int]]:
    positive = set(positive_diseases)
    diagnoses = {name: int(name in positive) for name in DEFAULT_DISEASES}
    return pseudonym, diagnoses


def get_demo_patients() -> list[tuple[str, dict[str, int]]]:
    """Deterministic sample set for early integration and testing."""
    return [
        _build_record("patient_001", ["grypa", "alergia"]),
        _build_record("patient_002", ["covid19"]),
        _build_record("patient_003", ["grypa", "nadcisnienie"]),
        _build_record("patient_004", ["cukrzyca", "astma"]),
        _build_record("patient_005", ["grypa", "covid19", "astma"]),
    ]
