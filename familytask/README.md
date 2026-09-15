# familytask — ton application

**Ce dossier est presque vide, et c'est normal.**

Il contient le squelette de départ : un back-end de 10 lignes, un écran de bienvenue.
C'est **toi** qui vas le remplir, du lundi au vendredi.

```
familytask/
├── docker-compose.yml     ← la liste des boîtes à démarrer
├── backend/               ← ce qui décide (Python / FastAPI)
│   ├── main.py            ← ton code back-end
│   ├── requirements.txt
│   └── Dockerfile
└── frontend/              ← ce que tu vois (Vue.js)
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.vue        ← ton écran principal
        ├── main.js
        └── style.css
```

## Démarrer

```bash
docker compose up
```

Puis clique sur **Open in Browser**.

## Chaque soir

```bash
git add .
git commit -m "Jour 2"
git push
docker compose down
```

Puis en bas à gauche : **Codespaces → Stop Current Codespace**.

---

> Tu cherches l'application terminée ? Elle est dans `../corrections/step-8-final`.
> Regarde-la si tu veux voir où tu vas — mais ne la copie pas : ce qu'on recopie,
> on ne l'apprend pas.
