import math
from typing import Dict, Any, Optional

CATEGORY_EFFORT_WEIGHTS = {
    "Grocery Shopping": {"base_rate": 11.0, "time_mins": 35, "hourly_rate": 16.0},
    "Delivery / Courier": {"base_rate": 8.5, "time_mins": 25, "hourly_rate": 15.0},
    "Pharmacy Pickup": {"base_rate": 8.0, "time_mins": 20, "hourly_rate": 15.0},
    "Pet Care": {"base_rate": 14.0, "time_mins": 45, "hourly_rate": 17.0},
    "House Cleaning": {"base_rate": 22.0, "time_mins": 75, "hourly_rate": 18.0},
    "Gardening": {"base_rate": 20.0, "time_mins": 60, "hourly_rate": 18.0},
    "Moving Help": {"base_rate": 28.0, "time_mins": 90, "hourly_rate": 20.0},
    "Tech Support": {"base_rate": 24.0, "time_mins": 45, "hourly_rate": 25.0},
    "Cooking / Meal Prep": {"base_rate": 18.0, "time_mins": 60, "hourly_rate": 18.0},
    "Car Wash": {"base_rate": 15.0, "time_mins": 40, "hourly_rate": 17.0},
    "Laundry": {"base_rate": 12.0, "time_mins": 35, "hourly_rate": 15.0},
    "Other": {"base_rate": 10.0, "time_mins": 30, "hourly_rate": 15.0},
}


def calculate_dynamic_pricing(
    category: str,
    title: str = "",
    description: str = "",
    deadline: str = "",
    user_price: Optional[float] = None
) -> Dict[str, Any]:
    """
    Predictive Dynamic Pricing & Fair-Reward Engine.
    Uses multi-variable heuristics to compute fair market compensation,
    estimated labor time, and anomaly/fraud detection.
    """
    cat_profile = CATEGORY_EFFORT_WEIGHTS.get(category, CATEGORY_EFFORT_WEIGHTS["Other"])
    base_rate = cat_profile["base_rate"]
    est_time = cat_profile["time_mins"]

    # 1. Complexity Multiplier from description depth and keyword triggers
    combined_text = f"{title} {description}".lower()
    word_count = len(combined_text.split())

    complexity_mult = 1.0
    if word_count > 30:
        complexity_mult += 0.15
    if any(k in combined_text for k in ["heavy", "stairs", "multiple", "urgent", "fragile", "assemble", "deep"]):
        complexity_mult += 0.20

    # 2. Urgency Multiplier
    urgency_mult = 1.0
    deadline_lower = (deadline or "").lower()
    if any(u in deadline_lower or u in combined_text for u in ["asap", "urgent", "1 hour", "today"]):
        urgency_mult += 0.25

    # 3. Compute predicted fair rate
    recommended_price = round(base_rate * complexity_mult * urgency_mult, 2)
    min_fair = round(recommended_price * 0.80, 2)
    max_fair = round(recommended_price * 1.35, 2)
    est_duration_minutes = int(est_time * complexity_mult)

    # 4. Anomaly & Fairness Assessment
    assessment = "fair"
    assessment_detail = "Price is within optimal fair market range for local runners."
    anomaly_detected = False

    if user_price is not None:
        if user_price < min_fair * 0.65:
            assessment = "underpriced"
            assessment_detail = f"Offered reward (£{user_price:.2f}) is significantly below living wage standards (£{min_fair:.2f} min). Runners may decline."
            anomaly_detected = True
        elif user_price > max_fair * 4.0:
            assessment = "overpriced_suspicious"
            assessment_detail = f"Offered reward (£{user_price:.2f}) is abnormally high for this task type. System flagged for anti-fraud review."
            anomaly_detected = True
        elif user_price < min_fair:
            assessment = "slightly_low"
            assessment_detail = f"Slightly below recommended market rate (£{min_fair:.2f} - £{max_fair:.2f})."
        elif user_price > max_fair:
            assessment = "generous"
            assessment_detail = "Generous reward! Likely to be accepted rapidly by top-rated runners."

    return {
        "recommended_price": recommended_price,
        "price_range": {
            "min": min_fair,
            "max": max_fair,
        },
        "estimated_duration_minutes": est_duration_minutes,
        "hourly_equivalent": round((recommended_price / (est_duration_minutes / 60)), 2),
        "complexity_tier": "High" if complexity_mult > 1.25 else ("Medium" if complexity_mult > 1.0 else "Standard"),
        "assessment": assessment,
        "assessment_detail": assessment_detail,
        "anomaly_detected": anomaly_detected,
    }
