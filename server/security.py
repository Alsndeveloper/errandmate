import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from server.config import SECRET_KEY, TOKEN_EXPIRY_HOURS
from server.database import get_db

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """PBKDF2-HMAC-SHA256 password hashing with random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verifies against PBKDF2 or legacy SHA-256 with constant-time equality."""
    if not stored_hash or not plain_password:
        return False
    if stored_hash.startswith("pbkdf2_sha256$"):
        parts = stored_hash.split("$")
        if len(parts) != 4:
            return False
        try:
            iterations = int(parts[1])
            salt = parts[2]
            expected_hex = parts[3]
            derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
            return hmac.compare_digest(derived.hex(), expected_hex)
        except Exception:
            return False
    else:
        legacy_hex = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hex, stored_hash)


def mask_id_number(id_number: str) -> str:
    """Keep only the last 4 characters of an ID number, e.g. 'P98765432' -> '*****5432'.

    The full number is never stored, so a database leak can't expose it.
    """
    cleaned = id_number.strip()
    if len(cleaned) <= 4:
        return "*" * len(cleaned)
    return "*" * (len(cleaned) - 4) + cleaned[-4:]


def create_access_token(data: Dict[str, Any], expires_hours: int = TOKEN_EXPIRY_HOURS) -> str:
    """
    Generates a secure cryptographically signed token (HMAC-SHA256).
    Header.Payload.Signature
    """
    payload = data.copy()
    payload["exp"] = int(time.time()) + (expires_hours * 3600)
    payload["iat"] = int(time.time())

    header_bytes = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=")
    payload_bytes = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")

    message = header_bytes + b"." + payload_bytes
    signature = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
    sig_bytes = base64.urlsafe_b64encode(signature).rstrip(b"=")

    return (message + b"." + sig_bytes).decode("utf-8")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies token signature and expiration, returning decoded claims."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts[0], parts[1], parts[2]

        message = (header_b64 + "." + payload_b64).encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode("utf-8")
        payload = json.loads(payload_json)

        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Dict[str, Any]:
    """Dependency that authenticates the user from the Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, full_name, email, phone, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done, joined_date FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists.",
            )
        return dict(user)


def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Optional[Dict[str, Any]]:
    """Optional authentication for endpoints that can be browsed publicly or customized for users."""
    if not credentials or not credentials.credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, full_name, email, phone, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done, joined_date FROM users WHERE id = ?",
            (payload["sub"],)
        ).fetchone()
        return dict(user) if user else None
