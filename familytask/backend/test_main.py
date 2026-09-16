import os
from pathlib import Path

TEST_DATABASE = Path(__file__).with_name("test.db")
if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"

from fastapi.testclient import TestClient

from main import app


def test_inscription_puis_tache():
    with TestClient(app) as client:
        signup_response = client.post(
            "/api/signup",
            json={
                "email": "test@example.com",
                "password": "secret",
                "name": "Parent",
                "family": "Famille Test",
                "lien": "parent",
            },
        )
        assert signup_response.status_code == 200

        token = signup_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        create_response = client.post(
            "/api/tasks",
            json={"title": "Sortir les poubelles"},
            headers=headers,
        )
        assert create_response.status_code == 200

        tasks_response = client.get("/api/tasks", headers=headers)
        assert tasks_response.status_code == 200
        assert any(
            task["title"] == "Sortir les poubelles"
            for task in tasks_response.json()
        )

    TEST_DATABASE.unlink(missing_ok=True)


def test_taches_sans_token_refusees():
    with TestClient(app) as client:
        response = client.get("/api/tasks")

    assert response.status_code == 401
