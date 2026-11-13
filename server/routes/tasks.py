import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from server.database import get_db
from server.schemas import TaskCreate, TaskUpdate, TaskCancel, TaskResponse
from server.security import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def get_task_query_base() -> str:
    return """
        SELECT t.*,
               u.full_name as poster_name, u.phone as poster_phone,
               r.full_name as runner_name, r.phone as runner_phone,
               (SELECT AVG(rating) FROM ratings WHERE runner_id = t.runner_id) as runner_rating
        FROM tasks t
        JOIN users u ON t.poster_id = u.id
        LEFT JOIN users r ON t.runner_id = r.id
    """


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status (e.g. open, in_progress, completed)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term in title, description, or location"),
    sort: Optional[str] = Query("newest", description="Sort order: newest, price_asc, price_desc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Browse tasks with dynamic filtering, search, and sorting."""
    query = get_task_query_base() + " WHERE 1=1"
    params = []

    if status:
        query += " AND t.status = ?"
        params.append(status)

    if category and category.lower() != "all":
        query += " AND t.category = ?"
        params.append(category)

    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query += " AND (LOWER(t.title) LIKE ? OR LOWER(t.description) LIKE ? OR LOWER(t.location) LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if sort == "price_asc":
        query += " ORDER BY t.price ASC"
    elif sort == "price_desc":
        query += " ORDER BY t.price DESC"
    else:
        query += " ORDER BY t.posted_on DESC"

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, current_user: dict = Depends(get_current_user)):
    """Create a new errand/task under the authenticated user."""
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO tasks (title, description, category, location, price, deadline, poster_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'open')""",
            (
                task_in.title.strip(),
                task_in.description.strip() if task_in.description else None,
                task_in.category.strip(),
                task_in.location.strip(),
                task_in.price,
                task_in.deadline.strip() if task_in.deadline else None,
                current_user["id"],
            ),
        )
        task_id = cursor.lastrowid
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.get("/user/summary")
def get_user_tasks(
    tab: str = Query("posted", pattern="^(posted|running|done|cancelled)$"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve tasks relating to the current user by lifecycle tab."""
    user_id = current_user["id"]
    query = get_task_query_base()

    if tab == "posted":
        query += " WHERE t.poster_id = ? ORDER BY t.posted_on DESC"
        params = [user_id]
    elif tab == "running":
        query += " WHERE t.runner_id = ? AND t.status IN ('accepted', 'in_progress', 'awaiting_confirmation') ORDER BY t.posted_on DESC"
        params = [user_id]
    elif tab == "done":
        query += " WHERE (t.poster_id = ? OR t.runner_id = ?) AND t.status = 'completed' ORDER BY t.finished_on DESC"
        params = [user_id, user_id]
    else:  # cancelled
        query += " WHERE (t.poster_id = ? OR t.runner_id = ?) AND t.status = 'cancelled' ORDER BY t.cancelled_on DESC"
        params = [user_id, user_id]

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    """Retrieve full details for a single task."""
    with get_db() as conn:
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        return dict(row)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updates: TaskUpdate, current_user: dict = Depends(get_current_user)):
    """Edit an open task (only allowed for task creator when status is open)."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["poster_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the task poster can edit this task.")
        if task["status"] != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open tasks can be edited.")

        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
            return dict(row)

        fields = []
        values = []
        for key, val in update_dict.items():
            fields.append(f"{key} = ?")
            values.append(val)
        values.append(task_id)

        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/accept", response_model=TaskResponse)
def accept_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Runner accepts an open errand."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["poster_id"] == current_user["id"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot accept your own task.")
        if task["status"] != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This task is no longer open.")

        conn.execute(
            "UPDATE tasks SET runner_id = ?, status = 'accepted', accepted_on = ? WHERE id = ?",
            (current_user["id"], now_iso(), task_id),
        )
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/start", response_model=TaskResponse)
def start_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Runner transitions task to 'in_progress'."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["runner_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned runner can start this task.")
        if task["status"] != "accepted":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be in 'accepted' state to start.")

        conn.execute("UPDATE tasks SET status = 'in_progress', started_on = ? WHERE id = ?", (now_iso(), task_id))
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/submit", response_model=TaskResponse)
def submit_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Runner submits task for poster confirmation (status -> 'awaiting_confirmation')."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["runner_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned runner can submit this task.")
        if task["status"] != "in_progress":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task must be 'in_progress' to submit.")

        conn.execute(
            "UPDATE tasks SET status = 'awaiting_confirmation', submitted_on = ? WHERE id = ?",
            (now_iso(), task_id),
        )
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/confirm", response_model=TaskResponse)
def confirm_task_completion(task_id: int, current_user: dict = Depends(get_current_user)):
    """Poster confirms task is done (status -> 'completed', runner tasks_done + 1)."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["poster_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the task creator can confirm completion.")
        if task["status"] != "awaiting_confirmation":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not awaiting confirmation.")

        conn.execute(
            "UPDATE tasks SET status = 'completed', finished_on = ? WHERE id = ?",
            (now_iso(), task_id),
        )
        if task["runner_id"]:
            conn.execute("UPDATE users SET tasks_done = tasks_done + 1 WHERE id = ?", (task["runner_id"],))

        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/abandon", response_model=TaskResponse)
def abandon_task(task_id: int, current_user: dict = Depends(get_current_user)):
    """Runner abandons task and returns it to 'open' state."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["runner_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned runner can abandon task.")
        if task["status"] not in ("accepted", "in_progress"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task cannot be abandoned in its current state.")

        conn.execute(
            """UPDATE tasks
               SET runner_id = NULL, status = 'open', accepted_on = NULL, started_on = NULL, submitted_on = NULL
               WHERE id = ?""",
            (task_id,),
        )
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: int, cancel_in: TaskCancel, current_user: dict = Depends(get_current_user)):
    """Poster cancels a task with an optional reason."""
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
        if task["poster_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the task creator can cancel this task.")
        if task["status"] in ("completed", "cancelled"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Task is already {task['status']}.")

        conn.execute(
            "UPDATE tasks SET status = 'cancelled', cancelled_on = ?, cancellation_reason = ? WHERE id = ?",
            (now_iso(), cancel_in.reason, task_id),
        )
        row = conn.execute(get_task_query_base() + " WHERE t.id = ?", (task_id,)).fetchone()
        return dict(row)
