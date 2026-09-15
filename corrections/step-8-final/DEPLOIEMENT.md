# Déploiement — la to-do pas à pas (à faire par chaque personne)

Objectif : mettre **ton** app en ligne, gratuitement, avec un lien à partager.
Tout se fait dans le navigateur — **rien à installer**. Compte ~20-30 min.

> Ton app doit déjà marcher en local (étape 5). On part du dossier `step-8-final`.

## Partie A — Mettre ton code sur GitHub (sans rien installer)

1. Va sur **github.com** et connecte-toi (compte créé lundi).
2. Clique **New** (nouveau dépôt). Nom : `familytask`. Clique **Create repository**.
3. Sur la page du dépôt, clique le lien **« uploading an existing file »**.
4. **Glisse-dépose** tout le contenu du dossier `step-8-final` (les dossiers `backend`, `frontend` et le fichier `render.yaml`).
5. Clique **Commit changes**. ✅ Ton code est sur GitHub.

## Partie B — Déployer sur Render (gratuit)

6. Va sur **render.com**, clique **Get Started**, connecte-toi **avec GitHub**.
7. Clique **New +** puis **Blueprint**.
8. Choisis ton dépôt `familytask` puis **Connect**.
9. Render lit le fichier `render.yaml` et propose **3 services** (base, back, front). Clique **Apply**.
10. Patiente ~5-10 min (Render installe et construit tout). ☕

## Partie C — Ouvrir ton app en ligne

11. Dans Render, ouvre le service **familytask-front** et clique son adresse (`...onrender.com`).
12. 🎉 Ton app est **en ligne**. Copie le lien et partage-le.

## Bon à savoir (honnête)

- Le **1er chargement est lent** : les serveurs gratuits « s'endorment » après inactivité. C'est normal.
- La **base gratuite** Render expire après ~1 mois : parfait pour une démo / un portfolio.
- **L'assistant IA fonctionne aussi en ligne.** Il appelle un modèle hébergé (GitHub Models), pas un modèle local : il n'y a donc rien de plus à faire. Render te demandera simplement la valeur de `AI_TOKEN` au moment du déploiement — c'est le même jeton que celui de lundi. Ta famille peut vraiment lui parler.

## Si le temps manque (côté formateur)

Déployer à 8 peut être long. Plan B : **le formateur déploie une fois** (au vidéoprojecteur), tout le monde voit le résultat en ligne, et chacun garde **son app locale** comme livrable. L'important est d'avoir compris le principe et d'avoir quelque chose à montrer.
