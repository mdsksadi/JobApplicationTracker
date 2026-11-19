"""DEVELOPER ONLY: issue a signed license code that removes the watermark.

Usage:
    python tools/issue_license.py "Customer Name" [--expires 2027-12-31]

Requires keys/private_key.pem created by generate_keys.py.
"""

from __future__ import annotations

import argparse
import base64
import json
from datetime import date
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATH = ROOT / "keys" / "private_key.pem"
PREFIX = "JAT1"


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def issue(name: str, expires: str = "") -> str:
    if not PRIVATE_PATH.exists():
        raise SystemExit(
            f"Missing private key at {PRIVATE_PATH}. Run tools/generate_keys.py first."
        )
    payload = {
        "app": "job-application-tracker",
        "name": name.strip() or "Licensed user",
        "issued": date.today().isoformat(),
    }
    if expires:
        payload["expires"] = expires
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    key = serialization.load_pem_private_key(PRIVATE_PATH.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):  # pragma: no cover
        raise SystemExit("Private key is not an Ed25519 key.")
    signature = key.sign(payload_bytes)
    return f"{PREFIX}.{_b64encode(payload_bytes)}.{_b64encode(signature)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue a JobApplicationTracker license code.")
    parser.add_argument("name", help="Name of the person receiving the license")
    parser.add_argument("--expires", default="", help="Optional expiry date, YYYY-MM-DD")
    args = parser.parse_args()

    if args.expires:
        try:
            date.fromisoformat(args.expires)
        except ValueError as exc:
            raise SystemExit("--expires must be in YYYY-MM-DD format") from exc

    print(issue(args.name, args.expires))


if __name__ == "__main__":
    main()
