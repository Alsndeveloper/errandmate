from fastapi import APIRouter, Depends
from server.database import get_db
from server.schemas import DashboardStats
from server.security import get_optional_current_user

router = APIRouter(prefix="/api/stats", tags=["Dashboard & Statistics"])


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats(current_user: dict = Depends(get_optional_current_user)):
    """Provides key performance indicators for the dashboard and user analytics."""
    with get_db() as conn:
        total_open = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'open'").fetchone()[0]
        platform_total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        platform_completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'").fetchone()[0]

        user_id = current_user["id"] if current_user else None
        if user_id:
            i_posted = conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id = ?", (user_id,)).fetchone()[0]
            i_active = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE runner_id = ? AND status IN ('accepted', 'in_progress', 'awaiting_confirmation')",
                (user_id,),
            ).fetchone()[0]
            i_done = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE (poster_id = ? OR runner_id = ?) AND status = 'completed'",
                (user_id, user_id),
            ).fetchone()[0]
            earnings = conn.execute(
                "SELECT COALESCE(SUM(price), 0) FROM tasks WHERE runner_id = ? AND status = 'completed'",
                (user_id,),
            ).fetchone()[0]
            runner_rating = conn.execute(
                "SELECT AVG(rating) FROM ratings WHERE runner_id = ?",
                (user_id,),
            ).fetchone()[0]
        else:
            i_posted = 0
            i_active = 0
            i_done = 0
            earnings = 0.0
            runner_rating = None

        return {
            "total_open_tasks": total_open,
            "my_posted_tasks": i_posted,
            "my_active_tasks": i_active,
            "my_completed_tasks": i_done,
            "my_earnings": float(earnings),
            "platform_total_tasks": platform_total,
            "platform_completed_tasks": platform_completed,
            "runner_average_rating": round(runner_rating, 2) if runner_rating is not None else None,
        }


@router.get("/categories")
def get_category_counts():
    """Returns task count distribution across errand categories."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT category, COUNT(*) as count
               FROM tasks
               GROUP BY category
               ORDER BY count DESC"""
        ).fetchall()
        return [{"category": row["category"] or "Other", "count": row["count"]} for row in rows]
