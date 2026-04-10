from __future__ import annotations

import argparse
from pathlib import Path

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


def command_setup(args: argparse.Namespace) -> int:
    public_key, private_key = generate_keypair(args.key_size)
    save_keypair(args.keys_path, public_key, private_key)

    app = ClientApplication(args.db_path, public_key, private_key)
    app.initialize_catalog(list(DEFAULT_DISEASES))

    print("Setup complete")
    print(f"Database path: {args.db_path}")
    print(f"Keys path: {args.keys_path}")
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
