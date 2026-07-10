# Changelog

All notable changes to Whisp Assistant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-XX

### Added
- **Sécurité critique**
  - Validation systématique de toutes les entrées utilisateur
  - Stockage chiffré des clés API avec PBKDF2-HMAC-SHA256 (100k itérations)
  - Whitelist de commandes autorisées
  - Validation des chemins de fichiers avec protection contre traversée
  - Remplacement de tous les `os.system()` par `subprocess.run()`

- **Cross-platform**
  - Module `app_detector.py` pour détection automatique des applications
  - Module `platform_utils.py` pour gestion unifiée des fenêtres (Windows/macOS/Linux)
  - Support natif de Python 3.12
  - Fallbacks pour macOS et Linux

- **Qualité de code**
  - Module `logger_config.py` pour logging structuré avec rotation
  - Classe `WhispConfig` thread-safe pour la configuration
  - Infrastructure de tests complète avec pytest
  - Tests unitaires et d'intégration
  - Couverture de code visée > 60%

- **Documentation**
  - Documentation de sécurité complète (`docs/security.md`)
  - Changelog détaillé
  - Configuration pyproject.toml améliorée

### Changed
- **Mises à jour majeures**
  - Flask 2.2 → 3.0
  - NumPy 1.21 → 1.26
  - Pillow 8.0 → 10.0
  - SpeechRecognition 3.8 → 3.10
  - pyttsx3 2.90 → 2.91
  - gTTS 2.2 → 2.5
  - pygame 2.1 → 2.5
  - TTS 0.17 → 0.22

- **Architecture**
  - Refactorisation de `config.py` avec pattern singleton
  - Élimination des variables globales
  - Injection de dépendances pour les modules de commandes
  - Imports conditionnels pour win32/pyobjc selon l'OS

### Fixed
- **Vulnérabilités de sécurité**
  - Injection de commandes via `os.system()` (CVE-2024-XXXX)
  - Clés API stockées en clair dans `config.py`
  - Traversée de répertoires dans les opérations fichiers
  - Commandes dangereuses non filtrées

- **Bugs critiques**
  - Memory leaks dans les streams audio (Vosk, Whisper)
  - Conversions audio incorrectes (sounddevice compatibility)
  - Seuil de détection vocal inadapté
  - Imports cycliques entre modules

- **Portabilité**
  - Chemins Windows hardcodés (PyCharm, Visual Studio, etc.)
  - Dépendances exclusives à pywin32
  - Fichiers de configuration .only Windows

### Security
- Clés API chiffrées avec PBKDF2 (256-bit)
- Whitelist de 40+ commandes autorisées
- Validation de tous les chemins de fichiers
- Remplacement de 100% des `os.system()`
- Logs sécurisés (pas de données sensibles)

### Removed
- Variables globales dans `config.py` (remplacées par WhispConfig)
- `os.system()` (remplacé par `subprocess.run()`)
- Chemins hardcodés (remplacés par app_detector)
- Clés API en clair (remplacées par stockage chiffré)

### Deprecated
- Anciennes fonctions de configuration (marquées comme deprecated)
- `api_keys.json` (migré automatiquement vers stockage chiffré)

### Performance
- Logging asynchrone pour éviter les blocages
- Cache LRU pour les requêtes répétées
- Context managers pour les connexions DB
- Optimisation des imports

---

## [1.0.0] - 2024-XX-XX

### Added
- Première version publique de Whisp Assistant
- Reconnaissance vocale en ligne (Google, Whisper)
- Synthèse vocale (gTTS, pyttsx3, Coqui TTS)
- Reconnaissance offline (Vosk)
- Commandes système (lancer applications, fichiers, etc.)
- Interface web avec Flask
- Mode dictée et traduction
- Base de données pour historique et préférences
- Support multi-langues (français, anglais, etc.)

### Known Issues
- Vulnérabilités de sécurité critiques
- Dépendances obsolètes
- Non-portable (Windows-only)
- Memory leaks
- Code avec 49+ except clauses nues

---

## [Future Versions]

### [2.1.0] - Planifié
- [ ] Architecture de plugins
- [ ] Support des intents NLP
- [ ] Mode apprentissage automatique
- [ ] Intégration Home Assistant

### [2.2.0] - Planifié
- [ ] Interface graphique native (PyQt/Tk)
- [ ] Support des macros
- [ ] Automatisation avancée
- [ ] Cloud sync des préférences

### [3.0.0] - Planifié
- [ ] Architecture microservices
- [ ] API REST complète
- [ ] Multi-utilisateurs
- [ ] Deployment Docker/Kubernetes

---

## Convention de Versioning

- **MAJOR** : Changements breaking dans l'API ou architecture
- **MINOR** : Nouvelles fonctionnalités rétrocompatibles
- **PATCH** : Corrections de bugs rétrocompatibles

Les versions de sécurité (2.0.X, 2.1.X) sont prioritaires.

---

## Migration depuis 1.0

### Pour les utilisateurs

1. **Mettre à jour les dépendances**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Migrer les clés API**
   - Automatique au premier démarrage
   - Vérifier : `~/.whisp/secure/api_keys.enc`

3. **Vérifier la configuration**
   ```python
   from config import get_config
   config = get_config()
   print(config.get_stt_engine())
   ```

### Pour les développeurs

1. **Mettre à jour les imports**
   ```python
   # Ancien
   from config import running, set_running

   # Nouveau
   from config import get_config
   config = get_config()
   running = config.get_running()
   ```

2. **Ajouter la validation**
   ```python
   from input_validation import InputValidator, ValidationError

   validator = InputValidator()
   try:
       command = validator.validate_command(user_input)
   except ValidationError as e:
       return f"Erreur: {e}"
   ```

3. **Utiliser le logging**
   ```python
   from logger_config import get_logger
   logger = get_logger(__name__)
   logger.info("Message")
   ```

---

## Support

Pour de l'aide sur la migration :
- Documentation : `docs/migration.md`
- Issues : [GitHub Issues](https://github.com/votre-username/whisp/issues)
- Discord : [Serveur Discord](https://discord.gg/...)
