import uuid
import pytest
from fastapi.testclient import TestClient
from server.app import app
from server.ai.nlp_extractor import parse_errand_intent, check_content_safety
from server.ai.pricing_engine import calculate_dynamic_pricing
from server.ai.crosscheck_engine import autonomous_task_crosscheck

client = TestClient(app)


def test_nlp_extraction_and_safety():
    # 1. Normal prompt
    prompt = "Can someone pick up groceries from Tesco on Albany Road tomorrow at 4pm? Offering £18."
    res = parse_errand_intent(prompt)
    assert res["is_valid"] is True
    extracted = res["extracted"]
    assert extracted["category"] == "Grocery Shopping"
    assert extracted["price"] == 18.0
    assert "Albany Road" in extracted["location"] or "Tesco" in extracted["location"]

    # 2. Complex address, task, and time extraction (Elmfield Rd / Maplewood St / CF24 9ZZ)
    dog_prompt = "I live in Elmfield road cf24 9zz 14 maplewood street and  i need somone to walk my dog on monday 21 , pm"
    res_dog = parse_errand_intent(dog_prompt)
    assert res_dog["is_valid"] is True
    assert res_dog["extracted"]["category"] == "Pet Care"
    assert "14 Maplewood Street" in res_dog["extracted"]["location"]
    assert "CF24 9ZZ" in res_dog["extracted"]["location"]
    assert "Monday" in res_dog["extracted"]["deadline"]
    assert res_dog["categorized_entities"]["postcode"] == "CF24 9ZZ"
    assert res_dog["categorized_entities"]["task"] == "Walk my dog"

    # 3. Screenshot Example 1: City Rd & St Peters St -> Moving Help (Truck Loading)
    truck_prompt = "i live in city road cf24 3ba 17 st peters street, i want someone to help me load things to a truck time 10 a"
    res_truck = parse_errand_intent(truck_prompt)
    assert res_truck["is_valid"] is True
    assert res_truck["extracted"]["category"] == "Moving Help"
    assert "17 St Peters Street" in res_truck["extracted"]["location"]
    assert "CF24 3BA" in res_truck["extracted"]["location"]
    assert "10 AM" in res_truck["extracted"]["deadline"]
    assert "truck" in res_truck["categorized_entities"]["task"].lower() or "load" in res_truck["categorized_entities"]["task"].lower()

    # 4. Screenshot Example 2: 40gordons road -> Gardening (Clean front yard)
    yard_prompt = "lives in 40gordons road, cf24 3al, and need someone to clean my front yard it doesnt have to be a supe"
    res_yard = parse_errand_intent(yard_prompt)
    assert res_yard["is_valid"] is True
    assert res_yard["extracted"]["category"] == "Gardening"
    assert "40 Gordons Road" in res_yard["extracted"]["location"]
    assert "CF24 3AL" in res_yard["extracted"]["location"]
    assert "front yard" in res_yard["categorized_entities"]["task"].lower()

    # 5. Screenshot Example 3: 14 maplewood street -> Gardening (Task clean backyard)
    backyard_prompt = "live in 14 maplewood street cf24 9zy, time of the task 7pm 21st monday afternoon, task clean my backyard"
    res_backyard = parse_errand_intent(backyard_prompt)
    assert res_backyard["is_valid"] is True
    assert res_backyard["extracted"]["category"] == "Gardening"
    assert "14 Maplewood Street" in res_backyard["extracted"]["location"]
    assert "CF24 9ZY" in res_backyard["extracted"]["location"]
    assert "Monday 21st" in res_backyard["extracted"]["deadline"]
    assert "7PM" in res_backyard["extracted"]["deadline"]
    assert "backyard" in res_backyard["categorized_entities"]["task"].lower()

    # 6. Safety filter check
    unsafe_prompt = "Need someone to transport illicit drug package secretly"
    safety = check_content_safety(unsafe_prompt)
    assert safety["is_safe"] is False
    assert "drug" in safety["flagged_keywords"]

    res_unsafe = parse_errand_intent(unsafe_prompt)
    assert res_unsafe["is_valid"] is False


def test_dynamic_pricing_and_anomaly_detection():
    # Standard pricing
    pricing = calculate_dynamic_pricing(
        category="Grocery Shopping",
        title="Weekly supermarket haul",
        description="Pick up 4 bags of heavy groceries including milk and potatoes",
        deadline="Today ASAP",
        user_price=16.0
    )
    assert pricing["recommended_price"] > 0
    assert pricing["estimated_duration_minutes"] > 0
    assert pricing["complexity_tier"] in ("Medium", "High")
    assert pricing["anomaly_detected"] is False

    # Underpriced anomaly
    underpriced = calculate_dynamic_pricing(
        category="House Cleaning",
        user_price=3.0
    )
    assert underpriced["assessment"] == "underpriced"
    assert underpriced["anomaly_detected"] is True

    # Overpriced anomaly
    overpriced = calculate_dynamic_pricing(
        category="Delivery / Courier",
        user_price=500.0
    )
    assert overpriced["assessment"] == "overpriced_suspicious"
    assert overpriced["anomaly_detected"] is True


def test_autonomous_crosscheck():
    # Valid normal task
    sample_task = {
        "id": 999,
        "title": "Collect boots pharmacy prescription",
        "description": "Collect pain tablets from Boots on Queen St",
        "category": "Pharmacy Pickup",
        "price": 10.0,
        "poster_id": 1,
        "runner_id": 2,
        "started_on": "2026-11-04T10:00:00",
        "submitted_on": "2026-11-04T10:25:00",
    }
    notes = "Prescription picked up from Boots and left with security desk."
    audit = autonomous_task_crosscheck(sample_task, notes)
    assert audit["verdict"] == "VERIFIED_AUTONOMOUSLY"
    assert audit["confidence_score"] >= 80

    # Self-assignment conflict of interest
    conflict_task = sample_task.copy()
    conflict_task["runner_id"] = conflict_task["poster_id"]
    audit_conflict = autonomous_task_crosscheck(conflict_task, notes)
    assert "SELF_ASSIGNMENT_VIOLATION" in audit_conflict["flags"]
    assert audit_conflict["confidence_score"] < 60


def test_ai_api_endpoints():
    # NLP Parse Intent
    res_nlp = client.post("/api/ai/parse-intent", json={
        "prompt": "Urgent dog walking needed in Roath park today, paying 20 quid"
    })
    assert res_nlp.status_code == 200
    data_nlp = res_nlp.json()
    assert data_nlp["is_valid"] is True
    assert data_nlp["extracted"]["category"] == "Pet Care"
    assert data_nlp["extracted"]["price"] == 20.0

    # Dynamic Pricing API
    res_price = client.post("/api/ai/estimate-price", json={
        "category": "Moving Help",
        "title": "Help move heavy couch up 3 flights of stairs",
        "deadline": "Today ASAP"
    })
    assert res_price.status_code == 200
    data_price = res_price.json()
    assert data_price["recommended_price"] >= 25.0

    # Telemetry API
    res_telem = client.get("/api/ai/telemetry")
    assert res_telem.status_code == 200
    assert "telemetry" in res_telem.json()
    assert res_telem.json()["status"] == "active"
