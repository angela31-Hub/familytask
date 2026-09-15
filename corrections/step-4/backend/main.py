import os
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks(session: Session = Depends(get_session)):
    return session.exec(select(Task)).all()


# Si le titre est vide, on attribue une tâche au hasard plutôt que de refuser.


@app.post("/api/tasks")
def add_task(title: str, session: Session = Depends(get_session)):
    # Un titre vide n'a pas de sens : on refuse proprement plutôt que
    # d'enregistrer une tâche sans nom. 422 = « données invalides ».
    if not title.strip():
        raise HTTPException(status_code=422, detail="Le titre ne peut pas être vide")
    task = Task(title=title)
    session.add(task); session.commit(); session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    # 404 = « cette chose n'existe pas ». On lève une vraie erreur HTTP :
    # renvoyer un message d'erreur avec un code 200 tromperait le client.
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    task.done = not task.done
    session.add(task); session.commit(); session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    session.delete(task); session.commit()
    return {"ok": True}
