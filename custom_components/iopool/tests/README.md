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

✅ **215/215 tests passent (100%)**

### Détail par Module:
- **test_api_models.py**: 31/31 (100%)
- **test_binary_sensor.py**: 20/20 (100%)
- **test_config_flow.py**: 27/27 (100%)
- **test_coordinator.py**: 19/19 (100%)
- **test_diagnostics.py**: 9/9 (100%)
- **test_filtration.py**: 43/43 (100%)
- **test_init.py**: 12/12 (100%)
- **test_models.py**: 20/20 (100%)
- **test_select.py**: 13/13 (100%)
- **test_sensor.py**: 21/21 (100%)

## 📊 Analyse de Couverture de Code

### Résumé Global
- **Couverture totale** : **77%** (975/1271 lignes couvertes)
- **Commande de test** : `python -m pytest tests/ --cov=. --cov-report=term-missing`

### Couverture par Module

| Module | Lignes | Couverture | État |
|--------|--------|------------|------|
| **__init__.py** | 46 | **100%** | 🟢 Parfait |
| **api_models.py** | 60 | **100%** | 🟢 Parfait |
| **const.py** | 47 | **100%** | 🟢 Parfait |
| **coordinator.py** | 35 | **100%** | 🟢 Parfait |
| **diagnostics.py** | 21 | **100%** | 🟢 Parfait |
| **sensor.py** | 103 | **97%** | 🟢 Excellent |
| **binary_sensor.py** | 151 | **95%** | 🟢 Excellent |
| **models.py** | 117 | **79%** | 🟡 Très bon |
| **select.py** | 171 | **75%** | 🟡 Bon |
| **entity.py** | 25 | **72%** | 🟡 Bon |
| **config_flow.py** | 156 | **71%** | 🟡 Bon |
| **filtration.py** | 339 | **51%** | 🟠 À améliorer |

### Points Forts
- **5 modules ont une couverture parfaite (100%)**
- **Tous les tests passent sans erreur**
- **Base solide de 215 tests automatisés**

## Structure des Tests

```
custom_components/iopool/tests/
├── README.md                # Instructions pour exécuter les tests
├── run_tests.sh             # Script de test automatisé
├── conftest.py              # Fixtures partagées
├── conftest_hass.py         # Fixtures Home Assistant
├── test_api_models.py       # Tests modèles API (31 tests)
├── test_binary_sensor.py    # Tests entités binary_sensor (20 tests)
├── test_config_flow.py      # Tests flux de configuration (27 tests)
├── test_coordinator.py      # Tests coordinateur de données (19 tests)
├── test_diagnostics.py      # Tests diagnostic système (9 tests)
├── test_filtration.py       # Tests logique de filtration (43 tests)
├── test_init.py             # Tests initialisation intégration (12 tests)
├── test_models.py           # Tests modèles de données (20 tests)
├── test_select.py           # Tests entités select (13 tests)
└── test_sensor.py           # Tests entités sensor (21 tests)
```

## 🎯 Objectifs d'Amélioration

### Priorité 1 - Modules à Améliorer
- **filtration.py** : 51% → 65%+ (module principal, 339 lignes)
- **config_flow.py** : 71% → 80%+ (gestion d'erreurs)

### Priorité 2 - Peaufinage
- **entity.py** : 72% → 90%+ (25 lignes, facile)
- **select.py** : 75% → 85%+ (cas limites avancés)

## Notes Importantes

- **Ne pas utiliser `pytest.ini`** dans ce dossier (cause des problèmes avec les tests async)
- Le script `run_tests.sh` configure automatiquement le `PYTHONPATH` correct
- Les tests utilisent des mocks pour l'API iopool (pas de connexion réseau requise)
- Tous les tests sont async-compatibles avec Home Assistant

## 🔧 Commandes Utiles

### Tests Standard
```bash
# Tous les tests
python -m pytest tests/

# Tests avec couverture
python -m pytest tests/ --cov=. --cov-report=term-missing

# Tests d'un module spécifique
python -m pytest tests/test_select.py -v

# Tests avec rapport HTML
python -m pytest tests/ --cov=. --cov-report=html
```

### Améliorations Récentes
- **test_select.py** : Nouveau module ajouté (75% de couverture, 13 tests)
- **test_config_flow.py** : Amélioré avec gestion d'erreurs avancée
- **test_sensor.py** : Optimisé à 97% de couverture
- **Couverture globale** : Atteint 77% (objectif initial de 75% dépassé)
