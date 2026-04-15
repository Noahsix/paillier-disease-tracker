from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from .crypto import decrypt, encrypt, generate_keypair, homomorphic_add_many, homomorphic_mul_const


@dataclass(frozen=True)
class OperationTiming:
    operation: str
    iterations: int
    total_seconds: float
    average_ms: float


@dataclass(frozen=True)
class KeySizeBenchmarkResult:
    key_size: int
    keygen_seconds: float
    encrypt_timing: OperationTiming
    decrypt_timing: OperationTiming
    homomorphic_add_timing: OperationTiming
    homomorphic_mul_timing: OperationTiming


def _build_timing(operation: str, iterations: int, total_seconds: float) -> OperationTiming:
    average_ms = 0.0
    if iterations > 0:
        average_ms = (total_seconds / iterations) * 1000.0

    return OperationTiming(
        operation=operation,
        iterations=iterations,
        total_seconds=total_seconds,
        average_ms=average_ms,
    )


def run_crypto_benchmark_for_key_size(
    key_size: int,
    encrypt_iterations: int = 200,
    decrypt_iterations: int = 200,
    homomorphic_iterations: int = 100,
    homomorphic_batch_size: int = 64,
) -> KeySizeBenchmarkResult:
    if key_size < 128:
        raise ValueError("key_size must be at least 128")
    if encrypt_iterations <= 0:
        raise ValueError("encrypt_iterations must be positive")
    if decrypt_iterations <= 0:
        raise ValueError("decrypt_iterations must be positive")
    if homomorphic_iterations <= 0:
        raise ValueError("homomorphic_iterations must be positive")
    if homomorphic_batch_size <= 0:
        raise ValueError("homomorphic_batch_size must be positive")

    keygen_start = perf_counter()
    public_key, private_key = generate_keypair(key_size)
    keygen_seconds = perf_counter() - keygen_start

    plaintexts = [index % 2 for index in range(encrypt_iterations)]
    encrypt_start = perf_counter()
    encrypted_values = [encrypt(public_key, value) for value in plaintexts]
    encrypt_seconds = perf_counter() - encrypt_start

    decrypt_samples = encrypted_values[:decrypt_iterations]
    if len(decrypt_samples) < decrypt_iterations:
        additional = [encrypt(public_key, index % 2) for index in range(decrypt_iterations - len(decrypt_samples))]
        decrypt_samples.extend(additional)

    decrypt_start = perf_counter()
    for ciphertext in decrypt_samples:
        decrypt(public_key, private_key, ciphertext)
    decrypt_seconds = perf_counter() - decrypt_start

    batch_plaintexts = [index % 2 for index in range(homomorphic_batch_size)]
    batch_ciphertexts = [encrypt(public_key, value) for value in batch_plaintexts]

    homomorphic_add_start = perf_counter()
    for _ in range(homomorphic_iterations):
        homomorphic_add_many(public_key, batch_ciphertexts)
    homomorphic_add_seconds = perf_counter() - homomorphic_add_start

    base_cipher = homomorphic_add_many(public_key, batch_ciphertexts)
    homomorphic_mul_start = perf_counter()
    for _ in range(homomorphic_iterations):
        homomorphic_mul_const(public_key, base_cipher, 3)
    homomorphic_mul_seconds = perf_counter() - homomorphic_mul_start

    return KeySizeBenchmarkResult(
        key_size=key_size,
        keygen_seconds=keygen_seconds,
        encrypt_timing=_build_timing("encrypt", encrypt_iterations, encrypt_seconds),
        decrypt_timing=_build_timing("decrypt", decrypt_iterations, decrypt_seconds),
        homomorphic_add_timing=_build_timing(
            "homomorphic_add_many",
            homomorphic_iterations,
            homomorphic_add_seconds,
        ),
        homomorphic_mul_timing=_build_timing(
            "homomorphic_mul_const",
            homomorphic_iterations,
            homomorphic_mul_seconds,
        ),
    )


def run_crypto_benchmark(
    key_sizes: list[int],
    encrypt_iterations: int = 200,
    decrypt_iterations: int = 200,
    homomorphic_iterations: int = 100,
    homomorphic_batch_size: int = 64,
) -> list[KeySizeBenchmarkResult]:
    if not key_sizes:
        raise ValueError("key_sizes cannot be empty")

    return [
        run_crypto_benchmark_for_key_size(
            key_size=key_size,
            encrypt_iterations=encrypt_iterations,
            decrypt_iterations=decrypt_iterations,
            homomorphic_iterations=homomorphic_iterations,
            homomorphic_batch_size=homomorphic_batch_size,
        )
        for key_size in key_sizes
    ]
