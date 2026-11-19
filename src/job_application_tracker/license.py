"""Offline Ed25519 license verification for the 'Sadi App' watermark."""

from __future__ import annotations

import base64
import json
from datetime import date
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key

PUBLIC_KEY_PATH = Path(__file__).resolve().parent / "assets" / "public_key.pem"
PREFIX = "JAT1"


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def verify_code(code: str) -> tuple[bool, str]:
    """Return (is_valid, licensee_name_or_error_message)."""
    code = (code or "").strip()
    parts = code.split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        return False, "Unrecognized code format. Expected JAT1.<...>.<...>"

    try:
        payload_bytes = _b64decode(parts[1])
        signature = _b64decode(parts[2])
        public_key = load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())
        public_key.verify(signature, payload_bytes)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except InvalidSignature:
        return False, "Invalid license code. Please check and try again."
    except FileNotFoundError:
        return False, "Public key missing from this installation."
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        return False, f"Could not read this code: {exc}"

    expires = payload.get("expires")
    if expires:
        try:
            if date.fromisoformat(str(expires)) < date.today():
                return False, "This license code has expired."
        except ValueError:
            return False, "This license code has an invalid expiry date."

    if payload.get("app") not in (None, "job-application-tracker"):
        return False, "This license code is for a different application."

    return True, str(payload.get("name", "Licensed user"))
