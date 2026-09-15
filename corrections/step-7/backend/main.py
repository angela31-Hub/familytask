import os
import re
import random
import hashlib
import secrets
import json
from typing import Optional

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select
import httpx

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
    name: str                                     # prénom (identifie la personne)
    lien: str = ""                                # lien de parenté (mère, fille, oncle…)
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
    member_id: Optional[int] = Field(default=None, foreign_key="member.id")
    created_by: Optional[int] = Field(default=None, foreign_key="member.id")


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


# --- Données de démo : 2 familles ---
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


# --- Liste (modifiable) des liens de parenté de la famille ---
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


# --- Comptes de la famille (l'admin crée les comptes) ---
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
    # On supprime d'abord ses tâches (assignées à lui OU créées par lui), puis on valide,
    # sinon la contrainte de clé étrangère bloque la suppression du membre.
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


TITRES_ALEATOIRES = [
    "Ranger le salon", "Sortir les poubelles", "Arroser les plantes",
    "Passer l'aspirateur", "Faire la vaisselle", "Promener le chien",
]


@app.post("/api/tasks")
def add_task(title: str, member_id: Optional[int] = None,
             me: Member = Depends(current_member), session: Session = Depends(get_session)):
    if not title.strip():
        title = random.choice(TITRES_ALEATOIRES)
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


# ---------------------------------------------------------------------------
#  Assistant IA : agent (function calling) + désambiguïsation des personnes
# ---------------------------------------------------------------------------
# Le "cerveau" de l'assistant est appelé en ligne via GitHub Models : une API
# gratuite, compatible OpenAI, incluse avec un simple compte GitHub.
# Avantages sur Ollama en local : rien à télécharger (plusieurs Go en moins),
# réponse quasi instantanée même sur un petit PC, et l'assistant continue de
# fonctionner une fois l'application déployée en ligne.
AI_URL = os.getenv("AI_URL", "https://models.github.ai/inference")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
AI_TOKEN = os.getenv("AI_TOKEN", "")

TOOLS = [
    {"type": "function", "function": {
        "name": "ajouter_tache",
        "description": "Ajoute une tache a la liste d'une personne. Mets dans 'personne' le PRENOM "
                       "si tu le connais, sinon le lien (ex: fille).",
        "parameters": {"type": "object", "properties": {
            "titre": {"type": "string"},
            "personne": {"type": "string", "description": "prenom ou lien, ex: Lea ou fille"},
            "jours": {"type": "array", "items": {"type": "string"}},
        }, "required": ["titre"]}}},
]


def _clean(p: str) -> str:
    p = (p or "").strip().lower()
    for det in ["à ", "a ", "aux ", "mes ", "ma ", "mon ", "les ", "la ", "le ", "de "]:
        if p.startswith(det):
            p = p[len(det):]
    return p.strip()


def _words(text):
    return re.findall(r"[a-zàâäéèêëïîôöùûüç]+", (text or "").lower())


def disambiguation_needed(message, family, session):
    """Regarde le message BRUT : si un lien y est cité (ex 'ma fille') et correspond à
    plusieurs personnes, sans qu'un prénom soit précisé, on renvoie la liste à départager."""
    members = session.exec(select(Member).where(Member.family_code == family)).all()
    words = _words(message)
    # Un prénom explicite est cité ? -> pas d'ambiguïté.
    if any(m.name.lower() in words for m in members):
        return None
    for label in {m.lien.lower() for m in members if m.lien}:
        base = label.rstrip("s")
        if label in words or base in words or (base + "s") in words:
            matches = [m for m in members if m.lien.lower() == label]
            if len(matches) > 1:
                return matches
    return None


def resolve_people(family, personne, session):
    """Retourne (liste_membres, ambigu). Prénom d'abord, sinon lien (peut être multiple)."""
    members = session.exec(select(Member).where(Member.family_code == family)).all()
    p = _clean(personne)
    if not p:
        return [], False
    by_name = [m for m in members if m.name.lower() == p]
    if not by_name:
        by_name = [m for m in members if p in m.name.lower() or m.name.lower() in p]
    if by_name:
        return by_name, len(by_name) > 1
    by_lien = [m for m in members if m.lien and (m.lien.lower() == p or m.lien.lower().rstrip("s") == p.rstrip("s"))]
    return by_lien, len(by_lien) > 1


@app.post("/api/assistant")
async def assistant(message: str, me: Member = Depends(current_member),
                    session: Session = Depends(get_session)):
    family = me.family_code
    roster = session.exec(select(Member).where(Member.family_code == family)).all()
    liste = ", ".join(f"{m.name} ({m.lien})" for m in roster)
    system = (f"Tu es l'assistant de la famille {me.family_name}. "
              f"La personne qui te parle est {me.name} ({me.lien}). "
              f"Membres de la famille : {liste}. "
              f"Pour ajouter une tache, appelle TOUJOURS l'outil ajouter_tache (ne demande pas de "
              f"confirmation) en mettant le PRENOM de la personne dans 'personne'. S'il n'y a qu'une "
              f"seule personne correspondant au lien demande, agis directement.")
    if not AI_TOKEN:
        return {"reply": "L'assistant IA n'est pas configure : il manque la cle "
                         "AI_TOKEN. Voir l'atelier 1, etape 3."}

    payload = {"model": AI_MODEL,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": message}],
               "tools": TOOLS, "stream": False}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{AI_URL}/chat/completions",
                headers={"Authorization": f"Bearer {AI_TOKEN}",
                         "Content-Type": "application/json"},
                json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception:
        return {"reply": "L'assistant IA n'a pas repondu. Verifie ta connexion "
                         "et ta cle AI_TOKEN, puis reessaie."}

    # Reponse au format OpenAI : le message est dans choices[0].message
    # (avec Ollama, il etait directement dans data["message"]).
    msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
    calls = msg.get("tool_calls") or []
    if not calls:
        return {"reply": msg.get("content", "(pas de reponse)")}

    # Garde-fou : même si le modèle a "deviné" un prénom, on vérifie l'ambiguïté sur le message brut.
    amb = disambiguation_needed(message, family, session)
    if amb:
        noms = ", ".join(m.name for m in amb)
        return {"reply": f"Il y a plusieurs {amb[0].lien}s ({noms}). Pour qui exactement ?"}

    done = []
    for call in calls:
        fn = call.get("function", {})
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        if fn.get("name") != "ajouter_tache":
            continue
        people, ambiguous = resolve_people(family, args.get("personne"), session)
        if ambiguous:
            noms = ", ".join(m.name for m in people)
            return {"reply": f"Il y a plusieurs personnes possibles : {noms}. Pour qui exactement ?"}
        targets = people if people else [me]
        jours = args.get("jours") or [None]
        for target in targets:
            for j in jours:
                titre = args.get("titre", "Nouvelle tache")
                if j:
                    titre = f"{titre} ({j})"
                session.add(Task(family_code=family, title=titre,
                                 member_id=target.id, created_by=me.id))
        session.commit()
        who = " et ".join(m.name for m in targets)
        done.append(f"\"{args.get('titre')}\" pour {who}")

    return {"reply": ("Ajouté : " + " ; ".join(done)) if done else "Rien à ajouter."}
