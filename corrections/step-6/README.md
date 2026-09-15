# step-6 — corrigé de l'**atelier 5** (l'assistant IA)

**Contient :** l'assistant intégré — la route `/api/assistant`, la déclaration de l'outil
`ajouter_tache`, la désambiguïsation (« ma fille » avec deux filles → il demande laquelle),
et le composant `ChatAssistant.vue` avec la dictée vocale.

**Ne contient pas :** les tests.

**À regarder en priorité :** dans `backend/main.py`, la boucle d'agent. Le modèle ne touche
jamais la base : il **demande** d'appeler `ajouter_tache`, et c'est le code qui exécute.

> 🔑 **Pour que l'assistant réponde**, il faut la clé `AI_TOKEN`.
> En codespace, c'est le secret que tu as créé à l'atelier 1 — rien à faire.
> En local, crée un fichier `.env` à côté du `docker-compose.yml` : `AI_TOKEN=ton_jeton`.

## Lancer ce dossier

```bash
docker compose up
```

Puis clique sur **Open in Browser** (ou onglet **PORTS** → ligne **5173** → 🌐).
Swagger, la documentation de l'API, est sur le port **8000**, chemin **`/docs`**.

> ⚠️ Ce dossier est un **corrigé** : il sert à comparer, pas à travailler dedans.
> Ton code à toi est dans `familytask/`.
