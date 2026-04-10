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

    count_sum = app.count_and_sum_disease("grypa")

    assert count_sum.decrypted_count == 2
    assert count_sum.decrypted_sum == 2
    assert count_sum.plain_count_reference == 2
    assert count_sum.plain_sum_reference == 2
    assert count_sum.row_count == 3


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


def test_server_side_count_sum_empty_dataset_returns_zero(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19"])

    result = app.count_and_sum_disease("grypa")

    assert result.row_count == 0
    assert result.decrypted_count == 0
    assert result.decrypted_sum == 0
    assert result.plain_count_reference == 0
    assert result.plain_sum_reference == 0


def test_flow_visualization_contains_plain_and_ciphertext_rows(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19"])

    app.add_patient("u1", {"grypa": 1, "covid19": 0})
    app.add_patient("u2", {"grypa": 1, "covid19": 1})

    flow = app.build_count_flow("covid19")

    assert len(flow.rows) == 2
    assert [row.pseudonym for row in flow.rows] == ["u1", "u2"]
    assert [row.plain_value for row in flow.rows] == [0, 1]
    assert flow.decrypted_result == 1
    assert flow.plain_reference == 1
