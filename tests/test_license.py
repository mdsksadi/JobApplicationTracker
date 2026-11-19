import base64
import json
from datetime import date, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from job_application_tracker import license as license_module


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _make_code(key, name="Sadi", expires=""):
    payload = {"app": "job-application-tracker", "name": name, "issued": date.today().isoformat()}
    if expires:
        payload["expires"] = expires
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return f"JAT1.{_b64(raw)}.{_b64(key.sign(raw))}"


@pytest.fixture
def keypair(tmp_path, monkeypatch):
    key = Ed25519PrivateKey.generate()
    public = tmp_path / "public_key.pem"
    public.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    monkeypatch.setattr(license_module, "PUBLIC_KEY_PATH", public)
    return key


def test_valid_code(keypair):
    valid, name = license_module.verify_code(_make_code(keypair, "Sadi"))
    assert valid is True
    assert name == "Sadi"


def test_tampered_code_is_rejected(keypair):
    code = _make_code(keypair)
    parts = code.split(".")
    bad_payload = json.dumps({"app": "job-application-tracker", "name": "Hacker"}).encode()
    tampered = f"{parts[0]}.{_b64(bad_payload)}.{parts[2]}"
    valid, message = license_module.verify_code(tampered)
    assert valid is False
    assert "Invalid" in message


def test_malformed_code(keypair):
    valid, message = license_module.verify_code("not-a-code")
    assert valid is False
    assert "format" in message.lower()


def test_expired_code(keypair):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    valid, message = license_module.verify_code(_make_code(keypair, expires=yesterday))
    assert valid is False
    assert "expired" in message.lower()
