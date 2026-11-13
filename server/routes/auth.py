import sqlite3
from fastapi import APIRouter, HTTPException, status, Depends
from server.database import get_db
from server.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from server.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """Registers a new user (ID details optional, self-declared) and returns an access token."""
    clean_email = user_data.email.strip().lower()

    with get_db() as conn:
        # Check if email is already registered
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (clean_email,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        password_hash = hash_password(user_data.password)

        cursor = conn.execute(
            """INSERT INTO users (full_name, email, phone, password, role, id_type, id_number, residential_address, postcode, is_id_verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                user_data.full_name.strip(),
                clean_email,
                user_data.phone.strip(),
                password_hash,
                user_data.role,
                # ID details are self-declared only. No document check happens, so new
                # accounts start unverified (is_id_verified = 0) and no ID is invented.
                user_data.id_type if user_data.id_number else None,
                user_data.id_number.strip() if user_data.id_number else None,
                user_data.residential_address.strip() if user_data.residential_address else None,
                user_data.postcode.strip().upper() if user_data.postcode else None,
            ),
        )
        new_user_id = cursor.lastrowid

        user = conn.execute(
            "SELECT id, username, full_name, email, phone, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done, joined_date FROM users WHERE id = ?",
            (new_user_id,)
        ).fetchone()

    user_dict = dict(user)
    token = create_access_token({"sub": user_dict["id"], "email": user_dict["email"]})

    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user_dict,
    }


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    """
    Authenticates a user with email or username (e.g. 'admin') and password,
    returning an access token.
    """
    clean_identifier = login_data.email.strip().lower()

    with get_db() as conn:
        # Support login via email OR username (e.g. username 'admin')
        user = conn.execute(
            "SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?",
            (clean_identifier, clean_identifier)
        ).fetchone()

        if not user or not verify_password(login_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password.",
            )

        # Opportunistic security upgrade: upgrade legacy SHA-256 to PBKDF2 if needed
        if not user["password"].startswith("pbkdf2_sha256$"):
            new_hash = hash_password(login_data.password)
            conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, user["id"]))

        user_info = conn.execute(
            "SELECT id, username, full_name, email, phone, role, id_type, id_number, residential_address, postcode, is_id_verified, tasks_done, joined_date FROM users WHERE id = ?",
            (user["id"],)
        ).fetchone()

    user_dict = dict(user_info)
    token = create_access_token({"sub": user_dict["id"], "email": user_dict["email"]})

    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user_dict,
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user
