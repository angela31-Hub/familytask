import os
import hashlib
import secrets
from typing import Optional

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

LIENS_DEFAUT = ["mère", "père", "fille", "fils", "frère", "sœur",
                "grand-mère", "grand-père", "oncle", "tante"]


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


# --- Modèles ---
class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)   # identifiant de connexion
    name: str                                     # prénom
    lien: str = ""                                # lien de parenté (mère, fille…)
    is_admin: bool = False                        # droit de gérer les comptes / assigner
    family_code: str = Field(index=True)          # tenant interne
    family_name: str = ""
    password_hash: str = ""
    token: Optional[str] = Field(default=None, index=True)


class Lien(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_code: str = Field(index=True)
    label: str


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_code: str = Field(index=True)
    title: str
    done: bool = False
    member_id: Optional[int] = Field(default=None, foreign_key="member.id")   # assignée à
    created_by: Optional[int] = Field(default=None, foreign_key="member.id")  # donnée par


def get_session():
    with Session(engine) as session:
        yield session


def public_member(m: Member) -> dict:
    return {"id": m.id, "name": m.name, "email": m.email, "lien": m.lien,
            "is_admin": m.is_admin, "family_code": m.family_code, "family_name": m.family_name}


app = FastAPI(title="FamilyTask")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)


def seed_liens(session: Session, family_code: str):
    for label in LIENS_DEFAUT:
        session.add(Lien(family_code=family_code, label=label))
    session.commit()


def seed(session: Session):
    if session.exec(select(Member)).first():
        return
    familles = [
        ("fam-durand", "Durand", [
            ("maman@durand.fr", "Maman", "mère", True, "durand"),
            ("lea@durand.fr", "Lea", "fille", False, "lea"),
            ("emma@durand.fr", "Emma", "fille", False, "emma"),
            ("tom@durand.fr", "Tom", "fils", False, "tom")]),
        ("fam-martin", "Martin", [
            ("papa@martin.fr", "Papa", "père", True, "martin"),
            ("chloe@martin.fr", "Chloe", "fille", False, "chloe"),
            ("hugo@martin.fr", "Hugo", "fils", False, "hugo")]),
    ]
    taches = {"fam-durand": ["Ranger sa chambre", "Faire ses devoirs", "Sortir les poubelles"],
              "fam-martin": ["Promener le chien", "Mettre la table"]}
    for code, fname, people in familles:
        seed_liens(session, code)
        objs, admin = [], None
        for email, name, lien, is_admin, pw in people:
            m = Member(email=email, name=name, lien=lien, is_admin=is_admin,
                       family_code=code, family_name=fname, password_hash=hash_password(pw))
            session.add(m); session.commit(); session.refresh(m)
            objs.append(m)
            if is_admin:
                admin = m
        enfants = [m for m in objs if not m.is_admin]
        for i, e in enumerate(enfants):
            session.add(Task(family_code=code, title=taches[code][i % len(taches[code])],
                             member_id=e.id, created_by=admin.id))
        session.commit()


# --- Auth (email + mot de passe) ---
def current_member(authorization: Optional[str] = Header(None),
                   session: Session = Depends(get_session)) -> Member:
    token = (authorization or "").replace("Bearer ", "").strip()
    m = session.exec(select(Member).where(Member.token == token)).first() if token else None
    if not m:
        raise HTTPException(status_code=401, detail="Non connecté")
    return m


@app.post("/api/signup")
def signup(email: str, password: str, name: str, family: str, lien: str = "parent",
           session: Session = Depends(get_session)):
    if session.exec(select(Member).where(Member.email == email.lower())).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    code = "fam-" + secrets.token_hex(4)
    seed_liens(session, code)
    m = Member(email=email.lower(), name=name, lien=lien, is_admin=True,
               family_code=code, family_name=family,
               password_hash=hash_password(password), token=secrets.token_hex(16))
    session.add(m); session.commit(); session.refresh(m)
    return {"token": m.token, **public_member(m)}


@app.post("/api/login")
def login(email: str, password: str, session: Session = Depends(get_session)):
    m = session.exec(select(Member).where(Member.email == email.lower())).first()
    if not m or m.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    m.token = secrets.token_hex(16)
    session.add(m); session.commit()
    return {"token": m.token, **public_member(m)}


