#!/bin/bash

# ============================================================
# Script de lancement — LinkedIn Automation
# ============================================================

DOSSIER="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DOSSIER"

source venv/bin/activate

# Point d'entrée unique : main.py
python3 main.py

deactivate