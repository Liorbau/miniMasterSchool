"""HTTP layer: global exception handlers and status codes."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_put_tasks_unknown_user_uses_global_404_handler():
    r = client.put(
        "/tasks",
        json={
            "user_id": 9_999_999,
            "step_name": "personal_details",
            "task_name": "personal_details",
            "payload": {
                "user_id": 9_999_999,
                "first_name": "A",
                "last_name": "B",
                "email": "x@y.com",
                "timestamp": "2026-01-01",
            },
        },
    )
    assert r.status_code == 404
    detail = r.json()["detail"]
    assert "does not exist" in detail
    assert "9999999" in detail


def test_put_tasks_step_mismatch_uses_global_400_handler():
    r = client.post("/users", json={"email": "api@example.com"})
    uid = r.json()["user_id"]
    r2 = client.put(
        "/tasks",
        json={
            "user_id": uid,
            "step_name": "iq_test",
            "task_name": "personal_details",
            "payload": {
                "user_id": uid,
                "first_name": "A",
                "last_name": "B",
                "email": "x@y.com",
                "timestamp": "2026-01-01",
            },
        },
    )
    assert r2.status_code == 400
    assert r2.json()["detail"].startswith("Flow violation:")


def test_put_tasks_accepts_task_payload_key_alias():
    r = client.post("/users", json={"email": "alias@example.com"})
    uid = r.json()["user_id"]
    r2 = client.put(
        "/tasks",
        json={
            "user_id": uid,
            "step_name": "personal_details",
            "task_name": "personal_details",
            "task_payload": {
                "user_id": uid,
                "first_name": "Pat",
                "last_name": "Lee",
                "email": "pat@example.com",
                "timestamp": "2026-01-01",
            },
        },
    )
    assert r2.status_code == 200
