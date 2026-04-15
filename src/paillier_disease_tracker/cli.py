from __future__ import annotations

import argparse
from pathlib import Path

from .benchmarking import run_crypto_benchmark
from .client import ClientApplication
from .config import DEFAULT_DB_PATH, DEFAULT_DISEASES, DEFAULT_KEYS_PATH, DEFAULT_KEY_SIZE
from .crypto import generate_keypair
from .keys import load_keypair, save_keypair


def _parse_diagnoses(raw: str, known_diseases: list[str]) -> dict[str, int]:
    entries = [item.strip() for item in raw.split(",") if item.strip()]
    if not entries:
        raise ValueError("diagnoses string is empty")

    parsed: dict[str, int] = {}
    for entry in entries:
        name, sep, value_text = entry.partition("=")
        if sep != "=":
            raise ValueError(f"Invalid diagnosis pair: {entry}")

        name = name.strip()
        if name not in known_diseases:
            raise ValueError(f"Unknown disease name: {name}")

        if value_text.strip() not in ("0", "1"):
            raise ValueError(f"Value for {name} must be 0 or 1")

        parsed[name] = int(value_text.strip())

    return parsed


def _default_diagnoses(disease_names: list[str], partial: dict[str, int]) -> dict[str, int]:
    return {name: int(partial.get(name, 0)) for name in disease_names}


def _parse_key_sizes(raw: str) -> list[int]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("key-sizes cannot be empty")

    key_sizes = [int(item) for item in values]
    for key_size in key_sizes:
        if key_size < 128:
            raise ValueError("Every key size must be at least 128")

    return key_sizes


def command_setup(args: argparse.Namespace) -> int:
    public_key, private_key = generate_keypair(args.key_size)
    save_keypair(args.keys_path, public_key, private_key)

    app = ClientApplication(args.db_path, public_key, private_key)
    app.initialize_catalog(list(DEFAULT_DISEASES))
    existing_patients = app.repository.total_patients()
    if existing_patients:
        app.repository.clear_patient_data()

    print("Setup complete")
    print(f"Database path: {args.db_path}")
    print(f"Keys path: {args.keys_path}")
    if existing_patients:
        print(f"Existing patient records cleared: {existing_patients}")
    print("Catalog diseases:", ", ".join(app.list_diseases()))
    return 0


def _build_app(db_path: Path, keys_path: Path) -> ClientApplication:
    public_key, private_key = load_keypair(keys_path)
    app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
    app.initialize_catalog(list(DEFAULT_DISEASES))
    return app


