import os  # Importe les fonctions d'accès aux variables d'environnement.
from typing import Optional  # Importe le type utilisé pour l'identifiant optionnel.

from fastapi import FastAPI, HTTPException  # Importe FastAPI et l'exception utilisée pour les erreurs HTTP.
from fastapi.middleware.cors import CORSMiddleware  # Importe le middleware qui autorise les requêtes du front-end.
from sqlmodel import Field, SQLModel, Session, create_engine, select  # Importe les outils de modèle, de session, de connexion et de requête SQL.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")  # Récupère l'adresse de la base de données.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}  # Configure SQLite pour FastAPI si nécessaire.
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)  # Crée le moteur de connexion à la base.


class Task(SQLModel, table=True):  # Déclare le modèle de tâche comme table SQL.
    id: Optional[int] = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement.
    title: str  # Définit le titre textuel de la tâche.
    done: bool = False  # Définit l'état de la tâche avec une valeur par défaut à False.


class TaskCreate(SQLModel):  # Déclare le modèle des données nécessaires à la création d'une tâche.
    title: str  # Définit le titre reçu dans le corps de la requête.


app = FastAPI(title="FamilyTask")  # Crée l'application FastAPI.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # Autorise les requêtes du front-end.


@app.on_event("startup")  # Demande l'exécution de la fonction au démarrage de l'application.
def create_tables():  # Déclare la fonction de création des tables.
    SQLModel.metadata.create_all(engine)  # Crée la table Task si elle n'existe pas encore.


@app.get("/")  # Déclare la route racine de l'API.
def home():  # Déclare la fonction qui répond à la route racine.
    return {"message": "FamilyTask API"}  # Retourne le message d'accueil de l'API.


@app.get("/api/health")  # Déclare la route de vérification de santé.
def health():  # Déclare la fonction qui répond à la vérification de santé.
    return {"status": "ok"}  # Retourne l'état opérationnel de l'API.


@app.get("/api/tasks", response_model=list[Task])  # Déclare une route qui expose le modèle Task dans la documentation OpenAPI.
def list_tasks():  # Déclare la fonction qui renvoie la liste des tâches.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        tasks = session.exec(select(Task)).all()  # Sélectionne toutes les lignes de la table Task.
    return tasks  # Renvoie les tâches sous forme de liste.


@app.post("/api/tasks", response_model=Task)  # Déclare une route qui crée une tâche et renvoie la tâche créée.
def create_task(task_data: TaskCreate):  # Reçoit le titre de la tâche dans le corps de la requête.
    if not task_data.title.strip():  # Vérifie que le titre contient au moins un caractère non blanc.
        raise HTTPException(status_code=422, detail="Le titre de la tâche ne peut pas être vide.")  # Refuse une tâche sans nom avec une erreur explicite.
    task = Task(title=task_data.title, done=False)  # Crée une tâche avec un état initial non terminée.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        session.add(task)  # Ajoute la nouvelle tâche à la session.
        session.commit()  # Enregistre la nouvelle tâche dans la base de données.
        session.refresh(task)  # Recharge la tâche pour obtenir son identifiant généré.
    return task  # Renvoie la tâche créée avec son identifiant.


@app.patch("/api/tasks/{task_id}", response_model=Task)  # Déclare une route qui bascule l'état d'une tâche.
def toggle_task(task_id: int):  # Reçoit l'identifiant de la tâche à modifier.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        task = session.get(Task, task_id)  # Recherche la tâche correspondant à l'identifiant reçu.
        if task is None:  # Vérifie qu'une tâche a bien été trouvée.
            raise HTTPException(status_code=404, detail=f"La tâche {task_id} est introuvable.")  # Renvoie une erreur explicite si la tâche n'existe pas.
        task.done = not task.done  # Bascule l'état de la tâche entre vraie et fausse.
        session.add(task)  # Ajoute la tâche modifiée à la session.
        session.commit()  # Enregistre la modification dans la base de données.
        session.refresh(task)  # Recharge la tâche modifiée depuis la base de données.
    return task  # Renvoie la tâche modifiée.


@app.delete("/api/tasks/{task_id}")  # Déclare une route qui supprime une tâche.
def delete_task(task_id: int):  # Reçoit l'identifiant de la tâche à supprimer.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        task = session.get(Task, task_id)  # Recherche la tâche correspondant à l'identifiant reçu.
        if task is None:  # Vérifie qu'une tâche a bien été trouvée.
            raise HTTPException(status_code=404, detail=f"La tâche {task_id} est introuvable.")  # Renvoie une erreur explicite si la tâche n'existe pas.
        session.delete(task)  # Marque la tâche pour suppression de la base de données.
        session.commit()  # Enregistre définitivement la suppression.
    return {"message": "Tâche supprimée", "id": task_id}  # Renvoie une confirmation avec l'identifiant supprimé.
