# step-5 — corrigé de l'**atelier 4** (comptes et connexion)

**Contient :** l'inscription, la connexion, la déconnexion, les jetons, le multi-tenant
(chaque famille son espace), les rôles admin, et les écrans `Login`, `Signup`,
`TasksView`, `FamilyView` avec vue-router.

**Ne contient pas :** l'assistant IA.

**À regarder en priorité :** la dépendance `current_member` dans `backend/main.py` —
c'est elle qui lit le jeton et refuse l'accès (401) sans lui. Et `frontend/src/api.js`,
qui ajoute le jeton à chaque appel sans que tu aies à y penser.

## Lancer ce dossier

```bash
docker compose up
```

Puis clique sur **Open in Browser** (ou onglet **PORTS** → ligne **5173** → 🌐).
Swagger, la documentation de l'API, est sur le port **8000**, chemin **`/docs`**.

> ⚠️ Ce dossier est un **corrigé** : il sert à comparer, pas à travailler dedans.
> Ton code à toi est dans `familytask/`.
