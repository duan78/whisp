# Guide de Démarrage Rapide - Whisp Assistant v2.0

## 🚀 Installation en 3 Étapes

```bash
# 1. Installer les dépendances
pip install --upgrade -r requirements.txt

# 2. Lancer les tests (optionnel mais recommandé)
pytest tests/ -v

# 3. Démarrer l'assistant
python main.py
```

---

## ✅ Vérification de l'Installation

### 1. Vérifier les dépendances

```bash
python -c "import flask, numpy; print(f'Flask: {flask.__version__}, NumPy: {numpy.__version__}')"
# Attendu: Flask: 3.x.x, NumPy: 1.26.x
```

### 2. Vérifier la sécurité

```bash
python -c "from input_validation import ALLOWED_COMMANDS; print(f'{len(ALLOWED_COMMANDS)} commandes autorisées')"
# Attendu: 40+ commandes autorisées
```

### 3. Vérifier le chiffrement

```bash
python -c "from api_security import get_secure_api_key; print('Chiffrement OK')"
# Attendu: Chiffrement OK
```

---

## 🔑 Configuration des Clés API

### Méthode 1 : Variables d'environnement (Recommandé)

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-..."
export MISTRAL_API_KEY="..."

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
$env:MISTRAL_API_KEY="..."
```

### Méthode 2 : Via l'interface web

```bash
# Démarrer l'assistant
python main.py

# Ouvrir le navigateur
http://localhost:5000

# Aller dans Configuration > API Keys
```

### Méthode 3 : Migration automatique

Si vous aviez des clés dans `api_keys.json`, elles seront automatiquement migrées vers le stockage chiffré au premier démarrage.

---

## 🧪 Lancer les Tests

### Tous les tests
```bash
pytest tests/ -v
```

### Avec couverture
```bash
pytest tests/ --cov=. --cov-report=html
# Rapport dans htmlcov/index.html
```

### Tests unitaires uniquement
```bash
pytest tests/unit/ -v
```

### Tests de performance
```bash
python test_optimizations.py
```

---

## 🎯 Utilisation de Base

### Commandes Vocales

```python
# Depuis Python
from command_processor import CommandProcessor

processor = CommandProcessor()

# Exécuter une commande
result = processor.process_command("quelle heure est-il")
print(result)  # "Il est 14:30"

# Ouvrir une application
result = processor.process_command("ouvre notepad")
```

### Via l'Interface Web

```bash
# Démarrer l'assistant
python main.py

# Ouvrir http://localhost:5000

# Utiliser l'interface pour:
# - Voir les logs
# - Envoyer des commandes
# - Configurer les moteurs
# - Gérer les clés API
```

---

## 🔧 Configuration

### Changer le moteur STT

```python
from config import set_stt_engine

set_stt_engine("vosk")  # Options: speechrecognition, nemo, whisper, vosk
```

### Changer le moteur TTS

```python
from config import get_config
config = get_config()
config.tts_engine = "gtts"  # Options: pyttsx3, gtts, coqui, piper
```

### Mode Dictée

```python
from config import set_dictation_mode

# Activer le mode dictée
set_dictation_mode(True, "Texte initial")

# Dicter du texte
config = get_config()
config.append_dictated_text("Hello world")
print(config.get_dictated_text())  # "Texte initial Hello world"
```

---

## 📊 Vérifier le Statut

### Via Python

```python
from config import get_config

config = get_config()
print(f"Running: {config.get_running()}")
print(f"STT Engine: {config.get_stt_engine()}")
print(f"OpenAI Key: {bool(config.get_openai_api_key())}")
```

### Via l'Interface Web

```bash
curl http://localhost:5000/status
```

---

## 🐛 Dépannage

### Erreur: ImportError pour input_validation

```bash
# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Erreur: Tests échouent

```bash
# Installer les dépendances de test
pip install pytest pytest-cov

# Lancer un seul test pour voir l'erreur
pytest tests/unit/test_input_validation.py::TestInputValidator::test_sanitize_string_basic -vv
```

### Erreur: Clés API non migrées

```python
# Forcer la migration
from api_security import migrate_api_keys
migrate_api_keys()
```

### Erreur: Le logging ne fonctionne pas

```python
# Réinitialiser le logging
from logger_config import setup_logging
logger = setup_logging()
logger.info("Test")
```

---

## 📚 Documentation Complète

| Document | Description |
|----------|-------------|
| `FINAL_REPORT.md` | Rapport final de modernisation |
| `docs/security.md` | Documentation sécurité |
| `CHANGELOG.md` | Historique des versions |
| `PERFORMANCE_OPTIMIZATIONS.md` | Documentation performance |

---

## 🎓 Exemples d'Utilisation

### Exemple 1 : Commande vocale simple

```python
from command_processor import CommandProcessor

processor = CommandProcessor()
result = processor.process_command("ouvre chrome")
print(result)  # "Chrome ouvert"
```

### Exemple 2 : Utiliser la validation

```python
from input_validation import InputValidator, ValidationError

validator = InputValidator()

try:
    safe_command = validator.validate_command("ouvre notepad")
    print(f"Commande sûre: {safe_command}")
except ValidationError as e:
    print(f"Commande bloquée: {e}")
```

### Exemple 3 : Utiliser le logging

```python
from logger_config import get_logger

logger = get_logger(__name__)
logger.info("Application démarrée")
logger.warning("Attention: quelque chose")
logger.error("Erreur survenue")
```

### Exemple 4 : Utiliser la configuration

```python
from config import get_config

config = get_config()

# Modifier la configuration
config.set_running(True)
config.set_stt_engine("vosk")

# Lire la configuration
print(f"Running: {config.get_running()}")
print(f"Engine: {config.get_stt_engine()}")
```

---

## 🚀 Prochaines Étapes

1. **Lire la documentation** : `docs/security.md`, `CHANGELOG.md`
2. **Explorer les tests** : `tests/unit/`, `tests/integration/`
3. **Vérifier les performances** : `python test_optimizations.py`
4. **Personnaliser** : Modifier `config.py` selon vos besoins

---

**Bon usage de Whisp Assistant v2.0 !** 🎉

Pour plus d'aide, consultez la documentation ou les tests.
