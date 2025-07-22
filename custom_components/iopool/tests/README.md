# Instructions pour Exécuter les Tests

## Méthode Recommandée

### Option 1: Script de Test
```bash
# Depuis n'importe où dans le projet
/workspaces/home-assistant-dev/config/custom_components/iopool/tests/run_tests.sh

# Avec options pytest
/workspaces/home-assistant-dev/config/custom_components/iopool/tests/run_tests.sh -v
/workspaces/home-assistant-dev/config/custom_components/iopool/tests/run_tests.sh --tb=short
```

### Option 2: Commande Manuelle
```bash
# Depuis /workspaces/home-assistant-dev/config
cd /workspaces/home-assistant-dev/config
PYTHONPATH=/workspaces/home-assistant-dev python -m pytest custom_components/iopool/tests/
```

## Résultats Actuels

✅ **64/64 tests passent (100%)**

### Détail par Module:
- **test_api_models.py**: 11/11 (100%)
- **test_binary_sensor.py**: 10/10 (100%)
- **test_config_flow.py**: 13/13 (100%)
- **test_coordinator.py**: 8/8 (100%)
- **test_init.py**: 4/4 (100%)
- **test_select.py**: 12/12 (100%)
- **test_sensor.py**: 6/6 (100%)

## Structure des Tests

```
custom_components/iopool/tests/
├── README.md                # Instructions pour exécuter les tests
├── run_tests.sh             # Script de test automatisé
├── conftest.py              # Fixtures partagées
├── test_api_models.py       # Tests modèles API
├── test_binary_sensor.py    # Tests entités binary_sensor
├── test_config_flow.py      # Tests flux de configuration
├── test_coordinator.py      # Tests coordinateur de données
├── test_init.py             # Tests initialisation intégration
├── test_select.py           # Tests entités select
└── test_sensor.py           # Tests entités sensor
```

## Notes Importantes

- **Ne pas utiliser `pytest.ini`** dans ce dossier (cause des problèmes avec les tests async)
- Le script `run_tests.sh` configure automatiquement le `PYTHONPATH` correct
- Les tests utilisent des mocks pour l'API iopool (pas de connexion réseau requise)
- Tous les tests sont async-compatibles avec Home Assistant
