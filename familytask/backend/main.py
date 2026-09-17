import base64  # Importe l'encodage utilisé dans le token.
import binascii  # Importe l'erreur de décodage base64.
import hmac  # Importe la comparaison sécurisée des hash.
import hashlib  # Importe l'algorithme de hachage SHA-256.
import json  # Importe la sérialisation des informations du token.
import os  # Importe les fonctions d'accès aux variables d'environnement.
import re  # Importe les expressions régulières utilisées pour détecter un lien dans le message.
import secrets  # Importe la génération de valeurs aléatoires sécurisées.
import unicodedata  # Importe la normalisation des accents pour rechercher un prénom.
from typing import Optional  # Importe le type utilisé pour l'identifiant optionnel.

import httpx  # Importe le client HTTP asynchrone utilisé pour appeler GitHub Models.
from fastapi import Depends, FastAPI, HTTPException  # Importe FastAPI, les dépendances et les erreurs HTTP.
from fastapi.middleware.cors import CORSMiddleware  # Importe le middleware qui autorise les requêtes du front-end.
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # Importe la lecture des tokens Bearer.
from sqlalchemy import inspect, text  # Importe les outils utilisés pour vérifier et compléter la base existante.
from sqlmodel import Field, SQLModel, Session, create_engine, select  # Importe les outils de modèle, de session, de connexion et de requête SQL.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///familytask.db")  # Récupère l'adresse de la base de données.
if DATABASE_URL.startswith("postgres://"):  # Render peut fournir l'ancien préfixe PostgreSQL.
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)  # Utilise le schéma attendu par SQLAlchemy.
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "familytask-dev-secret")  # Récupère la clé secrète utilisée pour signer les tokens.
ASSISTANT_TOOLS = [  # Déclare les outils que le modèle peut utiliser.
    {
        "type": "function",
        "function": {
            "name": "ajouter_tache",
            "description": "Ajoute une tâche à la liste d'une personne de la famille.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titre": {"type": "string", "description": "Le titre de la tâche."},
                    "personne": {"type": "string", "description": "Le prénom de la personne responsable."},
                },
                "required": ["titre", "personne"],
                "additionalProperties": False,
            },
        },
    }
]  # Conserve la définition au format attendu par l'API OpenAI.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}  # Configure SQLite pour FastAPI si nécessaire.
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)  # Crée le moteur de connexion à la base.


class Task(SQLModel, table=True):  # Déclare le modèle de tâche comme table SQL.
    id: Optional[int] = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement.
    title: str  # Définit le titre textuel de la tâche.
    done: bool = False  # Définit l'état de la tâche avec une valeur par défaut à False.
    member_id: Optional[int] = Field(default=None, foreign_key="member.id", index=True)  # Rattache la tâche au membre auquel elle est assignée.


class Member(SQLModel, table=True):  # Déclare le modèle de membre comme table SQL.
    id: Optional[int] = Field(default=None, primary_key=True)  # Définit l'identifiant entier généré automatiquement.
    email: str = Field(index=True, unique=True)  # Définit l'adresse e-mail unique et indexée du membre.
    name: str  # Définit le nom du membre.
    lien: str  # Définit le lien ou le rôle du membre dans la famille.
    is_admin: bool = False  # Définit les droits d'administrateur, désactivés par défaut.
    family_code: str = Field(index=True)  # Définit le code de famille indexé du membre.
    password_hash: str  # Définit le mot de passe enregistré sous forme de hash.
    token: str  # Définit le jeton d'authentification du membre.


class Lien(SQLModel, table=True):  # Déclare la liste des liens de parenté d'une famille.
    id: Optional[int] = Field(default=None, primary_key=True)  # Définit l'identifiant du lien.
    name: str  # Définit le nom du lien de parenté.
    family_code: str = Field(index=True)  # Rattache le lien à une famille précise.


def hash_password(pw: str) -> str:  # Déclare la fonction de hachage du mot de passe.
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()  # Retourne le hash SHA-256 du mot de passe.


def normalize_text(value: str) -> str:  # Normalise un texte pour comparer les prénoms sans accents ni casse.
    normalized = unicodedata.normalize("NFD", value)  # Décompose les caractères accentués.
    return "".join(character for character in normalized if unicodedata.category(character) != "Mn").casefold().strip()  # Retire les accents et uniformise le texte.


