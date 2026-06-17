#!/bin/bash

# ============================================================
# Script de lancement — LinkedIn Automation
# ============================================================

# On se place dans le dossier du projet
# (peu importe d'où vous lancez ce script)
DOSSIER="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DOSSIER"

# On active l'environnement virtuel
source venv/bin/activate

# On lance le script Python
python3 connexion.py

# On désactive l'environnement virtuel à la fin
deactivate