@app.get("/api/health")
def health():
    return {"status": "ok"}
@app.get("/api/me")
def me(me: Member = Depends(current_member)):
    """Qui suis-je ? Renvoie le membre connecté, sans son empreinte de mot de passe."""
    return {"id": me.id, "email": me.email, "name": me.name, "lien": me.lien,
            "is_admin": me.is_admin, "family_code": me.family_code}


@app.post("/api/logout")
def logout(me: Member = Depends(current_member),
           session: Session = Depends(get_session)):
    """Se déconnecter : on efface le jeton côté serveur.

    Effacer le jeton du navigateur ne suffit pas : tant que le serveur
    l'accepte encore, quelqu'un qui l'aurait intercepté pourrait s'en servir.
    Ici on le supprime pour de bon — l'ancien jeton ne vaut plus rien.
    """
    me.token = None
    session.add(me)
    session.commit()
    return {"ok": True}


# --- Liste (modifiable) des liens de parenté ---
@app.get("/api/liens")
def list_liens(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    liens = session.exec(select(Lien).where(Lien.family_code == me.family_code)).all()
    return [l.label for l in liens]


@app.post("/api/liens")
def add_lien(label: str, me: Member = Depends(current_member),
             session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut modifier les liens")
    existing = session.exec(select(Lien).where(
        Lien.family_code == me.family_code, Lien.label == label)).first()
    if not existing and label.strip():
        session.add(Lien(family_code=me.family_code, label=label.strip()))
        session.commit()
    return list_liens(me, session)


# --- Comptes de la famille (l'admin crée / supprime) ---
@app.get("/api/members")
def list_members(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    membres = session.exec(select(Member).where(Member.family_code == me.family_code)).all()
    return [public_member(m) for m in membres]


@app.post("/api/members")
def add_member(email: str, password: str, name: str, lien: str = "", is_admin: bool = False,
               me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut créer des comptes")
    if session.exec(select(Member).where(Member.email == email.lower())).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    m = Member(email=email.lower(), name=name, lien=lien, is_admin=is_admin,
               family_code=me.family_code, family_name=me.family_name,
               password_hash=hash_password(password))
    session.add(m); session.commit(); session.refresh(m)
    return public_member(m)


@app.delete("/api/members/{member_id}")
def delete_member(member_id: int, me: Member = Depends(current_member),
                  session: Session = Depends(get_session)):
    if not me.is_admin:
        raise HTTPException(status_code=403, detail="Seul l'admin peut supprimer un compte")
    m = session.get(Member, member_id)
    if not m or m.family_code != me.family_code:
        raise HTTPException(status_code=404, detail="introuvable")
    if m.id == me.id:
        raise HTTPException(status_code=400, detail="Tu ne peux pas supprimer ton propre compte")
    tasks = session.exec(select(Task).where(
        (Task.member_id == m.id) | (Task.created_by == m.id))).all()
    for t in tasks:
        session.delete(t)
    session.commit()
    session.delete(m)
    session.commit()
    return {"ok": True}


# --- Tâches ---
@app.get("/api/tasks")
def my_tasks(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    return session.exec(select(Task).where(
        Task.family_code == me.family_code, Task.member_id == me.id)).all()


@app.get("/api/tasks/famille")
def family_tasks(me: Member = Depends(current_member), session: Session = Depends(get_session)):
    return session.exec(select(Task).where(Task.family_code == me.family_code)).all()


@app.post("/api/tasks")
def add_task(title: str, member_id: Optional[int] = None,
             me: Member = Depends(current_member), session: Session = Depends(get_session)):
    assignee = member_id if (member_id is not None and me.is_admin) else me.id
    task = Task(family_code=me.family_code, title=title, member_id=assignee, created_by=me.id)
    session.add(task); session.commit(); session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: int, me: Member = Depends(current_member),
                session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if not task or task.family_code != me.family_code:
        raise HTTPException(status_code=404, detail="introuvable")
    task.done = not task.done
    session.add(task); session.commit(); session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, me: Member = Depends(current_member),
                session: Session = Depends(get_session)):
    task = session.get(Task, task_id)
    if task and task.family_code == me.family_code:
        session.delete(task); session.commit()
    return {"ok": True}
