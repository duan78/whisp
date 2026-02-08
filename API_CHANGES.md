# Changements d'API - Whisp Assistant v2.0

Ce document décrit tous les changements d'API entre v1.0 et v2.0.

---

## 🔄 Changements Rétrocompatibles

Tous les changements sont **rétrocompatibles**. L'ancien code continue de fonctionner.

### 1. Configuration

#### Ancien Code (Toujours Fonctionnel)

```python
from config import running, set_running, get_running

set_running(True)
if running:
    print("Assistant en marche")
```

#### Nouveau Code (Recommandé)

```python
from config import get_config

config = get_config()
config.set_running(True)
if config.get_running():
    print("Assistant en marche")
```

### 2. Clés API

#### Ancien Code (Toujours Fonctionnel)

```python
from config import setopenai_api_key, getopenai_api_key

setopenai_api_key("sk-...")
key = getopenai_api_key()
```

#### Nouveau Code (Recommandé)

```python
from config import get_config

config = get_config()
config.set_openai_api_key("sk-...")
key = config.get_openai_api_key()
```

### 3. Imports

#### Ancien Code (Toujours Fonctionnel)

```python
from config import load_config, save_config
from database_manager import save_user_preference
```

#### Nouveau Code (Recommandé)

```python
from core import load_config, save_config, save_user_preference
# OU
from config import load_config, save_config, save_user_preference
```

---

## 🆕 Nouvelles API

### 1. Gestionnaire de Configuration Unifié

```python
from config import get_config

# Obtenir l'instance singleton
config = get_config()

# État de l'assistant
config.set_running(True)
config.get_running()

# Mode dictée
config.set_dictation_mode(True, "Texte initial")
config.get_dictation_mode()
config.get_dictated_text()
config.append_dictated_text("Plus de texte")

# Mode traduction
config.set_translation_mode(True, "en", "Texte")
config.get_translation_mode()
config.get_translation_text()
config.get_target_language()
config.append_translation_text("More text")

# Moteurs
config.set_stt_engine("vosk")
config.get_stt_engine()

# Clés API (sécurisées)
config.set_openai_api_key("sk-...")
config.get_openai_api_key()
config.set_mistral_api_key("...")
config.get_mistral_api_key()
```

### 2. Validation des Entrées

```python
from input_validation import InputValidator, ValidationError

validator = InputValidator()

# Valider une commande
try:
    safe_command = validator.validate_command("ouvre notepad")
except ValidationError as e:
    print(f"Commande non autorisée: {e}")

# Valider un chemin de fichier
try:
    safe_path = validator.validate_file_path("~/Documents/file.txt")
except ValidationError as e:
    print(f"Chemin non autorisé: {e}")

# Valider une clé API
try:
    safe_key = validator.validate_api_key("sk-1234567890abcdef")
except ValidationError as e:
    print(f"Clé invalide: {e}")

# Extraire et valider un nom d'application
app_name = validator.extract_app_name("ouvre chrome")
if validator.is_command_safe("ouvre chrome"):
    # Exécuter la commande
    pass
```

### 3. Sécurité API

```python
from api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys

# Stocker une clé de manière sécurisée
set_secure_api_key("openai", "sk-...")

# Récupérer une clé
api_key = get_secure_api_key("openai")

# Migrer les anciennes clés
migrate_api_keys()
```

### 4. Détection d'Applications

```python
from app_detector import find_application, is_installed, ApplicationDetector

# Trouver une application
chrome_path = find_application("chrome")

# Vérifier si installée
if is_installed("pycharm"):
    # Lancer PyCharm
    import subprocess
    subprocess.Popen([find_application("pycharm")])

# Liste des applications installées
detector = ApplicationDetector()
apps = detector.get_installed_apps("code")  # Filtre "code"
print(apps)
```

### 5. Utilitaires Cross-Platform

```python
from platform_utils import get_window_manager, get_system_info, SystemInfo

# Gestion des fenêtres
wm = get_window_manager()

# Fenêtre active
active = wm.get_active_window()

# Liste des fenêtres
windows = wm.get_window_list()

# Mettre une fenêtre au premier plan
wm.set_foreground_window("Notepad")

# Informations système
sys_info = SystemInfo.get_system_info()
print(f"OS: {sys_info['system']} {sys_info['release']}")

# Mémoire
mem_info = SystemInfo.get_memory_info()
print(f"Mémoire: {mem_info['available_gb']:.2f} GB / {mem_info['total_gb']:.2f} GB")
```

### 6. Logging Structuré

