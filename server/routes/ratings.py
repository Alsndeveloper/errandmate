import sqlite3
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from server.database import get_db
from server.schemas import RatingCreate, RatingResponse
from server.security import get_current_user

router = APIRouter(prefix="/api/ratings", tags=["Ratings & Reviews"])


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def create_rating(rating_in: RatingCreate, current_user: dict = Depends(get_current_user)):
    """Poster submits a rating (1-5) and feedback for the runner of a completed task."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (rating_in.task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["poster_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the task creator can rate the runner.")
        if not task["runner_id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No runner assigned to this task.")
        if task["status"] != "completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be completed before rating.")

        try:
            cursor = conn.execute(
                """INSERT INTO ratings (task_id, reviewer_id, runner_id, rating, review)
                   VALUES (?, ?, ?, ?, ?)""",
                (task["id"], current_user["id"], task["runner_id"], rating_in.rating, rating_in.review),
            )
            rating_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already rated the runner for this task.",
            )

        row = conn.execute(
            """SELECT r.*,
                      u.full_name as reviewer_name,
                      rn.full_name as runner_name,
                      t.title as task_title
               FROM ratings r
               JOIN users u ON r.reviewer_id = u.id
               JOIN users rn ON r.runner_id = rn.id
               JOIN tasks t ON r.task_id = t.id
               WHERE r.id = ?""",
            (rating_id,),
        ).fetchone()

        return dict(row)


@router.get("/runner/{runner_id}", response_model=List[RatingResponse])
def get_runner_ratings(runner_id: int):
    """Retrieve all ratings and reviews received by a runner."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT r.*,
                      u.full_name as reviewer_name,
                      rn.full_name as runner_name,
                      t.title as task_title
               FROM ratings r
               JOIN users u ON r.reviewer_id = u.id
               JOIN users rn ON r.runner_id = rn.id
               JOIN tasks t ON r.task_id = t.id
               WHERE r.runner_id = ?
               ORDER BY r.created_on DESC""",
            (runner_id,),
        ).fetchall()
        return [dict(row) for row in rows]
