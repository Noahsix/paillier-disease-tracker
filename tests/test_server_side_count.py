import pytest

from paillier_disease_tracker.client import ClientApplication
from paillier_disease_tracker.cli import main
from paillier_disease_tracker.crypto import generate_keypair
from paillier_disease_tracker.db.database import connect
from paillier_disease_tracker.keys import load_keypair


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


def test_seed_bulk_data_inserts_requested_number_of_patients(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19", "astma"])

    inserted = app.seed_bulk_data(patient_count=250, seed=7, batch_size=40)

    assert inserted == 250
    assert app.repository.total_patients() == 250

    result = app.count_and_sum_disease("grypa")
    assert result.row_count == 250


def test_seed_bulk_data_rejects_invalid_arguments(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa"])

    with pytest.raises(ValueError, match="negative"):
        app.seed_bulk_data(patient_count=-1)

    with pytest.raises(ValueError, match="positive"):
        app.seed_bulk_data(patient_count=1, batch_size=0)


def test_validate_all_disease_sums_returns_successful_report(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19"])

    app.add_patient("v1", {"grypa": 1, "covid19": 0})
    app.add_patient("v2", {"grypa": 0, "covid19": 1})

    report = app.validate_all_disease_sums()

    assert report.total_diseases == 2
    assert report.passed_diseases == 2
    assert report.all_valid is True
    assert all(result.is_valid for result in report.results)


def test_validate_detects_mismatch_after_plain_value_tampering(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    public_key, private_key = generate_keypair(128)

    app = ClientApplication(db_path, public_key, private_key)
    app.initialize_catalog(["grypa", "covid19"])

    app.add_patient("x1", {"grypa": 1, "covid19": 0})
    app.add_patient("x2", {"grypa": 1, "covid19": 1})

    baseline = app.validate_disease_sum("grypa")
    assert baseline.is_valid is True

    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE diagnoses
            SET has_disease = 0
            WHERE patient_id = (SELECT id FROM patients WHERE pseudonym = ?)
              AND disease_id = (SELECT id FROM diseases WHERE name = ?)
            """,
            ("x2", "grypa"),
        )

    tampered = app.validate_disease_sum("grypa")

    assert tampered.is_valid is False
    assert tampered.homomorphic_sum != tampered.plain_sum

    report = app.validate_all_disease_sums()
    assert report.all_valid is False
    assert any(not result.is_valid for result in report.results)


def test_setup_clears_old_ciphertexts_before_key_rotation(tmp_path) -> None:
    db_path = tmp_path / "tracker.db"
    keys_path = tmp_path / "keys.json"

    first_setup_exit = main(
        [
            "--db-path",
            str(db_path),
            "--keys-path",
            str(keys_path),
            "setup",
            "--key-size",
            "128",
        ]
    )
    assert first_setup_exit == 0

    initial_public, initial_private = load_keypair(keys_path)
    initial_app = ClientApplication(db_path, initial_public, initial_private)
    initial_app.add_patient("setup_reset_patient", {"grypa": 1, "covid19": 0})
    assert initial_app.repository.total_patients() == 1

    second_setup_exit = main(
        [
            "--db-path",
            str(db_path),
            "--keys-path",
            str(keys_path),
            "setup",
            "--key-size",
            "128",
        ]
    )
    assert second_setup_exit == 0

    rotated_public, rotated_private = load_keypair(keys_path)
    rotated_app = ClientApplication(db_path, rotated_public, rotated_private)

    assert rotated_app.repository.total_patients() == 0

    report = rotated_app.validate_all_disease_sums()
    assert report.all_valid is True
    assert all(result.homomorphic_sum == 0 for result in report.results)
    assert all(result.plain_sum == 0 for result in report.results)
