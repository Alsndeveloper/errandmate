import sqlite3
from typing import List, Dict, Any


def rank_matching_runners(
    conn: sqlite3.Connection,
    task_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Explainable AI (XAI) Runner Matching Engine.
    Evaluates available runners across 4 multi-criteria affinity vectors:
    1. Historical Category Experience
    2. Runner Reputation & Reliability (Rating + Completed Task Count)
    3. Active Workload Availability
    4. Geographic Locality Proximity
    """
    # Fetch task details
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        return []

    task_dict = dict(task)
    category = task_dict.get("category") or "Other"
    location = (task_dict.get("location") or "").lower()
    poster_id = task_dict.get("poster_id")

    # Fetch eligible runners (role in 'runner', 'both', not the poster)
    runners_sql = """
        SELECT u.id, u.full_name, u.role, u.tasks_done,
               (SELECT AVG(rating) FROM ratings WHERE runner_id = u.id) as avg_rating,
               (SELECT COUNT(*) FROM ratings WHERE runner_id = u.id) as total_reviews,
               (SELECT COUNT(*) FROM tasks WHERE runner_id = u.id AND status IN ('accepted', 'in_progress')) as active_load
        FROM users u
        WHERE u.id != ? AND u.role IN ('runner', 'both')
    """
    candidates = conn.execute(runners_sql, (poster_id,)).fetchall()
    if not candidates:
        return []

    ranked = []
    for c in candidates:
        runner = dict(c)
        r_id = runner["id"]
        tasks_done = runner.get("tasks_done") or 0
        avg_rating = runner.get("avg_rating") or 4.5  # default prior for unrated runners
        total_reviews = runner.get("total_reviews") or 0
        active_load = runner.get("active_load") or 0

        # Factor 1: Experience & Reliability Score (0 - 40 pts)
        # Bayesian smoothed rating
        smooth_rating = ((total_reviews * avg_rating) + (2 * 4.0)) / (total_reviews + 2)
        rating_score = (smooth_rating / 5.0) * 25.0
        volume_score = min(tasks_done * 1.5, 15.0)
        reputation_points = rating_score + volume_score

        # Factor 2: Category Affinity (0 - 30 pts)
        cat_history = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE runner_id = ? AND category = ? AND status = 'completed'",
            (r_id, category)
        ).fetchone()[0]
        cat_score = min(cat_history * 10.0, 30.0)
        if cat_history == 0 and tasks_done > 0:
            cat_score = 15.0  # general errand experience transfer

        # Factor 3: Availability & Workload (0 - 20 pts)
        if active_load == 0:
            availability_score = 20.0
        elif active_load == 1:
            availability_score = 14.0
        elif active_load == 2:
            availability_score = 8.0
        else:
            availability_score = 2.0

        # Factor 4: Locality Overlap (0 - 10 pts)
        # Check if runner has completed jobs in same locality
        loc_history = 0
        if location:
            loc_history = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE runner_id = ? AND LOWER(location) LIKE ?",
                (r_id, f"%{location[:5]}%")
            ).fetchone()[0]
        locality_score = 10.0 if loc_history > 0 else 6.0

        total_match_score = min(round(reputation_points + cat_score + availability_score + locality_score), 99)

        # Explainable AI Rationale Generation
        reasons = []
        if avg_rating and avg_rating >= 4.7:
            reasons.append(f"⭐ High Quality Rating: {avg_rating:.1f}/5 across {total_reviews} reviews")
        elif tasks_done > 3:
            reasons.append(f"✅ Verified Track Record: {tasks_done} errands completed")

        if cat_history > 0:
            reasons.append(f"🎯 Category Specialist: {cat_history} '{category}' jobs finished")
        else:
            reasons.append(f"⚡ Ready to accept new '{category}' opportunities")

        if active_load == 0:
            reasons.append("🟢 Immediate Availability (0 active tasks)")
        else:
            reasons.append(f"🟡 Currently handling {active_load} active errand")

        if loc_history > 0:
            reasons.append(f"📍 Familiar with local route: {task_dict.get('location')}")

        ranked.append({
            "runner_id": r_id,
            "full_name": runner["full_name"],
            # No email/phone: this endpoint is public. Contact details are never
            # shared with people who aren't part of an errand.
            "match_score_percent": total_match_score,
            "tasks_done": tasks_done,
            "average_rating": round(avg_rating, 1) if runner.get("avg_rating") else None,
            "active_tasks_count": active_load,
            "xai_reasons": reasons,
            "confidence_level": "Optimal" if total_match_score >= 85 else ("Strong" if total_match_score >= 70 else "Eligible"),
        })

    # Sort descending by match score
    ranked.sort(key=lambda x: x["match_score_percent"], reverse=True)
    return ranked[:limit]
