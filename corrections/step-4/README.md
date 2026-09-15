# step-4 — corrigé de l'**atelier 3** (le back-end et la base)

**Contient :** les 5 routes de l'API (`/api/health`, plus lister, créer, cocher, supprimer),
le modèle `Task`, la connexion à PostgreSQL, et le front branché dessus.
Les tâches survivent au rechargement.

**Ne contient pas :** de comptes ni de familles. Tout le monde partage la même liste.

**À regarder en priorité :** la gestion des erreurs dans `backend/main.py` — un titre vide
renvoie un **422**, une tâche introuvable un **404**. Ce n'est pas un détail : renvoyer une
erreur avec un code 200 tromperait celui qui appelle l'API.

## Lancer ce dossier

```bash
docker compose up
```

Puis clique sur **Open in Browser** (ou onglet **PORTS** → ligne **5173** → 🌐).
Swagger, la documentation de l'API, est sur le port **8000**, chemin **`/docs`**.

> ⚠️ Ce dossier est un **corrigé** : il sert à comparer, pas à travailler dedans.
> Ton code à toi est dans `familytask/`.
