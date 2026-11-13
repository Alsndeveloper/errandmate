import datetime
import sqlite3
from typing import Dict, Any, Optional
from server.ai.matching_engine import rank_matching_runners
from server.ai.crosscheck_engine import autonomous_task_crosscheck


class ErrandMateAutonomousAgent:
    """
    ErrandMate Autonomous Agent ('Nova-Agent').
    Orchestrates autonomous errand matching, dispatch triggers,
    and fraud prevention crosschecks.
    """

    def __init__(self):
        self.agent_name = "Nova-1 Autonomous Dispatch & Crosscheck Agent"
        self.version = "2.1-AI"
        self.status = "active"
        self.auto_dispatch_enabled = True
        self.telemetry = {
            "started_at": datetime.datetime.now().isoformat(),
            "autonomous_crosschecks_count": 0,
            "ai_dispatches_count": 0,
            "pricing_queries_count": 0,
            "nlp_extractions_count": 0,
            "verified_completions": 0,
            "anomalies_flagged": 0,
        }

    def record_nlp_extraction(self):
        self.telemetry["nlp_extractions_count"] += 1

    def record_pricing_query(self):
        self.telemetry["pricing_queries_count"] += 1

    def autonomous_dispatch(self, conn: sqlite3.Connection, task_id: int) -> Dict[str, Any]:
        """
        Autonomously evaluates open task candidates and dispatches the
        optimal runner with highest confidence.
        """
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return {"success": False, "reason": "Task not found"}

        if task["status"] != "open":
            return {"success": False, "reason": f"Task is not open (status: {task['status']})"}

        ranked = rank_matching_runners(conn, task_id, limit=3)
        if not ranked:
            return {
                "success": False,
                "reason": "No qualified runners currently available for this category."
            }

        top_match = ranked[0]
        if top_match["match_score_percent"] < 65:
            return {
                "success": False,
                "reason": f"Highest candidate affinity ({top_match['match_score_percent']}%) did not meet autonomous dispatch threshold (65%)."
            }

        # Execute assignment
        now = datetime.datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE tasks SET runner_id = ?, status = 'accepted', accepted_on = ? WHERE id = ?",
            (top_match["runner_id"], now, task_id),
        )

        self.telemetry["ai_dispatches_count"] += 1

        return {
            "success": True,
            "dispatched_runner": top_match,
            "alternatives": ranked[1:],
            "reasoning": f"Autonomously dispatched {top_match['full_name']} based on {top_match['match_score_percent']}% affinity score.",
            "dispatched_at": now,
        }

    def perform_crosscheck(self, task: Dict[str, Any], notes: Optional[str] = None) -> Dict[str, Any]:
        result = autonomous_task_crosscheck(task, notes)
        self.telemetry["autonomous_crosschecks_count"] += 1
        if result["verdict"] == "VERIFIED_AUTONOMOUSLY":
            self.telemetry["verified_completions"] += 1
        elif result["verdict"] == "ANOMALY_SUSPECTED":
            self.telemetry["anomalies_flagged"] += 1
        return result

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "version": self.version,
            "status": self.status,
            "auto_dispatch_enabled": self.auto_dispatch_enabled,
            "telemetry": self.telemetry,
            "health": "operational",
            "last_heartbeat": datetime.datetime.now().isoformat(),
        }


# Global agent instance
ai_agent = ErrandMateAutonomousAgent()