def ambiguous_link_reply(message: str, family_members: list[Member]) -> Optional[str]:  # Recherche un lien ambigu dans le message brut.
    normalized_message = normalize_text(message)  # Normalise uniquement pour comparer le lien sans modifier le message utilisateur.
    members_by_link = {}  # Regroupe les membres par lien de parenté.
    for member in family_members:  # Parcourt les membres de la famille connectée.
        normalized_link = normalize_text(member.lien)  # Normalise le lien pour le regroupement et la détection.
        if normalized_link:  # Ignore les membres sans lien renseigné.
            members_by_link.setdefault(normalized_link, []).append(member)  # Ajoute le membre au groupe correspondant.
    for normalized_link, members in members_by_link.items():  # Recherche le premier lien présent dans le message.
        link_pattern = rf"(?<!\w){re.escape(normalized_link)}s?(?!\w)"  # Accepte le singulier et le pluriel du lien.
        if len(members) > 1 and re.search(link_pattern, normalized_message):  # Vérifie que le lien est mentionné et ambigu.
            display_link = members[0].lien if members[0].lien.endswith("s") else f"{members[0].lien}s"  # Forme le libellé pluriel de la question.
            names = ", ".join(member.name for member in members)  # Prépare la liste des personnes à départager.
            return f"Il y a plusieurs {display_link} ({names}). Pour qui ?"  # Demande explicitement le prénom cible.
    return None  # Poursuit le traitement normal lorsqu'aucun lien ambigu n'est détecté.


def create_token(member: Member) -> str:  # Crée un token signé contenant les informations nécessaires du membre.
    header = {"alg": "HS256", "typ": "JWT"}  # Décrit le format et l'algorithme du token.
    payload = {"id": member.id, "name": member.name, "lien": member.lien, "is_admin": member.is_admin, "nonce": secrets.token_urlsafe(16)}  # Place les informations du membre et une valeur unique dans le token.
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode("utf-8")).rstrip(b"=").decode("ascii")  # Encode une partie du token sans caractères inutiles.
    unsigned_token = f"{encode(header)}.{encode(payload)}"  # Assemble l'en-tête et les informations du token.
    signature = hmac.new(TOKEN_SECRET.encode("utf-8"), unsigned_token.encode("ascii"), hashlib.sha256).digest()  # Signe le token avec la clé secrète.
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")  # Encode la signature pour le transport HTTP.
    return f"{unsigned_token}.{encoded_signature}"  # Retourne le token complet.


def token_has_member_claims(token: str, member: Member) -> bool:  # Vérifie que le token contient les quatre informations obligatoires.
    try:  # Protège le décodage contre les tokens mal formés.
        token_parts = token.split(".")  # Sépare les trois parties du token signé.
        if len(token_parts) != 3:  # Vérifie que le token possède son en-tête, ses informations et sa signature.
            return False  # Refuse un token incomplet.
        unsigned_token = f"{token_parts[0]}.{token_parts[1]}"  # Reconstitue la partie signée du token.
        expected_signature = hmac.new(TOKEN_SECRET.encode("utf-8"), unsigned_token.encode("ascii"), hashlib.sha256).digest()  # Recalcule la signature attendue.
        provided_signature = base64.urlsafe_b64decode(token_parts[2] + "=" * (-len(token_parts[2]) % 4))  # Décode la signature reçue.
        if not hmac.compare_digest(expected_signature, provided_signature):  # Vérifie que le token n'a pas été modifié.
            return False  # Refuse une signature invalide.
        payload = token_parts[1]  # Récupère la partie contenant les informations du membre.
        payload += "=" * (-len(payload) % 4)  # Restaure le remplissage base64 si nécessaire.
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))  # Décode les informations du token.
    except (IndexError, ValueError, binascii.Error, json.JSONDecodeError):  # Intercepte les erreurs de format du token.
        return False  # Refuse un token illisible.
    return (
        claims.get("id") == member.id
        and claims.get("name") == member.name
        and claims.get("lien") == member.lien
        and claims.get("is_admin") is member.is_admin
    )  # Refuse le token si une information obligatoire manque ou ne correspond pas.


