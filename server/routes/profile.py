from fastapi import APIRouter, HTTPException, status, Depends
from server.database import get_db
from server.schemas import UserProfileUpdate, PasswordChange, UserResponse
from server.security import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/users", tags=["User Profile"])


@router.put("/profile", response_model=UserResponse)
def update_profile(profile_in: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Update profile details (name, phone, role) for the authenticated user."""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET full_name = ?, phone = ?, role = ? WHERE id = ?",
            (profile_in.full_name.strip(), profile_in.phone.strip(), profile_in.role, current_user["id"]),
        )
        updated = conn.execute(
            "SELECT id, full_name, email, phone, role, tasks_done, joined_date FROM users WHERE id = ?",
            (current_user["id"],),
        ).fetchone()
        return dict(updated)


@router.post("/change-password")
def change_password(pw_in: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Securely change account password after validating the existing password."""
    with get_db() as conn:
        db_user = conn.execute("SELECT password FROM users WHERE id = ?", (current_user["id"],)).fetchone()
        if not db_user or not verify_password(pw_in.old_password, db_user["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        new_hash = hash_password(pw_in.new_password)
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, current_user["id"]))

    return {"message": "Password changed successfully."}


@router.get("/{user_id}", response_model=dict)
def get_public_user_profile(user_id: int):
    """Retrieve public profile statistics and rating for a user."""
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, full_name, role, tasks_done, joined_date FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        avg_rating = conn.execute("SELECT AVG(rating) FROM ratings WHERE runner_id = ?", (user_id,)).fetchone()[0]
        posted_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id = ?", (user_id,)).fetchone()[0]

        return {
            **dict(user),
            "average_rating": round(avg_rating, 2) if avg_rating is not None else None,
            "tasks_posted": posted_count,
        }
