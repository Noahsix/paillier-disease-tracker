from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from secrets import randbelow, randbits
from typing import Iterable


@dataclass(frozen=True)
class PublicKey:
    n: int
    g: int
    n_sq: int


@dataclass(frozen=True)
class PrivateKey:
    lambda_: int
    mu: int


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


def _is_probable_prime(candidate: int, rounds: int = 20) -> bool:
    if candidate in (2, 3):
        return True
    if candidate < 2 or candidate % 2 == 0:
        return False

    power_of_two = 0
    remainder = candidate - 1
    while remainder % 2 == 0:
        power_of_two += 1
        remainder //= 2

    for _ in range(rounds):
        witness = randbelow(candidate - 3) + 2
        value = pow(witness, remainder, candidate)

        if value in (1, candidate - 1):
            continue

        for _ in range(power_of_two - 1):
            value = pow(value, 2, candidate)
            if value == candidate - 1:
                break
        else:
            return False

    return True


def _generate_prime(bit_length: int) -> int:
    while True:
        candidate = randbits(bit_length) | (1 << (bit_length - 1)) | 1
        if _is_probable_prime(candidate):
            return candidate


def _mod_inverse(value: int, modulus: int) -> int:
    try:
        return pow(value, -1, modulus)
    except ValueError as error:
        raise ValueError("Inverse does not exist for provided value and modulus") from error


def generate_keypair(bit_length: int = 512) -> tuple[PublicKey, PrivateKey]:
    if bit_length < 128:
        raise ValueError("bit_length must be at least 128 bits")

    half_bits = bit_length // 2

    while True:
        p = _generate_prime(half_bits)
        q = _generate_prime(half_bits)
        if p == q:
            continue

        n = p * q
        n_sq = n * n
        g = n + 1

        lambda_value = _lcm(p - 1, q - 1)
        l_value = (pow(g, lambda_value, n_sq) - 1) // n

        if gcd(l_value, n) != 1:
            continue

        mu = _mod_inverse(l_value, n)
        return PublicKey(n=n, g=g, n_sq=n_sq), PrivateKey(lambda_=lambda_value, mu=mu)


def encrypt(public_key: PublicKey, value: int, r: int | None = None) -> int:
    if not 0 <= value < public_key.n:
        raise ValueError("value must be in range [0, n)")

    if r is None:
        while True:
            candidate = randbelow(public_key.n - 1) + 1
            if gcd(candidate, public_key.n) == 1:
                r = candidate
                break
    elif not 1 <= r < public_key.n or gcd(r, public_key.n) != 1:
        raise ValueError("r must satisfy 1 <= r < n and gcd(r, n) = 1")

    gm = pow(public_key.g, value, public_key.n_sq)
    rn = pow(r, public_key.n, public_key.n_sq)
    return (gm * rn) % public_key.n_sq


def encrypt_zero(public_key: PublicKey) -> int:
    return encrypt(public_key, 0)


def decrypt(public_key: PublicKey, private_key: PrivateKey, ciphertext: int) -> int:
    if not 0 <= ciphertext < public_key.n_sq:
        raise ValueError("ciphertext must be in range [0, n^2)")

    x_value = pow(ciphertext, private_key.lambda_, public_key.n_sq)
    l_value = (x_value - 1) // public_key.n
    return (l_value * private_key.mu) % public_key.n


def homomorphic_add(public_key: PublicKey, left_ciphertext: int, right_ciphertext: int) -> int:
    return (left_ciphertext * right_ciphertext) % public_key.n_sq


def homomorphic_add_many(public_key: PublicKey, ciphertexts: Iterable[int]) -> int:
    result = 1
    for ciphertext in ciphertexts:
        result = (result * ciphertext) % public_key.n_sq
    return result


def homomorphic_mul_const(public_key: PublicKey, ciphertext: int, constant: int) -> int:
    if constant < 0:
        raise ValueError("constant must be non-negative")
    return pow(ciphertext, constant, public_key.n_sq)
