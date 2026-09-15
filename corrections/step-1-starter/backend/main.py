import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import create_engine

# La ligne de connexion à la base — déjà configurée pour toi (Docker fournit l'adresse).
# Hors Docker, on retombe sur un simple fichier SQLite. Tu n'as rien à changer ici.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