def command_add_patient(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    disease_names = app.list_diseases()

    partial_diagnoses = _parse_diagnoses(args.diagnoses, disease_names)
    diagnoses = _default_diagnoses(disease_names, partial_diagnoses)

    patient_id = app.add_patient(args.name, diagnoses)
    print(f"Inserted patient id={patient_id}, pseudonym={args.name}")
    return 0


def command_seed_demo(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    added = app.seed_demo_data()
    print(f"Inserted demo patients: {added}")
    return 0


def command_seed_bulk(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    inserted = app.seed_bulk_data(
        patient_count=args.patients,
        seed=args.seed,
        pseudonym_prefix=args.prefix,
        batch_size=args.batch_size,
    )
    print(f"Inserted bulk patients: {inserted}")
    print(f"Total patients in DB: {app.repository.total_patients()}")
    return 0


def command_count(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    if args.disease not in app.list_diseases():
        raise ValueError(f"Unknown disease: {args.disease}")

    result = app.count_and_sum_disease(args.disease)
    print(f"Disease: {result.disease}")
    print(f"Rows considered by server: {result.row_count}")
    print(f"Encrypted COUNT (server-side): {result.encrypted_count}")
    print(f"Encrypted SUM (server-side): {result.encrypted_sum}")
    print(f"Decrypted COUNT (client-side): {result.decrypted_count}")
    print(f"Decrypted SUM (client-side): {result.decrypted_sum}")
    print(f"Plain COUNT reference from DB: {result.plain_count_reference}")
    print(f"Plain SUM reference from DB: {result.plain_sum_reference}")
    print(
        "Validation status: "
        f"{result.decrypted_count == result.plain_count_reference and result.decrypted_sum == result.plain_sum_reference}"
    )

    if args.show_steps:
        flow = app.build_count_flow(args.disease)
        print("Process visualization: plain -> ciphertext -> homomorphic -> decrypted")
        for row in flow.rows:
            print(f"  {row.pseudonym}: {row.plain_value} -> {row.ciphertext}")
        print(f"  Homomorphic aggregate ciphertext: {flow.encrypted_homomorphic_result}")
        print(f"  Decrypted final result: {flow.decrypted_result}")
        print(f"  Plain reference: {flow.plain_reference}")

    return 0


def command_list_diseases(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    mapping = app.repository.disease_mapping()
    print("Disease mapping:")
    for name, numeric_code in mapping.items():
        print(f"  {numeric_code}: {name}")
    return 0


def command_show_encrypted(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)
    rows = app.repository.get_encrypted_rows_for_disease(args.disease)
    print(f"Encrypted rows for disease={args.disease}")
    for pseudonym, ciphertext in rows:
        print(f"  {pseudonym}: {ciphertext}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    app = _build_app(args.db_path, args.keys_path)

    if args.disease:
        result = app.validate_disease_sum(args.disease)
        print(f"Disease: {result.disease}")
        print(f"Homomorphic SUM: {result.homomorphic_sum}")
        print(f"Plain SUM reference: {result.plain_sum}")
        print(f"Homomorphic COUNT: {result.homomorphic_count}")
        print(f"Plain COUNT reference: {result.plain_count}")
        print(f"Validation status: {result.is_valid}")
        return 0 if result.is_valid else 1

    report = app.validate_all_disease_sums()
    print("Validation report (all diseases):")
    for result in report.results:
        print(
            " | ".join(
                [
                    f"disease={result.disease}",
                    f"homomorphic_sum={result.homomorphic_sum}",
                    f"plain_sum={result.plain_sum}",
                    f"status={result.is_valid}",
                ]
            )
        )

    print(
        f"Summary: passed={report.passed_diseases}/{report.total_diseases}, all_valid={report.all_valid}"
    )
    return 0 if report.all_valid else 1


def command_benchmark_crypto(args: argparse.Namespace) -> int:
    key_sizes = _parse_key_sizes(args.key_sizes)

    results = run_crypto_benchmark(
        key_sizes=key_sizes,
        encrypt_iterations=args.encrypt_iterations,
        decrypt_iterations=args.decrypt_iterations,
        homomorphic_iterations=args.homomorphic_iterations,
        homomorphic_batch_size=args.homomorphic_batch_size,
    )

    for result in results:
        print(f"Key size: {result.key_size} bits")
        print(f"  Key generation: {result.keygen_seconds:.6f}s")
        print(
            f"  Encrypt avg ({result.encrypt_timing.iterations} runs): "
            f"{result.encrypt_timing.average_ms:.3f}ms"
        )
        print(
            f"  Decrypt avg ({result.decrypt_timing.iterations} runs): "
            f"{result.decrypt_timing.average_ms:.3f}ms"
        )
        print(
            f"  Homomorphic add_many avg ({result.homomorphic_add_timing.iterations} runs): "
            f"{result.homomorphic_add_timing.average_ms:.3f}ms"
        )
        print(
            f"  Homomorphic mul_const avg ({result.homomorphic_mul_timing.iterations} runs): "
            f"{result.homomorphic_mul_timing.average_ms:.3f}ms"
        )

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paillier Disease Tracker CLI")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--keys-path", type=Path, default=DEFAULT_KEYS_PATH)

    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Generate keys and initialize DB")
    setup_parser.add_argument("--key-size", type=int, default=DEFAULT_KEY_SIZE)
    setup_parser.set_defaults(handler=command_setup)

    add_parser = subparsers.add_parser("add-patient", help="Add one patient record")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument(
        "--diagnoses",
        required=True,
        help="Comma-separated disease=0|1 pairs, e.g. grypa=1,covid19=0",
    )
    add_parser.set_defaults(handler=command_add_patient)

    seed_parser = subparsers.add_parser("seed-demo", help="Insert deterministic demo data")
    seed_parser.set_defaults(handler=command_seed_demo)

    bulk_parser = subparsers.add_parser(
        "seed-bulk",
        help="Insert large synthetic dataset for performance testing",
    )
    bulk_parser.add_argument("--patients", type=int, default=5000)
    bulk_parser.add_argument("--seed", type=int, default=42)
    bulk_parser.add_argument("--prefix", default="bulk_patient")
    bulk_parser.add_argument("--batch-size", type=int, default=1000)
    bulk_parser.set_defaults(handler=command_seed_bulk)

    count_parser = subparsers.add_parser(
        "count",
        help="Compute encrypted COUNT/SUM on server and decrypt result on client",
    )
    count_parser.add_argument("--disease", required=True)
    count_parser.add_argument("--show-steps", action="store_true")
    count_parser.set_defaults(handler=command_count)

    list_parser = subparsers.add_parser("list-diseases", help="Show disease mapping")
    list_parser.set_defaults(handler=command_list_diseases)

    show_parser = subparsers.add_parser(
        "show-encrypted",
        help="Show per-patient ciphertexts for one disease",
    )
    show_parser.add_argument("--disease", required=True)
    show_parser.set_defaults(handler=command_show_encrypted)

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate homomorphic results against plain SQL reference",
    )
    validate_parser.add_argument("--disease", required=False)
    validate_parser.set_defaults(handler=command_validate)

    benchmark_parser = subparsers.add_parser(
        "benchmark-crypto",
        help="Measure encryption/decryption/homomorphic operation timings for key sizes",
    )
    benchmark_parser.add_argument("--key-sizes", default="256,512,768")
    benchmark_parser.add_argument("--encrypt-iterations", type=int, default=200)
    benchmark_parser.add_argument("--decrypt-iterations", type=int, default=200)
    benchmark_parser.add_argument("--homomorphic-iterations", type=int, default=100)
    benchmark_parser.add_argument("--homomorphic-batch-size", type=int, default=64)
    benchmark_parser.set_defaults(handler=command_benchmark_crypto)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
