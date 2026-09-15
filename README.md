# FamilyTask — Summer Camp « Crée ton app avec l'IA »

Bienvenue ! Tu n'as **rien à installer** : tout se passe dans ton navigateur.

## Démarrer

1. **Use this template** → **Create a new repository** → nom : `familytask` → **Create**
2. Sur ton nouveau dépôt : **Code** → onglet **Codespaces** → **Create codespace on main**
3. Patiente 3 à 5 minutes, puis dans le terminal :

```bash
cd familytask
docker compose up
```

4. Clique sur **Open in Browser**.

## Les deux dossiers

| | |
|---|---|
| **`familytask/`** | **Ton** application. Tu travailles ici du lundi au vendredi. Ce que tu écris reste. |
| **`corrections/`** | Les versions terminées de chaque étape. À **lire** quand tu bloques, jamais à copier. |

## Chaque soir

```bash
git add .
git commit -m "Jour 2"
git push
docker compose down
```

Puis en bas à gauche : **Codespaces → Stop Current Codespace**.

Éteindre n'est pas supprimer : ton travail est conservé, tu reprends demain où tu en étais.

---

---

## Tester en local (facultatif)

Dans un codespace, la clé de l'IA est déjà fournie. Si tu veux faire tourner
l'app sur ta propre machine avec Docker, crée un fichier `.env` à côté du
`docker-compose.yml` :

```
AI_TOKEN=ton_jeton_github
```

Docker Compose le lit tout seul. Voir `.env.example`.
