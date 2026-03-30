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
