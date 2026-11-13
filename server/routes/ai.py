from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from server.database import get_db
from server.schemas import AIPromptRequest, AIPricingRequest, AICrosscheckRequest
from server.security import get_current_user, get_optional_current_user
from server.ai.nlp_extractor import parse_errand_intent
from server.ai.pricing_engine import calculate_dynamic_pricing
from server.ai.matching_engine import rank_matching_runners
from server.ai.autonomous_agent import ai_agent

router = APIRouter(prefix="/api/ai", tags=["AI & Autonomous Engine"])


@router.post("/parse-intent")
def parse_intent(payload: AIPromptRequest):
    """
    NLP Entity Extractor:
    Parses unstructured natural language text or voice transcripts into
    structured Errand entities with automatic category classification,
    deadline inference, location extraction, and safety guardrails.
    """
    result = parse_errand_intent(payload.prompt)
    if result.get("is_valid"):
        ai_agent.record_nlp_extraction()
    return result


@router.post("/estimate-price")
def estimate_price(payload: AIPricingRequest):
    """
    Machine Learning / Heuristic Dynamic Pricing Engine:
    Calculates fair market compensation range, estimated completion duration,
    and detects pricing anomalies or exploitation risks.
    """
    result = calculate_dynamic_pricing(
        category=payload.category,
        title=payload.title or "",
        description=payload.description or "",
        deadline=payload.deadline or "",
        user_price=payload.user_price
    )
    ai_agent.record_pricing_query()
    return result


@router.get("/match-runners/{task_id}")
def match_runners(task_id: int):
    """
    Explainable AI (XAI) Runner Matching:
    Computes multi-factor affinity scores (Category History, Rating & Track Record,
    Availability, Locality Proximity) and provides explainable rationale.
    """
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        ranked = rank_matching_runners(conn, task_id, limit=5)
        return {
            "task_id": task_id,
            "category": task["category"],
            "total_candidates_analyzed": len(ranked),
            "matches": ranked
        }


@router.post("/crosscheck/{task_id}")
def crosscheck_task(task_id: int, payload: AICrosscheckRequest = None, current_user: dict = Depends(get_current_user)):
    """
    Autonomous Errand Crosscheck & Verification Engine:
    Performs algorithmic checks across temporal plausibility, keyword alignment,
    identity segregation, and escrow release compliance before completion release.
    """
    with get_db() as conn:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        task_dict = dict(task)
        notes = payload.completion_notes if payload else None
        audit = ai_agent.perform_crosscheck(task_dict, notes)
        return audit


@router.post("/autonomous-dispatch/{task_id}")
def autonomous_dispatch(task_id: int, current_user: dict = Depends(get_current_user)):
    """
    Autonomous Dispatch Trigger:
    Autonomously evaluates open task candidates and dispatches the optimal runner
    with the highest multi-criteria affinity score.
    """
    with get_db() as conn:
        # Check permissions: only poster or admin can trigger autonomous dispatch
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        if task["poster_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only task poster can trigger autonomous dispatch.")

        result = ai_agent.autonomous_dispatch(conn, task_id)
        if not result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["reason"])
        return result


@router.get("/telemetry")
def get_ai_telemetry():
    """
    Retrieves real-time AI Agent telemetry, health status, and autonomous metrics.
    """
    return ai_agent.get_telemetry()


@router.post("/toggle-agent")
def toggle_agent(current_user: dict = Depends(get_current_user)):
    """
    Toggles the autonomous agent dispatch mode.
    """
    ai_agent.auto_dispatch_enabled = not ai_agent.auto_dispatch_enabled
    return {
        "auto_dispatch_enabled": ai_agent.auto_dispatch_enabled,
        "status": "active" if ai_agent.auto_dispatch_enabled else "paused",
    }
