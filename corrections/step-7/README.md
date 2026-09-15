# step-7 — corrigé de l'**atelier 6** (les tests)

**Contient :** tout `step-6`, plus `backend/test_main.py` et `pytest` dans les dépendances.

**Ne contient pas :** le déploiement.

**Lancer les tests :**

```bash
docker compose exec backend pytest -q
```

**À regarder en priorité :** comment un test crée une famille, obtient un jeton, crée une tâche
et vérifie qu'elle est bien là — sans jamais ouvrir l'app. Et le test qui vérifie qu'une requête
sans jeton reçoit bien un **401**.

> 🔑 Même remarque que pour `step-6` : l'assistant a besoin de `AI_TOKEN` pour répondre.

## Lancer ce dossier

```bash
docker compose up
```

Puis clique sur **Open in Browser** (ou onglet **PORTS** → ligne **5173** → 🌐).
Swagger, la documentation de l'API, est sur le port **8000**, chemin **`/docs`**.

> ⚠️ Ce dossier est un **corrigé** : il sert à comparer, pas à travailler dedans.
> Ton code à toi est dans `familytask/`.
