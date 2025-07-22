#!/bin/bash

# Script wrapper pour lancer les tests sans les warnings aiohttp
# Usage: ./run_tests.sh [test_path]

export PYTHONPATH="/workspaces/home-assistant-dev"
export PYTHONWARNINGS="ignore::ResourceWarning"

cd /workspaces/home-assistant-dev/config

if [ $# -eq 0 ]; then
    # Aucun argument, lancer tous les tests iopool
    python -m pytest custom_components/iopool/tests/ -v --tb=short 2>/dev/null
else
    # Avec arguments, lancer les tests spécifiés
    python -m pytest "$@" -v --tb=short 2>/dev/null
fi
