import hashlib
from server.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing_and_verification():
    pw = "SuperSecurePassword123!"
    hashed = hash_password(pw)
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_legacy_sha256_backward_compatibility():
    pw = "OldLegacyPass123"
    legacy_hash = hashlib.sha256(pw.encode()).hexdigest()
    assert verify_password(pw, legacy_hash) is True
    assert verify_password("Incorrect", legacy_hash) is False


def test_jwt_token_creation_and_decoding():
    payload = {"sub": 42, "email": "test@example.com"}
    token = create_access_token(payload, expires_hours=1)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == 42
    assert decoded["email"] == "test@example.com"


def test_tampered_token_rejection():
    token = create_access_token({"sub": 1}, expires_hours=1)
    tampered = token[:-4] + "abcd"
    assert decode_access_token(tampered) is None