```python
from logger_config import get_logger, setup_logging

# Configurer le logging
logger = setup_logging()

# Obtenir un logger
logger = get_logger(__name__)

# Niveaux de log
logger.debug("Message de debug")
logger.info("Message d'information")
logger.warning("Message d'avertissement")
logger.error("Message d'erreur")
logger.critical("Message critique")

# Décorateur pour les fonctions
from logger_config import log_function_call

@log_function_call()
def ma_fonction(x, y):
    return x + y
```

### 7. Cache Manager

```python
from cache_manager import (
    get_config_cache,
    get_aliases_cache,
    get_preferences_cache,
    clear_all_caches
)

# Utiliser le cache
config_cache = get_config_cache()

# Mettre en cache
config_cache.set("my_key", "my_value")

# Récupérer depuis le cache
value = config_cache.get("my_key")

# Statistiques du cache
stats = config_cache.get_stats()
print(f"Taille: {stats['size']}/{stats['max_size']}")

# Effacer tous les caches
clear_all_caches()
```

---

## 🌐 API Web (Flask 3)

### Nouveaux Endpoints

#### Cache Management

```bash
# Obtenir les statistiques du cache
GET /get_cache_stats

# Réponse
{
  "config_cache": {"size": 10, "max_size": 50},
  "aliases_cache": {"size": 5, "max_size": 100},
  ...
}

# Effacer tous les caches
POST /clear_cache

# Réponse
{"status": "success", "message": "All caches cleared"}
```

### Changements de Routes

#### Format Ancien (Toujours Supporté)

```python
@app.route('/api/command', methods=['POST'])
def process_command():
    data = request.json
    return jsonify({"result": "ok"})
```

#### Format Nouveau (Recommandé)

```python
@app.post('/api/command')
def process_command():
    data = request.get_json()  # Au lieu de request.json
    return jsonify({"result": "ok"}), 200
```

---

## 📋 Changements dans les Paramètres

### WhispConfig

```python
@dataclass
class WhispConfig:
    # État
    running: bool = True
    mode_dictee: bool = False
    mode_traduction: bool = False

    # Moteurs
    stt_engine: str = "speechrecognition"
    tts_engine: str = "gtts"

    # Texte
    texte_dicte: str = ""
    texte_a_traduire: str = ""
    langue_cible: str = ""

    # Thread-safe lock
    _lock: threading.Lock = threading.Lock()
```

---

## 🔒 Changements de Sécurité

### Validation Automatique

Toutes les commandes sont maintenant automatiquement validées :

```python
# Dans chaque module de commandes
from input_validation import InputValidator, ValidationError

validator = InputValidator()

def executer_commande_xxx(texte):
    try:
        texte = validator.validate_command(texte)
        # Traitement...
    except ValidationError as e:
        return f"Commande non autorisée: {str(e)}"
```

### Chemins Sécurisés

Tous les chemins de fichiers sont validés :

```python
# Dans file_commands.py
try:
    safe_path = validator.validate_file_path(user_path)
    # Utiliser safe_path...
except ValidationError as e:
    return f"Chemin non autorisé: {e}"
```

---

## 🧪 Tests API

```python
# Tests unitaires
from config import WhispConfig
from input_validation import InputValidator

config = WhispConfig()
assert config.get_running() == True

validator = InputValidator()
assert validator.is_command_safe("ouvre notepad") == True
```

---

## 📝 Migration Guide

### Étape 1 : Mettre à jour les imports

```python
# Ancien
from config import running, set_running

# Nouveau
from config import get_config
config = get_config()
```

### Étape 2 : Mettre à jour les accès aux données

```python
# Ancien
if running:
    set_running(False)

# Nouveau
if config.get_running():
    config.set_running(False)
```

### Étape 3 : Ajouter la validation

```python
from input_validation import InputValidator, ValidationError

validator = InputValidator()
try:
    safe_command = validator.validate_command(user_input)
except ValidationError as e:
    return f"Erreur: {e}"
```

---

## ✅ Checklist de Migration

- [ ] Mettre à jour les imports de config
- [ ] Remacer les variables globales par get_config()
- [ ] Ajouter la validation des entrées
- [ ] Utiliser le nouveau système de logging
- [ ] Mettre à jour les appels d'API (request.json → request.get_json())
- [ ] Tester toutes les fonctionnalités
- [ ] Vérifier les logs

---

**Pour plus d'informations, consultez :**
- `FINAL_REPORT.md` - Rapport complet
- `docs/security.md` - Documentation sécurité
- `QUICK_START.md` - Guide de démarrage
