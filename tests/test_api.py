import uuid
import pytest
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"


def test_auth_registration_and_login():
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Test Runner",
        "email": unique_email,
        "phone": "+447000111222",
        "password": "Password123!",
        "role": "both"
    }

    # Register
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    reg_data = res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email

    # Login
    login_payload = {
        "email": unique_email,
        "password": "Password123!"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == unique_email


def test_admin_login_without_email():
    res = client.post("/api/auth/login", json={
        "email": "admin",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["is_id_verified"] == 1


def test_registration_with_personal_identification():
    unique_email = f"verified_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Verified Resident",
        "email": unique_email,
        "phone": "+447888999111",
        "password": "Password123!",
        "role": "both",
        "residential_address": "14 Maplewood Street, Roath",
        "postcode": "CF24 9ZZ",
        "id_type": "UK Driving Licence",
        "id_number": "DL-CARD-9921"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    user = res.json()["user"]
    assert user["residential_address"] == "14 Maplewood Street, Roath"
    assert user["postcode"] == "CF24 9ZZ"
    assert user["id_type"] == "UK Driving Licence"
    assert user["is_id_verified"] == 1


def test_task_creation_and_lifecycle():
    # 1. Register poster
    poster_email = f"poster_{uuid.uuid4().hex[:8]}@example.com"
    res_p = client.post("/api/auth/register", json={
        "full_name": "Jane Poster",
        "email": poster_email,
        "phone": "+447000333444",
        "password": "Password123!",
        "role": "poster"
    })
    token_poster = res_p.json()["access_token"]
    headers_poster = {"Authorization": f"Bearer {token_poster}"}

    # 2. Register runner
    runner_email = f"runner_{uuid.uuid4().hex[:8]}@example.com"
    res_r = client.post("/api/auth/register", json={
        "full_name": "Bob Runner",
        "email": runner_email,
        "phone": "+447000555666",
        "password": "Password123!",
        "role": "runner"
    })
    token_runner = res_r.json()["access_token"]
    headers_runner = {"Authorization": f"Bearer {token_runner}"}

    # 3. Poster creates task
    task_payload = {
        "title": "Collect parcel from Post Office",
        "description": "Parcel pickup slip is ready on table",
        "category": "Delivery / Courier",
        "location": "Cardiff Bay",
        "price": 12.50,
        "deadline": "Today 5pm"
    }
    res_t = client.post("/api/tasks", json=task_payload, headers=headers_poster)
    assert res_t.status_code == 201
    task = res_t.json()
    task_id = task["id"]
    assert task["status"] == "open"
    assert task["price"] == 12.50

    # 4. Runner accepts task
    res_accept = client.post(f"/api/tasks/{task_id}/accept", headers=headers_runner)
    assert res_accept.status_code == 200
    assert res_accept.json()["status"] == "accepted"

    # 5. Runner starts task
    res_start = client.post(f"/api/tasks/{task_id}/start", headers=headers_runner)
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "in_progress"

    # 6. Runner submits task
    res_submit = client.post(f"/api/tasks/{task_id}/submit", headers=headers_runner)
    assert res_submit.status_code == 200
    assert res_submit.json()["status"] == "awaiting_confirmation"

    # 7. Poster confirms completion
    res_confirm = client.post(f"/api/tasks/{task_id}/confirm", headers=headers_poster)
    assert res_confirm.status_code == 200
    assert res_confirm.json()["status"] == "completed"

    # 8. Poster rates runner
    rating_payload = {
        "task_id": task_id,
        "rating": 5,
        "review": "Fast delivery and great communication!"
    }
    res_rate = client.post("/api/ratings", json=rating_payload, headers=headers_poster)
    assert res_rate.status_code == 201
    assert res_rate.json()["rating"] == 5


def test_dashboard_stats():
    res = client.get("/api/stats/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_open_tasks" in data
    assert "platform_total_tasks" in data
    assert "platform_completed_tasks" in data
