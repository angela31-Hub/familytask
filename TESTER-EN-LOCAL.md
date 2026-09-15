# Tester sur ton Mac, avec Docker

Le dossier `.devcontainer/` que tu vois ici **ne sert qu'à GitHub Codespaces**.
En local, il ne doit jamais être utilisé : c'est Docker Desktop qui fait tourner l'app,
directement, comme dans n'importe quel projet.

## Une fois pour toutes

Si VS Code t'a déjà proposé « Reopen in Container » et que tu as accepté :
**Cmd+Shift+P** → `Reopen Folder Locally`.

Pour qu'il ne le propose plus jamais, désactive l'extension **Dev Containers**
(onglet Extensions → chercher « Dev Containers » → Disable). Elle est inutile ici :
Codespaces tourne côté serveur et n'a pas besoin d'elle.

Le fichier `.vscode/settings.json` de ce dossier coupe déjà la détection automatique,
mais désactiver l'extension est la garantie la plus sûre.

## La clé de l'IA

Une seule fois, depuis ce dossier :

```bash
for d in familytask corrections/step-*; do echo 'AI_TOKEN=ton_jeton_github' > "$d/.env"; done
```

Docker Compose lit ce `.env` tout seul. Plus besoin d'`export`.
`.env` est dans le `.gitignore` : la clé ne partira jamais sur GitHub.

## La boucle, dossier par dossier

Ouvre VS Code **sur le dossier du step**, pas sur `app/` :

```bash
code ~/Downloads/SummerCamp/app/corrections/step-4
```

Puis, dans le terminal :

```bash
docker compose up --build
# tester sur http://localhost:5173, puis Ctrl+C
docker compose down -v
```

Un seul dossier à la fois : ils utilisent tous les ports 5173 et 8000.
Le `-v` efface le volume Postgres pour repartir sur une base propre.

## Ce que tu dois voir

| Dossier | Attendu | Le test |
|---|---|---|
| `familytask` | « Bienvenue ! 🎉 » | Rien d'autre : c'est le squelette |
| `corrections/step-2` | Identique | L'atelier 1 ne change que l'environnement |
| `corrections/step-3` | Champ + liste de tâches | Ajoute, coche, supprime. Recharge → **tout disparaît** (voulu) |
| `corrections/step-4` | Idem | Ajoute, recharge → **c'est toujours là** |
| `corrections/step-5` | Écran de connexion | `maman@durand.fr` / `durand`, puis `lea@durand.fr` / `lea` |
| `corrections/step-6` | Onglet Assistant | « ajoute la vaisselle pour Lea » → tâche chez Lea |
| `corrections/step-7` | Idem | `docker compose exec backend pytest -q` → vert |
| `corrections/step-8-final` | Idem | « ajoute le ménage pour ma fille » → « Lea ou Emma ? » |

## Si l'assistant ne répond pas

**« pas configuré »** → le `.env` du dossier est absent ou vide.
**« n'a pas répondu »** → la permission `models:read` du jeton est mal réglée.
