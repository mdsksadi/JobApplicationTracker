"""DEVELOPER ONLY: create the Ed25519 keypair used by the license system.

Run once from the repository root:
    python tools/generate_keys.py

The private key is written to keys/private_key.pem (gitignored - back it up
somewhere safe!). The public key is written to
src/job_application_tracker/assets/public_key.pem and is shipped with the app.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PATH = ROOT / "keys" / "private_key.pem"
PUBLIC_PATH = ROOT / "src" / "job_application_tracker" / "assets" / "public_key.pem"


def main() -> None:
    if PRIVATE_PATH.exists():
        answer = input(f"Private key already exists at {PRIVATE_PATH}. Overwrite? [y/N] ")
        if answer.strip().lower() != "y":
            print("Aborted. Existing keys were left untouched.")
            return

    private_key = Ed25519PrivateKey.generate()
    PRIVATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_PATH.parent.mkdir(parents=True, exist_ok=True)

    PRIVATE_PATH.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    PUBLIC_PATH.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    print(f"Private key: {PRIVATE_PATH}  (KEEP THIS SECRET, DO NOT COMMIT)")
    print(f"Public key:  {PUBLIC_PATH}  (shipped with the package)")


if __name__ == "__main__":
    main()
