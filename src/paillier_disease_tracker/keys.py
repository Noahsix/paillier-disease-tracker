from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .crypto import PrivateKey, PublicKey

PathLike = Union[str, Path]


def save_keypair(path: PathLike, public_key: PublicKey, private_key: PrivateKey) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "public_key": {
            "n": str(public_key.n),
            "g": str(public_key.g),
        },
        "private_key": {
            "lambda": str(private_key.lambda_),
            "mu": str(private_key.mu),
        },
    }
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_keypair(path: PathLike) -> tuple[PublicKey, PrivateKey]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Key file does not exist: {source}")

    payload = json.loads(source.read_text(encoding="utf-8"))

    n = int(payload["public_key"]["n"])
    g = int(payload["public_key"]["g"])
    lambda_value = int(payload["private_key"]["lambda"])
    mu = int(payload["private_key"]["mu"])

    public_key = PublicKey(n=n, g=g, n_sq=n * n)
    private_key = PrivateKey(lambda_=lambda_value, mu=mu)
    return public_key, private_key
