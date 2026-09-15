# Identifiants de test — FamilyTask

Application **mobile**. Connexion **email + mot de passe**. Chaque personne a un **prénom**
(qui l'identifie) et un **lien de parenté** (mère, père, fille, fils… — liste **modifiable**).
Le droit **admin** est séparé : un admin crée les comptes et peut assigner des tâches.

La base est pré-remplie avec **2 familles**. La famille Durand a **2 filles** (Léa + Emma) exprès,
pour tester la désambiguïsation de l'assistant IA.

## Famille Durand
| Email             | Prénom | Lien   | Admin | Mot de passe |
|-------------------|--------|--------|-------|--------------|
| maman@durand.fr   | Maman  | mère   | ✅    | `durand`     |
| lea@durand.fr     | Lea    | fille  |       | `lea`        |
| emma@durand.fr    | Emma   | fille  |       | `emma`       |
| tom@durand.fr     | Tom    | fils   |       | `tom`        |

## Famille Martin
| Email             | Prénom | Lien   | Admin | Mot de passe |
|-------------------|--------|--------|-------|--------------|
| papa@martin.fr    | Papa   | père   | ✅    | `martin`     |
| chloe@martin.fr   | Chloe  | fille  |       | `chloe`      |
| hugo@martin.fr    | Hugo   | fils   |       | `hugo`       |

## À tester en priorité (assistant IA, connecté en maman@durand.fr)
- « ajoute sortir les poubelles **pour ma fille** » → l'IA **demande** : Léa ou Emma ?
- « ajoute la vaisselle **pour ma fille Léa** » → créé chez Léa.
- « ajoute tondre la pelouse **pour mon fils** » → un seul fils → créé direct chez Tom.

## Créer sa famille
Écran de connexion → **Créer ma famille** (nom, prénom, lien, email, mot de passe) → tu es admin,
tu crées les comptes (onglet **Famille**), tu peux ajouter des liens (ex. « belle-mère »).

> ⚠️ Mots de passe simples : comptes de **démonstration**.
