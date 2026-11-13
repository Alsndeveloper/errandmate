import hashlib
import hmac
import secrets


def hash_pw(pw: str, salt: str = None) -> str:
    """
    PBKDF2-HMAC-SHA256 password hashing with salt.
    Format: pbkdf2_sha256$<iterations>$<salt>$<hash>
    """
    if not salt:
        salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def legacy_hash_pw(pw: str) -> str:
    """Legacy SHA-256 hashing for compatibility testing."""
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def verify_pw(pw: str, stored_hash: str) -> bool:
    """
    Verifies passwords against stored hash, supporting both modern PBKDF2
    and legacy plain SHA-256 hashes seamlessly with constant-time comparison.
    """
    if not stored_hash or not pw:
        return False
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) != 4:
            return False
        try:
            iterations = int(parts[1])
            salt = parts[2]
            expected_hex = parts[3]
            derived = hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("utf-8"), iterations)
            return hmac.compare_digest(derived.hex(), expected_hex)
        except Exception:
            return False
    else:
        # Legacy plain SHA-256
        legacy_hash = hashlib.sha256(pw.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash)
