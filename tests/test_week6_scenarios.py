from paillier_disease_tracker.benchmarking import run_crypto_benchmark
from paillier_disease_tracker.client import ClientApplication
from paillier_disease_tracker.crypto import generate_keypair
from paillier_disease_tracker.db.database import connect


def _create_app(tmp_path, diseases: list[str]) -> ClientApplication:
    db_path = tmp_path / "week6.db"
    public_key, private_key = generate_keypair(128)
    app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
    app.initialize_catalog(diseases)
    return app


def test_scenario_01_setup_and_catalog_initialization(tmp_path) -> None:
    app = _create_app(tmp_path, ["grypa", "covid19", "astma"])

    assert app.list_diseases() == ["grypa", "covid19", "astma"]
    assert app.repository.total_patients() == 0


def test_scenario_02_manual_insert_and_encrypted_count(tmp_path) -> None:
    app = _create_app(tmp_path, ["grypa", "covid19", "astma"])

    app.add_patient("s2_p1", {"grypa": 1, "covid19": 0, "astma": 1})
    app.add_patient("s2_p2", {"grypa": 1, "covid19": 1, "astma": 0})
    app.add_patient("s2_p3", {"grypa": 0, "covid19": 1, "astma": 0})

    result = app.count_and_sum_disease("grypa")

    assert result.row_count == 3
    assert result.decrypted_count == 2
    assert result.decrypted_sum == 2
    assert result.plain_count_reference == 2
    assert result.plain_sum_reference == 2


def test_scenario_03_demo_seed_and_flow_preview(tmp_path) -> None:
    app = _create_app(tmp_path, ["grypa", "covid19", "cukrzyca", "nadcisnienie", "astma", "alergia"])

    inserted = app.seed_demo_data()
    flow = app.build_count_flow("covid19")

    assert inserted > 0
    assert len(flow.rows) == inserted
    assert flow.decrypted_result == flow.plain_reference


def test_scenario_04_bulk_dataset_and_full_validation(tmp_path) -> None:
    app = _create_app(tmp_path, ["grypa", "covid19", "astma", "alergia"])

    inserted = app.seed_bulk_data(patient_count=1000, seed=24, batch_size=200)
    report = app.validate_all_disease_sums()

    assert inserted == 1000
    assert app.repository.total_patients() == 1000
    assert report.total_diseases == 4
    assert report.passed_diseases == 4
    assert report.all_valid is True


def test_scenario_05_integrity_check_detects_tampering(tmp_path) -> None:
    db_path = tmp_path / "week6_tamper.db"
    public_key, private_key = generate_keypair(128)
    app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
    app.initialize_catalog(["grypa", "covid19"])

    app.add_patient("s5_p1", {"grypa": 1, "covid19": 0})
    app.add_patient("s5_p2", {"grypa": 1, "covid19": 1})

    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE diagnoses
            SET has_disease = 0
            WHERE patient_id = (SELECT id FROM patients WHERE pseudonym = ?)
              AND disease_id = (SELECT id FROM diseases WHERE name = ?)
            """,
            ("s5_p2", "grypa"),
        )

    report = app.validate_all_disease_sums()

    assert report.all_valid is False
    assert any(not result.is_valid for result in report.results)


def test_scenario_06_benchmark_for_multiple_key_sizes() -> None:
    results = run_crypto_benchmark(
        key_sizes=[128, 256],
        encrypt_iterations=8,
        decrypt_iterations=8,
        homomorphic_iterations=5,
        homomorphic_batch_size=8,
    )

    assert len(results) == 2
    assert [result.key_size for result in results] == [128, 256]
    assert all(result.keygen_seconds > 0 for result in results)
    assert all(result.encrypt_timing.average_ms >= 0 for result in results)
    assert all(result.decrypt_timing.average_ms >= 0 for result in results)
