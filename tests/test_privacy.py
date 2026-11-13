"""Privacy tests: public endpoints must never expose personal data.

These walk every endpoint that works WITHOUT logging in and check that no
contact details, addresses, ID numbers or password hashes appear anywhere
in the response.
"""

import json
import uuid

from fastapi.testclient import TestClient

from server.app import app
from server.security import mask_id_number

client = TestClient(app)

PRIVATE_FIELDS = {
    "email", "phone", "password", "id_number", "residential_address", "postcode",
    "poster_phone", "runner_phone",
}


def find_private_fields(data):
    """Return every private key found anywhere in a JSON response."""
    found = set()
    if isinstance(data, dict):
        found |= PRIVATE_FIELDS & data.keys()
        for value in data.values():
            found |= find_private_fields(value)
    elif isinstance(data, list):
        for item in data:
            found |= find_private_fields(item)
    return found


def public_urls():
    task_ids = [t["id"] for t in client.get("/api/tasks").json()][:3]
    urls = ["/api/tasks", "/api/stats/dashboard", "/api/stats/categories", "/api/ai/telemetry"]
    for task_id in task_ids:
        urls += [f"/api/tasks/{task_id}", f"/api/ai/match-runners/{task_id}"]
    for user_id in (1, 2, 3):
        urls += [f"/api/users/{user_id}", f"/api/ratings/runner/{user_id}"]
    return urls


def test_public_endpoints_expose_no_personal_data():
    for url in public_urls():
        res = client.get(url)
        if res.status_code != 200:
            continue
        leaked = find_private_fields(res.json())
        assert not leaked, f"{url} exposes private fields: {leaked}"


def test_id_numbers_are_masked_before_storage():
    res = client.post("/api/auth/register", json={
        "full_name": "Privacy Tester",
        "email": f"privacy_{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+447888999444",
        "password": "Password123!",
        "role": "both",
        "id_type": "Passport",
        "id_number": "P98765432",
    })
    assert res.status_code == 201
    stored = res.json()["user"]["id_number"]
    assert stored == "*****5432"
    assert "P9876" not in json.dumps(res.json())


def test_mask_id_number_short_values():
    assert mask_id_number("1234") == "****"
    assert mask_id_number("  AB12345 ") == "***2345"
