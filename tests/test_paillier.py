import pytest

from paillier_disease_tracker.crypto import (
    decrypt,
    encrypt,
    generate_keypair,
    homomorphic_add,
    homomorphic_add_many,
    homomorphic_mul_const,
)


def test_encrypt_decrypt_roundtrip() -> None:
    public_key, private_key = generate_keypair(128)

    for message in (0, 1, 7, 42):
        ciphertext = encrypt(public_key, message)
        assert decrypt(public_key, private_key, ciphertext) == message


def test_homomorphic_addition() -> None:
    public_key, private_key = generate_keypair(128)

    left = encrypt(public_key, 3)
    right = encrypt(public_key, 5)
    encrypted_sum = homomorphic_add(public_key, left, right)

    assert decrypt(public_key, private_key, encrypted_sum) == 8


def test_homomorphic_add_many_and_mul_const() -> None:
    public_key, private_key = generate_keypair(128)

    ciphertexts = [encrypt(public_key, value) for value in (1, 0, 1, 1)]
    encrypted_count = homomorphic_add_many(public_key, ciphertexts)

    assert decrypt(public_key, private_key, encrypted_count) == 3

    encrypted_scaled = homomorphic_mul_const(public_key, encrypted_count, 4)
    assert decrypt(public_key, private_key, encrypted_scaled) == 12


def test_homomorphic_add_many_empty_collection_returns_zero() -> None:
    public_key, private_key = generate_keypair(128)

    encrypted_sum = homomorphic_add_many(public_key, [])

    assert decrypt(public_key, private_key, encrypted_sum) == 0


def test_homomorphic_mul_const_with_zero_returns_zero() -> None:
    public_key, private_key = generate_keypair(128)

    ciphertext = encrypt(public_key, 17)
    encrypted_zero = homomorphic_mul_const(public_key, ciphertext, 0)

    assert decrypt(public_key, private_key, encrypted_zero) == 0


def test_homomorphic_mul_const_rejects_negative_constant() -> None:
    public_key, _ = generate_keypair(128)
    ciphertext = encrypt(public_key, 1)

    with pytest.raises(ValueError, match="non-negative"):
        homomorphic_mul_const(public_key, ciphertext, -1)


def test_encrypt_rejects_invalid_plaintext_range() -> None:
    public_key, _ = generate_keypair(128)

    with pytest.raises(ValueError, match="range"):
        encrypt(public_key, -1)

    with pytest.raises(ValueError, match="range"):
        encrypt(public_key, public_key.n)


def test_encrypt_rejects_invalid_randomizer() -> None:
    public_key, _ = generate_keypair(128)

    with pytest.raises(ValueError, match="gcd"):
        encrypt(public_key, 1, r=0)

    with pytest.raises(ValueError, match="gcd"):
        encrypt(public_key, 1, r=public_key.n)


def test_decrypt_rejects_out_of_range_ciphertext() -> None:
    public_key, private_key = generate_keypair(128)

    with pytest.raises(ValueError, match="range"):
        decrypt(public_key, private_key, -1)

    with pytest.raises(ValueError, match="range"):
        decrypt(public_key, private_key, public_key.n_sq)
