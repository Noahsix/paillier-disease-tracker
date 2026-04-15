import pytest

from paillier_disease_tracker.benchmarking import run_crypto_benchmark, run_crypto_benchmark_for_key_size


def test_run_crypto_benchmark_for_key_size_returns_expected_shape() -> None:
    result = run_crypto_benchmark_for_key_size(
        key_size=128,
        encrypt_iterations=6,
        decrypt_iterations=6,
        homomorphic_iterations=4,
        homomorphic_batch_size=4,
    )

    assert result.key_size == 128
    assert result.keygen_seconds > 0
    assert result.encrypt_timing.iterations == 6
    assert result.decrypt_timing.iterations == 6
    assert result.homomorphic_add_timing.iterations == 4
    assert result.homomorphic_mul_timing.iterations == 4


def test_run_crypto_benchmark_rejects_empty_key_sizes() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        run_crypto_benchmark([])