class TaskCreate(SQLModel):  # Déclare le modèle des données nécessaires à la création d'une tâche.
    title: str  # Définit le titre reçu dans le corps de la requête.
    member_id: Optional[int] = None  # Permet à un administrateur de choisir un autre membre de sa famille.


class SignupRequest(SQLModel):  # Déclare les données nécessaires à la création du premier membre.
    email: str  # Définit l'adresse e-mail du membre.
    password: str  # Définit le mot de passe reçu avant son hachage.
    name: str  # Définit le nom du membre.
    family: str  # Définit le nom fourni pour la famille.
    lien: str  # Définit le lien de parenté choisi par le membre.


class LoginRequest(SQLModel):  # Déclare les données nécessaires à la connexion.
    email: str  # Définit l'adresse e-mail utilisée pour se connecter.
    password: str  # Définit le mot de passe à vérifier.


class TokenResponse(SQLModel):  # Déclare la réponse contenant un token d'authentification.
    token: str  # Définit le token renvoyé au client.


class MemberPublic(SQLModel):  # Déclare les informations publiques d'un membre.
    id: Optional[int]  # Définit l'identifiant du membre.
    email: str  # Définit l'adresse e-mail du membre.
    name: str  # Définit le nom du membre.
    lien: str  # Définit le lien de parenté du membre.
    is_admin: bool  # Définit les droits d'administrateur du membre.
    family_code: str  # Définit le code de famille du membre.


class LienCreate(SQLModel):  # Déclare les données nécessaires à la création d'un lien.
    name: str  # Définit le nom du nouveau lien de parenté.


class MemberCreate(SQLModel):  # Déclare les données nécessaires à la création d'un membre par un admin.
    email: str  # Définit l'adresse e-mail du nouveau membre.
    password: str  # Définit le mot de passe avant son hachage.
    name: str  # Définit le prénom ou nom affiché du nouveau membre.
    lien: str  # Définit le lien de parenté du nouveau membre.
    is_admin: bool = False  # Définit les droits admin, désactivés par défaut.


security = HTTPBearer(auto_error=False)  # Configure la lecture facultative d'un token Bearer.


