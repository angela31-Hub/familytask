#!/usr/bin/env bash
# Message d'accueil affiché dans le terminal du codespace.

echo ""
echo "  ┌────────────────────────────────────────────────────────┐"
echo "  │  FamilyTask · Summer Camp « Crée ton app avec l'IA »    │"
echo "  └────────────────────────────────────────────────────────┘"
echo ""
echo "  📁  familytask/   ← TON application. Tu travailles ici toute la semaine."
echo "      corrections/  ← les versions terminées, à lire quand tu bloques."
echo ""
echo "  Pour démarrer :"
echo "      cd familytask"
echo "      docker compose up"
echo ""
echo "  Puis clique sur « Open in Browser » (bulle en bas à droite)."
echo ""

if [ -z "${AI_TOKEN}" ]; then
  echo "  ⚠️  AI_TOKEN n'est pas configuré (nécessaire pour l'assistant IA, jeudi)."
  echo "      Marche à suivre : ATELIER 1, étape 3."
  echo ""
fi

echo "  🔌 Avant de partir : git push, docker compose down,"
echo "     puis Codespaces (en bas à gauche) → Stop Current Codespace."
echo ""
