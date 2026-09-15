import os
# Base SQLite de test, neuve à chaque exécution.
if os.path.exists("./test.db"):
    os.remove("./test.db")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient
from main import app


def test_inscription_puis_tache():
    # Le "with" démarre l'app (crée les tables + les données de démo).
    with TestClient(app) as client:
        # 1) On crée une famille de test → on récupère un token
        r = client.post("/api/signup", params={
            "email": "test@fam.fr", "password": "secret", "name": "Chef", "family": "Test"})
        assert r.status_code == 200
        token = r.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2) On crée une tâche pour soi
        r = client.post("/api/tasks", params={"title": "Sortir les poubelles"}, headers=headers)
        assert r.status_code == 200

        # 3) On relit ses tâches : elle est là
        r = client.get("/api/tasks", headers=headers)
        assert r.status_code == 200
        assert any(t["title"] == "Sortir les poubelles" for t in r.json())


def test_sans_token_refuse():
    with TestClient(app) as client:
        assert client.get("/api/tasks").status_code == 401


def test_logout_invalide_le_jeton():
    """Après déconnexion, l'ancien jeton ne doit plus ouvrir aucune porte."""
    with TestClient(app) as client:
        r = client.post("/api/login", params={"email": "maman@durand.fr",
                                              "password": "durand"})
        jeton = r.json()["token"]
        entetes = {"Authorization": "Bearer " + jeton}

        # Le jeton marche
        assert client.get("/api/me", headers=entetes).status_code == 200

        # On se déconnecte
        assert client.post("/api/logout", headers=entetes).status_code == 200

        # Le MEME jeton ne vaut plus rien : le serveur l'a invalidé
        assert client.get("/api/me", headers=entetes).status_code == 401
        assert client.get("/api/tasks", headers=entetes).status_code == 401