def get_current_member(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Member:  # Recherche le membre correspondant au token fourni.
    if credentials is None:  # Vérifie qu'un token a bien été fourni.
        raise HTTPException(status_code=401, detail="Authentification requise.")  # Refuse la requête sans authentification.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        member = session.exec(select(Member).where(Member.token == credentials.credentials)).first()  # Recherche le membre par son token.
    if member is None:  # Vérifie que le token correspond à un membre.
        raise HTTPException(status_code=401, detail="Token invalide.")  # Refuse un token inconnu.
    if not token_has_member_claims(credentials.credentials, member):  # Vérifie que le token contient toutes les informations attendues.
        raise HTTPException(status_code=401, detail="Token incomplet ou invalide.")  # Refuse un token sans id, nom, lien ou droits d'administration.
    return member  # Renvoie le membre authentifié.


def ensure_task_member_column():  # Ajoute la colonne member_id aux bases créées avant l'authentification.
    columns = {column["name"] for column in inspect(engine).get_columns("task")}  # Récupère les colonnes actuelles de la table Task.
    if "member_id" not in columns:  # Vérifie si la colonne d'affectation est absente.
        with engine.begin() as connection:  # Ouvre une transaction de migration.
            connection.execute(text("ALTER TABLE task ADD COLUMN member_id INTEGER"))  # Ajoute la colonne sans supprimer les anciennes tâches.
            connection.execute(text("CREATE INDEX ix_task_member_id ON task (member_id)"))  # Ajoute l'index nécessaire aux recherches par membre.


app = FastAPI(title="FamilyTask")  # Crée l'application FastAPI.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])  # Autorise les requêtes du front-end.


@app.on_event("startup")  # Demande l'exécution de la fonction au démarrage de l'application.
def create_tables():  # Déclare la fonction de création des tables.
    SQLModel.metadata.create_all(engine)  # Crée la table Task si elle n'existe pas encore.
    ensure_task_member_column()  # Complète une ancienne table Task si nécessaire.


@app.get("/")  # Déclare la route racine de l'API.
def home():  # Déclare la fonction qui répond à la route racine.
    return {"message": "FamilyTask API"}  # Retourne le message d'accueil de l'API.


@app.get("/api/health")  # Déclare la route de vérification de santé.
def health():  # Déclare la fonction qui répond à la vérification de santé.
    return {"status": "ok"}  # Retourne l'état opérationnel de l'API.


@app.post("/api/assistant")  # Déclare la route de conversation avec l'assistant.
async def assistant(message: str, current_member: Member = Depends(get_current_member)):  # Reçoit le message et vérifie le membre connecté.
    ai_token = os.getenv("AI_TOKEN")  # Récupère la clé GitHub Models depuis l'environnement.
    if not ai_token:  # Vérifie que la clé nécessaire à l'appel est configurée.
        return {"reply": "L'assistant IA n'est pas configuré : la clé AI_TOKEN est manquante."}  # Informe clairement que la clé manque.
    if not message.strip():  # Vérifie que le message contient du texte utile.
        raise HTTPException(status_code=422, detail="Le message ne peut pas être vide.")  # Refuse une question vide.

    with Session(engine) as session:  # Ouvre une session pour préparer le contexte familial.
        family_members = session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()  # Charge les membres de la famille connectée.
    link_reply = ambiguous_link_reply(message, family_members)  # Contrôle le message brut avant tout appel au modèle.
    if link_reply is not None:  # Vérifie si le message désigne plusieurs personnes par le même lien.
        return {"reply": link_reply}  # Demande le prénom sans laisser le modèle deviner.
    family_roster = ", ".join(f"{member.name} ({member.lien})" for member in family_members)  # Prépare la liste lisible pour le modèle.

    payload = {  # Prépare le corps au format compatible avec l'API OpenAI.
        "model": "openai/gpt-4o-mini",  # Sélectionne le modèle demandé.
        "messages": [
            {"role": "system", "content": f"Tu es l'assistant d'une famille. Membres disponibles : {family_roster}. Si le message demande d'ajouter ou de noter une tâche, appelle toujours ajouter_tache avec le titre dans titre et le prénom exact dans personne. Par exemple, 'vaisselle pour Léa' devient titre='Vaisselle' et personne='Léa'."},  # Donne au modèle la règle d'utilisation de l'outil.
            {"role": "user", "content": message},  # Transmet le message de l'utilisateur.
        ],
        "tools": ASSISTANT_TOOLS,  # Donne au modèle accès à l'outil d'ajout de tâche.
    }
    headers = {"Authorization": f"Bearer {ai_token}", "Content-Type": "application/json"}  # Ajoute la clé dans l'en-tête Bearer.
    try:  # Encadre l'appel réseau pour renvoyer une erreur API compréhensible.
        async with httpx.AsyncClient(timeout=30.0) as client:  # Ouvre un client HTTP asynchrone avec un délai raisonnable.
            response = await client.post("https://models.github.ai/inference/chat/completions", headers=headers, json=payload)  # Appelle GitHub Models.
        response.raise_for_status()  # Transforme une erreur HTTP distante en exception.
        response_data = response.json()  # Décode la réponse au format OpenAI.
        assistant_message = response_data["choices"][0]["message"]  # Récupère le message OpenAI retourné par le modèle.
        tool_calls = assistant_message.get("tool_calls") or []  # Récupère les appels d'outils éventuels.
        parsed_tool_call = None  # Prépare la réponse décodée de l'outil.
        if tool_calls:  # Traite le premier appel d'outil renvoyé par le modèle.
            tool_call = tool_calls[0]  # Sélectionne l'appel demandé.
            function = tool_call.get("function", {})  # Récupère les détails de la fonction.
            arguments = function.get("arguments", "{}")  # Récupère les arguments, souvent fournis comme chaîne JSON.
            if isinstance(arguments, str):  # Vérifie si les arguments doivent être décodés.
                arguments = json.loads(arguments)  # Transforme la chaîne JSON en dictionnaire Python.
            if not isinstance(arguments, dict):  # Vérifie que les arguments décodés ont la bonne structure.
                raise ValueError("Les arguments de l'outil doivent être un objet JSON.")  # Refuse des arguments mal formés.
            parsed_tool_call = {"name": function.get("name"), "arguments": arguments}  # Conserve le nom et les arguments décodés.
        answer = assistant_message.get("content") or ""  # Récupère le texte quand le modèle en fournit un.
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as error:  # Intercepte les erreurs réseau et de format.
        raise HTTPException(status_code=502, detail="Le service de l'assistant est indisponible.") from error  # Masque les détails internes et signale l'échec distant.
    if parsed_tool_call is not None and parsed_tool_call["name"] == "ajouter_tache":  # Exécute l'outil d'ajout de tâche demandé par le modèle.
        arguments = parsed_tool_call["arguments"]  # Récupère les arguments déjà décodés.
        title = str(arguments.get("titre", "")).strip()  # Récupère le titre de la tâche.
        person_name = str(arguments.get("personne", "")).strip()  # Récupère le prénom du responsable.
        if not title or not person_name:  # Vérifie que les deux arguments obligatoires sont présents.
            return {"reply": "Il me faut un titre et une personne pour ajouter la tâche."}  # Demande les informations manquantes.
        with Session(engine) as session:  # Ouvre une session dans la base de données.
            family_members = session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()  # Charge uniquement les membres de la famille connectée.
            matching_members = [member for member in family_members if normalize_text(member.name) == normalize_text(person_name)]  # Recherche le prénom sans tenir compte des majuscules ni des accents.
            if not matching_members:  # Vérifie qu'une personne correspond au prénom demandé.
                return {"reply": f"Je ne trouve pas {person_name} dans ta famille."}  # Signale que la personne est inconnue.
            if len(matching_members) > 1:  # Vérifie que le prénom désigne une seule personne.
                return {"reply": f"Plusieurs membres s'appellent {person_name}. Peux-tu préciser ?"}  # Évite une affectation ambiguë.
            target_member = matching_members[0]  # Sélectionne la personne responsable de la tâche.
            task = Task(title=title, done=False, member_id=target_member.id)  # Crée la tâche pour cette personne.
            session.add(task)  # Ajoute la tâche à la session.
            session.commit()  # Enregistre la tâche dans la base.
            target_name = target_member.name  # Conserve le nom avant la fermeture de la session.
        return {"reply": f"Tâche « {title} » ajoutée pour {target_name}.", "tool_call": parsed_tool_call}  # Confirme l'affectation réalisée.

    result = {"reply": answer}  # Prépare la réponse textuelle de l'assistant.
    if parsed_tool_call is not None:  # Ajoute l'appel d'outil décodé s'il a été demandé.
        result["tool_call"] = parsed_tool_call  # Rend les arguments structurés disponibles pour la suite du traitement.
    return result  # Renvoie la réponse de l'assistant et, si besoin, son outil demandé.


@app.post("/api/signup", response_model=TokenResponse)  # Déclare la route d'inscription du premier membre d'une famille.
def signup(signup_data: SignupRequest):  # Reçoit les informations du nouveau membre.
    if not signup_data.family.strip():  # Vérifie qu'un nom de famille a été fourni.
        raise HTTPException(status_code=422, detail="La famille ne peut pas être vide.")  # Refuse une famille sans nom.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        existing_member = session.exec(select(Member).where(Member.email == signup_data.email)).first()  # Recherche un compte utilisant déjà cet e-mail.
        if existing_member is not None:  # Vérifie que l'adresse e-mail est disponible.
            raise HTTPException(status_code=409, detail="Cette adresse e-mail est déjà utilisée.")  # Signale le conflit d'adresse.
        member = Member(  # Prépare le premier membre de la nouvelle famille.
            email=signup_data.email,  # Enregistre l'adresse e-mail.
            name=signup_data.name,  # Enregistre le nom du membre.
            lien=signup_data.lien,  # Enregistre le lien de parenté choisi.
            is_admin=True,  # Accorde les droits d'administrateur au premier membre.
            family_code=secrets.token_urlsafe(8),  # Génère le code unique de la famille.
            password_hash=hash_password(signup_data.password),  # Enregistre uniquement le hash du mot de passe.
            token="",  # Réserve le champ avant de connaître l'identifiant généré.
        )
        session.add(member)  # Ajoute le membre à la session.
        session.commit()  # Enregistre le membre dans la base de données.
        session.refresh(member)  # Recharge le membre enregistré.
        member.token = create_token(member)  # Génère le token avec l'identifiant réel et les informations du membre.
        session.add(member)  # Ajoute le token signé à la session.
        session.commit()  # Enregistre le token signé dans la base de données.
        token = member.token  # Conserve le token avant la fermeture de la session.
    return TokenResponse(token=token)  # Renvoie le token de connexion.


@app.post("/api/login", response_model=TokenResponse)  # Déclare la route de connexion d'un membre.
def login(login_data: LoginRequest):  # Reçoit l'e-mail et le mot de passe du membre.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        member = session.exec(select(Member).where(Member.email == login_data.email)).first()  # Recherche le membre par son e-mail.
        if member is None or not hmac.compare_digest(member.password_hash, hash_password(login_data.password)):  # Compare les hash avec un message d'erreur neutre.
            raise HTTPException(status_code=401, detail="Identifiants invalides.")  # Refuse l'e-mail ou le mot de passe incorrect.
        member.token = create_token(member)  # Génère un nouveau token contenant les informations du membre.
        session.add(member)  # Ajoute la modification à la session.
        session.commit()  # Enregistre le nouveau token.
        session.refresh(member)  # Recharge le membre modifié.
        token = member.token  # Conserve le token avant la fermeture de la session.
    return TokenResponse(token=token)  # Renvoie le nouveau token.


@app.get("/api/me", response_model=MemberPublic)  # Déclare la route qui renvoie le membre connecté sans son hash.
def get_me(current_member: Member = Depends(get_current_member)):  # Reçoit le membre identifié par son token.
    return current_member  # Renvoie uniquement les informations publiques du membre.


@app.post("/api/logout")  # Déclare la route de déconnexion du membre connecté.
def logout(current_member: Member = Depends(get_current_member)):  # Reçoit le membre identifié par son token.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        member = session.get(Member, current_member.id)  # Recharge le membre dans la session active.
        member.token = ""  # Efface le token du membre en base.
        session.add(member)  # Ajoute la modification à la session.
        session.commit()  # Enregistre la déconnexion.
    return {"message": "Déconnexion réussie."}  # Confirme la déconnexion.


@app.get("/api/tasks", response_model=list[Task])  # Renvoie les tâches assignées au membre connecté.
def list_tasks(current_member: Member = Depends(get_current_member)):  # Reçoit le membre connecté grâce à son token.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        tasks = session.exec(select(Task).where(Task.member_id == current_member.id)).all()  # Sélectionne uniquement les tâches du membre connecté.
    return tasks  # Renvoie les tâches sous forme de liste.


@app.get("/api/members", response_model=list[MemberPublic])  # Expose les membres de la famille connectée dans OpenAPI.
def list_members(current_member: Member = Depends(get_current_member)):  # Reçoit le membre connecté grâce à son token.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        members = session.exec(select(Member).where(Member.family_code == current_member.family_code)).all()  # Sélectionne uniquement les membres de sa famille.
    return members  # Renvoie les membres sous forme de liste.


@app.post("/api/members", response_model=MemberPublic)  # Crée un membre dans la famille de l'administrateur connecté.
def create_member(member_data: MemberCreate, current_member: Member = Depends(get_current_member)):  # Reçoit le nouveau membre et l'administrateur connecté.
    if not current_member.is_admin:  # Vérifie que seul un administrateur peut créer un compte.
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de la famille.")  # Refuse l'accès aux autres membres.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        existing_member = session.exec(select(Member).where(Member.email == member_data.email)).first()  # Recherche un compte utilisant déjà cet e-mail.
        if existing_member is not None:  # Vérifie que l'adresse e-mail est disponible.
            raise HTTPException(status_code=409, detail="Cette adresse e-mail est déjà utilisée.")  # Signale le conflit d'adresse.
        member = Member(email=member_data.email, name=member_data.name, lien=member_data.lien, is_admin=member_data.is_admin, family_code=current_member.family_code, password_hash=hash_password(member_data.password), token="")  # Prépare le nouveau membre de la famille.
        session.add(member)  # Ajoute le membre à la session.
        session.commit()  # Enregistre le membre pour générer son identifiant.
        session.refresh(member)  # Recharge le membre avec son identifiant.
        member.token = create_token(member)  # Génère un token initial contenant les informations du membre.
        session.add(member)  # Ajoute le token au membre.
        session.commit()  # Enregistre le token initial.
        session.refresh(member)  # Recharge le membre avant de le renvoyer.
    return member  # Renvoie les informations publiques du membre créé.


@app.delete("/api/members/{member_id}")  # Supprime un membre et ses tâches.
def delete_member(member_id: int, current_member: Member = Depends(get_current_member)):  # Reçoit l'identifiant et l'administrateur connecté.
    if not current_member.is_admin:  # Vérifie que seul un administrateur peut supprimer un compte.
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de la famille.")  # Refuse l'accès aux autres membres.
    if member_id == current_member.id:  # Interdit à l'administrateur de supprimer son propre compte.
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte.")  # Maintient un administrateur dans sa famille.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        member = session.get(Member, member_id)  # Recherche le membre à supprimer.
        if member is None or member.family_code != current_member.family_code:  # Vérifie que le membre appartient à la famille.
            raise HTTPException(status_code=404, detail="Membre introuvable dans votre famille.")  # Refuse une cible inconnue ou extérieure.
        tasks = session.exec(select(Task).where(Task.member_id == member_id)).all()  # Sélectionne les tâches du membre.
        for task in tasks:  # Parcourt les tâches à supprimer.
            session.delete(task)  # Supprime chaque tâche liée au membre.
        session.delete(member)  # Supprime le compte du membre.
        session.commit()  # Enregistre la suppression du compte et de ses tâches.
    return {"message": "Membre et tâches supprimés.", "id": member_id}  # Confirme la suppression.


@app.get("/api/liens", response_model=list[Lien])  # Renvoie les liens de parenté de la famille connectée.
def list_liens(current_member: Member = Depends(get_current_member)):  # Reçoit le membre connecté grâce à son token.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        liens = session.exec(select(Lien).where(Lien.family_code == current_member.family_code)).all()  # Sélectionne les liens de sa famille.
    return liens  # Renvoie la liste des liens.


@app.post("/api/liens", response_model=Lien)  # Ajoute un lien de parenté à la famille connectée.
def create_lien(lien_data: LienCreate, current_member: Member = Depends(get_current_member)):  # Reçoit le lien et le membre connecté.
    if not current_member.is_admin:  # Vérifie que seul un administrateur peut modifier la liste.
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de la famille.")  # Refuse l'accès aux autres membres.
    if not lien_data.name.strip():  # Vérifie que le nom du lien n'est pas vide.
        raise HTTPException(status_code=422, detail="Le nom du lien ne peut pas être vide.")  # Refuse un lien sans nom.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        existing_lien = session.exec(select(Lien).where(Lien.name == lien_data.name, Lien.family_code == current_member.family_code)).first()  # Recherche un doublon dans la famille.
        if existing_lien is not None:  # Vérifie que le lien n'existe pas déjà.
            raise HTTPException(status_code=409, detail="Ce lien existe déjà dans la famille.")  # Signale le doublon.
        lien = Lien(name=lien_data.name.strip(), family_code=current_member.family_code)  # Prépare le nouveau lien de la famille.
        session.add(lien)  # Ajoute le lien à la session.
        session.commit()  # Enregistre le lien.
        session.refresh(lien)  # Recharge le lien avec son identifiant.
    return lien  # Renvoie le lien créé.


@app.get("/api/tasks/famille", response_model=list[Task])  # Renvoie toutes les tâches de la famille pour un administrateur.
def list_family_tasks(current_member: Member = Depends(get_current_member)):  # Reçoit le membre connecté grâce à son token.
    if not current_member.is_admin:  # Vérifie que le membre possède les droits d'administrateur.
        raise HTTPException(status_code=403, detail="Réservé à l'administrateur de la famille.")  # Refuse l'accès aux autres membres.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        tasks = session.exec(select(Task).join(Member).where(Member.family_code == current_member.family_code)).all()  # Sélectionne les tâches de tous les membres de la famille.
    return tasks  # Renvoie les tâches de la famille.


@app.post("/api/tasks", response_model=Task)  # Crée une tâche pour le membre connecté ou un membre de sa famille.
def create_task(task_data: TaskCreate, current_member: Member = Depends(get_current_member)):  # Reçoit la tâche et le membre connecté.
    if not task_data.title.strip():  # Vérifie que le titre contient au moins un caractère non blanc.
        raise HTTPException(status_code=422, detail="Le titre de la tâche ne peut pas être vide.")  # Refuse une tâche sans nom avec une erreur explicite.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        target_member = current_member  # Affecte par défaut la tâche au membre connecté.
        if task_data.member_id is not None:  # Vérifie si une affectation particulière a été demandée.
            if not current_member.is_admin:  # Vérifie que seul un administrateur peut affecter une autre personne.
                raise HTTPException(status_code=403, detail="Seul un administrateur peut affecter une tâche à un autre membre.")  # Refuse l'affectation par un membre ordinaire.
            target_member = session.get(Member, task_data.member_id)  # Recherche le membre choisi par l'administrateur.
            if target_member is None or target_member.family_code != current_member.family_code:  # Vérifie que la cible appartient à la famille.
                raise HTTPException(status_code=404, detail="Le membre choisi est introuvable dans votre famille.")  # Refuse une cible inconnue ou extérieure.
        task = Task(title=task_data.title, done=False, member_id=target_member.id)  # Crée une tâche rattachée à la bonne personne.
        session.add(task)  # Ajoute la nouvelle tâche à la session.
        session.commit()  # Enregistre la nouvelle tâche dans la base de données.
        session.refresh(task)  # Recharge la tâche pour obtenir son identifiant généré.
    return task  # Renvoie la tâche créée avec son identifiant.


@app.patch("/api/tasks/{task_id}", response_model=Task)  # Déclare une route qui bascule l'état d'une tâche.
def toggle_task(task_id: int, current_member: Member = Depends(get_current_member)):  # Reçoit la tâche et le membre connecté.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        task = session.get(Task, task_id)  # Recherche la tâche correspondant à l'identifiant reçu.
        if task is None:  # Vérifie qu'une tâche a bien été trouvée.
            raise HTTPException(status_code=404, detail=f"La tâche {task_id} est introuvable.")  # Renvoie une erreur explicite si la tâche n'existe pas.
        if task.member_id != current_member.id and not (current_member.is_admin and session.exec(select(Member).where(Member.id == task.member_id, Member.family_code == current_member.family_code)).first()):  # Vérifie que le membre peut modifier cette tâche.
            raise HTTPException(status_code=403, detail="Cette tâche ne vous est pas accessible.")  # Refuse une tâche d'une autre famille ou d'un autre membre non administrateur.
        task.done = not task.done  # Bascule l'état de la tâche entre vraie et fausse.
        session.add(task)  # Ajoute la tâche modifiée à la session.
        session.commit()  # Enregistre la modification dans la base de données.
        session.refresh(task)  # Recharge la tâche modifiée depuis la base de données.
    return task  # Renvoie la tâche modifiée.


@app.delete("/api/tasks/{task_id}")  # Déclare une route qui supprime une tâche.
def delete_task(task_id: int, current_member: Member = Depends(get_current_member)):  # Reçoit la tâche et le membre connecté.
    with Session(engine) as session:  # Ouvre une session SQLModel avec la base de données.
        task = session.get(Task, task_id)  # Recherche la tâche correspondant à l'identifiant reçu.
        if task is None:  # Vérifie qu'une tâche a bien été trouvée.
            raise HTTPException(status_code=404, detail=f"La tâche {task_id} est introuvable.")  # Renvoie une erreur explicite si la tâche n'existe pas.
        if task.member_id != current_member.id and not (current_member.is_admin and session.exec(select(Member).where(Member.id == task.member_id, Member.family_code == current_member.family_code)).first()):  # Vérifie que le membre peut supprimer cette tâche.
            raise HTTPException(status_code=403, detail="Cette tâche ne vous est pas accessible.")  # Refuse une tâche d'une autre famille ou d'un autre membre non administrateur.
        session.delete(task)  # Marque la tâche pour suppression de la base de données.
        session.commit()  # Enregistre définitivement la suppression.
    return {"message": "Tâche supprimée", "id": task_id}  # Renvoie une confirmation avec l'identifiant supprimé.
