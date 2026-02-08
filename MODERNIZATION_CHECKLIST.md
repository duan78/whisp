# Guide de Démarrage - Whisp Assistant v2.0

## Installation Rapide

```bash
# 1. Mettre à jour les dépendances
pip install --upgrade -r requirements.txt

# 2. Installer les dépendances de développement (optionnel)
pip install -e ".[dev]"

# 3. Lancer les tests
pytest tests/ -v

# 4. Démarrer l'assistant
python main.py
```

---

## Vérification de la Modernisation

### ✅ Sécurité

```bash
# 1. Vérifier que la validation est activée
python -c "from input_validation import ALLOWED_COMMANDS; print(f'{len(ALLOWED_COMMANDS)} commandes autorisées')"

# 2. Tester la validation des commandes
python -c "
from input_validation import InputValidator, ValidationError
v = InputValidator()
try:
    v.validate_command('ouvre notepad && rm -rf /')
except ValidationError as e:
    print(f'✓ Injection bloquée: {e}')
"

# 3. Vérifier le stockage chiffré
python -c "
from api_security import get_secure_api_key
key = get_secure_api_key('openai')
print(f'✓ Clé API chiffrée: {bool(key)}')
"
```

### ✅ Dépendances

```bash
# Vérifier les versions
python -c "
import flask, numpy, speechrecognition
print(f'Flask: {flask.__version__} (attendu: 3.0.x)')
print(f'NumPy: {numpy.__version__} (attendu: 1.26.x)')
print(f'SpeechRecognition: {speechrecognition.__version__} (attendu: 3.10.x)')
"
```

### ✅ Cross-Platform

```bash
# Tester le détecteur d'applications
python -c "
from app_detector import ApplicationDetector
detector = ApplicationDetector()
print(f'Système: {detector.system}')
print(f'Chrome trouvé: {detector.is_installed(\"chrome\")}')
print(f'Notepad trouvé: {detector.is_installed(\"notepad\")}')
"
```

### ✅ Configuration

```bash
# Tester la nouvelle configuration
python -c "
from config import get_config
config = get_config()
print(f'Running: {config.get_running()}')
print(f'STT Engine: {config.get_stt_engine()}')
print(f'Thread-safe: {hasattr(config, \"_lock\")}')
"
```

### ✅ Logging

```bash
# Tester le système de logging
python -c "
from logger_config import get_logger
logger = get_logger('test')
logger.info('Test de logging')
print('✓ Logging fonctionnel')
"
```

---

## Tests

### Lancer tous les tests

```bash
pytest tests/ -v
```

### Tests avec couverture

```bash
pytest tests/ --cov=. --cov-report=html
# Rapport généré dans htmlcov/index.html
```

### Tests unitaires uniquement

```bash
pytest tests/unit/ -v
```

### Tests d'intégration uniquement

```bash
pytest tests/integration/ -v
```

### Tests spécifiques

```bash
# Tests de validation
pytest tests/unit/test_input_validation.py -v

# Tests de configuration
pytest tests/unit/test_config.py -v

# Tests de commande
pytest tests/integration/test_command_processing.py -v
```

---

## Migration

### Clés API

Les clés API sont automatiquement migrées depuis `api_keys.json` vers le stockage chiffré.

**Emplacement du nouveau stockage** :
- Windows : `C:\Users\{User}\.whisp\secure\api_keys.enc`
- macOS/Linux : `~/.whisp/secure/api_keys.enc`

### Variables Globales

L'ancien code avec les variables globales fonctionne toujours grâce aux fonctions de compatibilité :

```python
# Ancien code (toujours fonctionnel)
from config import running, set_running
set_running(True)

# Nouveau code (recommandé)
from config import get_config
config = get_config()
config.set_running(True)
```

---

## Développement

### Formatter le code

```bash
black .
isort .
```

### Linter

```bash
flake8 .
```

### Type checking

```bash
mypy .
```

### Sécurité

```bash
bandit -r .
```

---

## Dépannage

### Problème : ImportError pour input_validation

**Solution** :
```bash
# Vérifier que le fichier existe
ls input_validation.py

# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Problème : Les tests échouent

**Solution** :
```bash
# Installer les dépendances de test
pip install pytest pytest-cov

# Lancer un seul test pour voir l'erreur détaillée
pytest tests/unit/test_input_validation.py::TestInputValidator::test_sanitize_string_basic -vv
```

### Problème : Clés API non migrées

**Solution** :
```python
from api_security import migrate_api_keys
migrate_api_keys()
```

### Problème : Le logging ne fonctionne pas

**Solution** :
```python
from logger_config import setup_logging
logger = setup_logging()
logger.info("Test")
```

---

## Prochaines Étapes

1. **Compléter la sécurité** (Phase 1.3-1.4)
   - Valider les chemins dans file_commands.py
   - Requêtes paramétrées dans database_commands.py

2. **Implémenter la cross-platform** (Phase 3.2)
   - Intégrer platform_utils dans screen_reader
   - Tester sur macOS et Linux

3. **Améliorer la qualité** (Phase 4.1, 4.4)
   - Remplacer les except clauses nues
   - Résoudre les imports cycliques

4. **Optimiser** (Phase 6)
   - Implémenter async/await
   - Corriger les memory leaks restants

---

## Support

- **Documentation** : `docs/security.md`, `CHANGELOG.md`
- **Rapport** : `MODERNIZATION_REPORT.md`
- **Issues** : GitHub Issues
