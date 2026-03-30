from paillier_disease_tracker.client import ClientApplication
from paillier_disease_tracker.crypto import generate_keypair


def test_server_side_encrypted_count_matches_plain_count(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19", "astma"])

    app.add_patient("p1", {"grypa": 1, "covid19": 0, "astma": 1})
    app.add_patient("p2", {"grypa": 1, "covid19": 1, "astma": 0})
    app.add_patient("p3", {"grypa": 0, "covid19": 1, "astma": 0})

    encrypted_count = app.server.encrypted_count_for_disease("grypa")
    decrypted_count = app.decrypt_value(encrypted_count)
    plain_count = app.repository.get_plain_count_for_disease("grypa")

    assert decrypted_count == 2
    assert plain_count == 2


def test_count_result_contains_validation_data(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19"])

    app.add_patient("a1", {"grypa": 1, "covid19": 1})
    app.add_patient("a2", {"grypa": 0, "covid19": 1})

    result = app.count_disease("covid19")

    assert result.decrypted_result == 2
    assert result.plain_reference == 2
