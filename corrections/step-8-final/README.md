# step-8-final — corrigé de l'**atelier 7**, et arrivée de la semaine

**Contient :** l'app complète, plus tout ce qu'il faut pour la mettre en ligne —
`render.yaml`, `frontend/src/api.js` qui lit `VITE_API_URL`, et `DEPLOIEMENT.md`.

C'est l'application finie : comptes, familles, rôles, base de données, tests, assistant IA.

**Le déploiement :** suis `DEPLOIEMENT.md`. Gratuit, via GitHub et Render.
Render te demandera la valeur de `AI_TOKEN` — c'est le même jeton que lundi.
Comme l'assistant appelle un modèle **en ligne**, il fonctionne aussi sur l'app déployée.

**Des comptes pour essayer :** voir `IDENTIFIANTS-TEST.md`.

## Lancer ce dossier

```bash
docker compose up
```

Puis clique sur **Open in Browser** (ou onglet **PORTS** → ligne **5173** → 🌐).
Swagger, la documentation de l'API, est sur le port **8000**, chemin **`/docs`**.

> ⚠️ Ce dossier est un **corrigé** : il sert à comparer, pas à travailler dedans.
> Ton code à toi est dans `familytask/`.
