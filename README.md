# 🎤 Whisp Assistant v2.1

<div align="center">

![Whisp Assistant Logo](https://img.shields.io/badge/Whisp-Assistant-blue?style=for-the-badge&logo=python)
![Python Version](https://img.shields.io/badge/python-3.8%2B-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-GPL%20v3-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Un assistant vocal personnel intelligent et multiplateforme avec backend audio universel**

[📖 Documentation](#-documentation-complète) • [🚀 Installation](#-installation-rapide) • [💡 Utilisation](#-utilisation) • [🔧 Configuration](#-configuration) • [🤝 Contribuer](#-contribuer)

</div>

---

## 🎉 Nouveautés v2.1

### 🔒 Sécurité Renforcée
- **Validation des entrées** améliorée pour prévenir les injections
- **Tests de sécurité** intégrés et réguliers
- **Nettoyage des commandes système** avec mode sandbox
- **Suppression de l'authentification web** inutile (simplification du code)

### 🎛️ Moteurs TTS Modernisés
- **Edge-TTS** : Moteur online Microsoft de haute qualité (prioritaire)
- **Piper TTS** : Synthèse offline rapide et de qualité supérieure
- **pyttsx3** : Fallback offline natif
- **gTTS** : Google Text-to-Speech (fallback online)
- **27 tests TTS** pour garantir la fiabilité

### 🎯 Backend Audio Universel v2.0
- **Détection automatique** du meilleur backend audio disponible
- **Cross-platform** : Fonctionne sur Windows, macOS, Linux
- **Offline natif** : Reconnaissance vocale offline avec Vosk
- **Fallback intelligent** : Bascule automatiquement entre les backends
- **Diagnostics audio** complets pour le dépannage

### 🤖 IA Intégrée
- **OpenAI API** : Support complet pour les modèles GPT
- **Mistral AI** : Alternative open-source performante
- **Contexte conversationnel** intelligent

**Backend audio prioritaire :**
1. **Vosk + sounddevice** (offline, recommandé)
2. **sounddevice + Google Speech** (online)
3. **PyAudio + Google Speech** (si disponible)
4. **Web only** (mode dégradé)

---

## 🌟 Fonctionnalités Principales

### 🎙️ Reconnaissance Vocale Avancée
- **Backend audio universel** avec détection automatique
- **faster-whisper** : Version optimisée de Whisper (jusqu'à 4x plus rapide)
- **Vosk** : Reconnaissance offline native
- **SpeechRecognition** : Support multi-API (Google, Wit.ai, etc.)
- **Support multilingue** avec optimisation française
- **Mode continu** intelligent et adaptatif
- **Diagnostics audio** intégrés

### 🔊 Synthèse Vocale de Haute Qualité
- **Edge-TTS** : Moteur online Microsoft (prioritaire)
- **Piper TTS** : Synthèse offline rapide
- **pyttsx3** : Système natif (fallback offline)
- **gTTS** : Google Text-to-Speech (fallback online)
- **Cache audio** pour réponses rapides
- **Voices personnalisables** par langue
- **27 tests TTS** pour fiabilité maximale

### 🖥️ Interface Web Moderne v2.0
- **Tableau de bord** responsive et élégant
- **Configuration en temps réel**
- **Visualisation des métriques** et logs
- **Chat moderne** avec historique
- **Accessibilité** améliorée
- **Mode sombre/clair** automatique

### ⚡ Automatisation & Productivité
- **Contrôle système** complet par commandes vocales
- **Automatisation navigateur** et applications
- **Intégration Git** pour développeurs
- **Mode dictée** continue pour rédaction
- **Raccourcis personnalisables** avec base de données SQLite
- **Validation des entrées** pour sécurité

### 🤖 Intelligence Artificielle
- **OpenAI GPT** : Modèles de langage state-of-the-art
- **Mistral AI** : Alternative open-source performante
- **Contexte conversationnel** intelligent
- **Génération de code** et assistance développement

### 🛠️ Outils Intégrés
- **Gestion de fenêtres** intelligente
- **Lecteur d'écran** avancé
- **Traduction automatique**
- **Analyse de code** et assistance développement
- **Gestionnaire de rappels**

---

## 📋 Prérequis

- **Python 3.8+** (3.12+ recommandé pour compatibilité optimale)
- **Microphone** (pour reconnaissance vocale)
- **Haut-parleurs/casque** (pour synthèse vocale)
- **Windows 10+/macOS 10.15+/Linux** (support multiplateforme complet)

---

## 🚀 Installation Rapide

### 1. Cloner le repository
```bash
git clone https://github.com/duan78/whisp.git
cd whisp
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
# Installation des dépendances core
pip install -r requirements.txt

# Installation recommandée pour reconnaissance offline
pip install sounddevice vosk

# Installation optionnelle (fonctionnalités avancées)
pip install -r requirements_optional.txt
```

### 4. Télécharger un modèle Vosk (pour reconnaissance offline)
```bash
# Télécharger depuis: https://alphacephei.com/vosk/models
# Recommandé: vosk-model-small-fr-0.22 (~50 Mo)

# Extraire dans le dossier models/
# Votre structure devrait ressembler à:
# whisp-assistant/
#   ├── models/
#   │   └── vosk-model-small-fr-0.22/
#   │       ├── am/
#   │       ├── conf/
#   │       └── ...
#   └── ...
```

### 5. Configurer les clés API (optionnel mais recommandé)
```bash
# Créer un fichier .env ou config.env
OPENAI_API_KEY=votre-clé-openai
MISTRAL_API_KEY=votre-clé-mistral
```

### 6. Lancer l'assistant
```bash
python main.py
```

L'interface web sera accessible à **http://localhost:5000**

---

## 💡 Utilisation

### Commandes de Base
- `"Dis aide"` - Afficher l'aide générale
- `"Écris [texte]"` - Dicter du texte
- `"Fin de dictée"` - Arrêter la dictée
- `"Ouvre [application]"` - Lancer une application
- `"Recherche [terme]"` - Lancer une recherche web
- `"Quitte l'assistant"` - Arrêter l'assistant

### Commandes IA
- `"Explique-moi [sujet]"` - Explication avec GPT/Mistral
- `"Résume ce texte"` - Résumer un texte
- `"Génère du code pour [tâche]"` - Génération de code
- `"Traduis en [langue]"` - Traduction intelligente

### Pour les Développeurs
- `"Git status"` - Voir l'état Git
- `"Git commit [message]"` - Créer un commit
- `"Git push"` - Pousser les changements
- `"Ouvre VS Code"` - Lancer l'éditeur
- `"Décris cet écran"` - Analyse contextuelle

### Mode Dictée
```bash
# Démarrer la dictée
"Écris" ou "Commence la dictée"

# Arrêter la dictée
"Fin de dictée" ou "Arrête la dictée"
```

---

## 🔧 Configuration

### Backend Audio Universel

Le système détecte automatiquement le meilleur backend disponible :

```python
# Configuration automatique (recommandé)
from core.config import set_audio_backend
set_audio_backend("auto")

# Forcer un backend spécifique
set_audio_backend("vosk_sounddevice")      # Offline (recommandé)
set_audio_backend("sounddevice_google")     # Online
set_audio_backend("pyaudio_google")         # Online (si PyAudio installé)
set_audio_backend("web_only")               # Pas de reconnaissance vocale
```

### Variables d'Environnement (config.env)

```bash
# Moteurs de reconnaissance vocale
STT_ENGINE=vosk  # Options: speechrecognition, whisper, vosk, faster-whisper

# Moteurs de synthèse vocale
TTS_ENGINE=edge_tts  # Options: pyttsx3, edge_tts, piper, gtts

# Clés API (optionnelles mais recommandées)
OPENAI_API_KEY=votre-clé-openai
MISTRAL_API_KEY=votre-clé-mistral

# Interface web
WEB_PORT=5000
WEB_HOST=127.0.0.1
```

### Moteurs Disponibles

#### Reconnaissance Vocale (STT)
- **faster-whisper** : ⭐ **Recommandé** - Version optimisée de Whisper (4x plus rapide)
- **Vosk + sounddevice** : Reconnaissance offline native
- **SpeechRecognition** : Support multi-API (Google, Wit.ai, etc.)
- **Whisper** : Modèles OpenAI haute précision

#### Synthèse Vocale (TTS)
- **Edge-TTS** : ⭐ **Recommandé** - Moteur Microsoft online de haute qualité
- **Piper** : Synthèse offline rapide et de qualité
- **pyttsx3** : Système natif (offline)
- **gTTS** : Google Text-to-Speech (online, fallback)

---

## 🏗️ Architecture

```
whisp/
├── 🎙️ Système Audio Universel v2.0
│   ├── universal_audio_backend.py  # Gestionnaire audio unifié
│   ├── platform_audio_config.py    # Configuration par plateforme
│   └── stt_engine_factory.py       # Factory pour moteurs STT
├── 🎯 Modules principaux
│   ├── main.py                      # Point d'entrée
│   ├── speech_recognition_module.py # Reconnaissance vocale (STT)
│   ├── tts_module.py                # Synthèse vocale (Edge-TTS, Piper, gTTS, pyttsx3)
│   └── command_processor.py         # Cœur de traitement
├── 🖥️ Interface web v2.0
│   ├── web_interface.py             # App Flask + enregistrement des blueprints
│   ├── web/state.py                 # État partagé (logs, queues, handlers)
│   ├── web/blueprints/              # Routes extraites (bugs, shortcuts, aliases, finetune)
│   ├── templates/                   # Templates HTML
│   └── static/                      # CSS/JS assets
├── 🪟 Gestion des fenêtres
│   ├── window_manager.py            # Shim de compatibilité
│   └── window/                      # commands, focus, monitors, enumeration, active_app
├── ⚡ Modules de commande
│   ├── keyboard_commands.py         # Contrôle clavier
│   ├── mouse_commands.py            # Contrôle souris
│   ├── browser_commands.py          # Automatisation web
│   ├── system_commands.py           # Commandes système
│   ├── git_commands.py              # Intégration Git
│   └── ...                          # Autres modules
├── 🗄️ Gestion des données
│   ├── core/
│   │   ├── config.py                # Configuration centralisée
│   │   ├── database_manager.py      # Base de données SQLite
│   │   ├── api_security.py          # Sécurité API (chiffrement clés)
│   │   └── error_handler.py         # Gestion d'erreurs
│   ├── stt/finetune.py              # Pipeline fine-tuning HuggingFace
│   └── shortcuts_database.py        # Raccourcis perso (scripts sandboxés)
├── 🧪 Tests
│   ├── tests/unit/                  # Tests unitaires (config, validation, TTS, sécurité)
│   └── tests/integration/           # Tests d'intégration
└── 🔧 Utilitaires
    ├── error_handler.py             # Shim → core/error_handler
    ├── lazy_loader.py               # Chargement paresseux
    ├── dependency_manager.py        # Gestion dépendances
    └── scripts/diagnostics/         # Scripts de diagnostic audio/performance
```

---

## 🧪 Tests

### Diagnostic du Backend Audio

```bash
# Test complet du système audio universel
python scripts/diagnostics/check_universal_audio.py

# Le script vérifie:
# - Détection des backends disponibles
# - Microphone détecté
# - Modèle Vosk présent
# - Meilleur backend sélectionné
```

### Tests Unitaires et d'Intégration

```bash
# Lancer tous les tests (68 tests, 5 skipped)
pytest

# Tests avec couverture
pytest --cov=.

# Tests spécifiques
pytest tests/unit/test_tts_engines.py        # 27 tests TTS
pytest tests/unit/test_shortcuts_security.py  # Tests de sécurité raccourcis
pytest tests/unit/test_config.py              # Tests de configuration
pytest tests/unit/test_input_validation.py    # Tests de validation
```

---

## 📊 Métriques et Performance

### Optimisations Intégrées
- **faster-whisper** : Jusqu'à 4x plus rapide que Whisper standard
- **Backend audio universel** avec sélection automatique
- **Chargement paresseux** des modules lourds
- **Cache intelligent** pour réponses TTS fréquentes
- **Threading async** pour non-bloquant
- **Validation des entrées** pour sécurité

### Performance par Backend

| Backend | Latence | Offline | CPU | Qualité |
|---------|---------|---------|-----|---------|
| faster-whisper | ~200-400ms | ✅ | 10-20% | ⭐⭐⭐⭐⭐ |
| Vosk + sounddevice | ~100-200ms | ✅ | 5-15% | ⭐⭐⭐⭐⭐ |
| Edge-TTS | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐⭐ |
| Piper | ~100-300ms | ✅ | 5-10% | ⭐⭐⭐⭐ |
| sounddevice + Google | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| SpeechRecognition | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |

---

## 🌐 Support Multilingue

- **Français** : Support natif et optimisé (modèle Vosk français)
- **Anglais** : Support complet
- **Espagnol, Allemand, Italien** : Support partiel
- **Extensible** : Ajout facile de nouvelles langues

---

## 🔒 Sécurité

- **Validation des entrées** pour prévenir injections
- **Stockage sécurisé** des clés API (encryption avec cryptography)
- **Mode sandbox** pour commandes système
- **Tests de sécurité** intégrés et réguliers
- **Nettoyage des commandes** avant exécution
- **Suppression de l'authentification web** inutile (réduction de la surface d'attaque)

---

## 🐛 Dépannage

### Problème: "Aucun backend audio n'est disponible"

**Solution:**
```bash
pip install sounddevice vosk
```

### Problème: "Aucun modèle Vosk trouvé"

**Solution:**
1. Téléchargez: https://alphacephei.com/vosk/models
2. Choisissez: vosk-model-small-fr-0.22
3. Extrayez dans: `models/vosk-model-small-fr-0.22/`

### Problème: "faster-whisper non disponible"

**Solution:**
```bash
pip install faster-whisper
```

### Problème: "Edge-TTS ne fonctionne pas"

**Solution:**
```bash
pip install edge-tts
```

### Problème: "Niveaux audio trop bas"

**Solution:**
```bash
# Lancer les diagnostics audio
python scripts/diagnostics/check_universal_audio.py
```

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Voici comment participer :

### 1. Fork le projet
```bash
git clone https://github.com/duan78/whisp.git
```

### 2. Créer une branche
```bash
git checkout -b feature/nouvelle-fonctionnalite
```

### 3. Faire les changements
- Ajouter des tests pour nouvelles fonctionnalités
- Maintenir le style de code existant (PEP 8)
- Documenter les changements
- Exécuter les tests de sécurité
- Vérifier la compatibilité multiplateforme

### 4. Soumettre une Pull Request
```bash
git push origin feature/nouvelle-fonctionnalite
# Créer une PR sur GitHub
```

---

## 📖 Documentation Complète

- [📘 Guide d'Installation](docs/installation.md)
- [🔧 Configuration Avancée](docs/configuration.md)
- [🎤 Commandes Vocales](docs/utilisation.md)
- [🔒 Sécurité](docs/security.md)
- [🐛 Dépannage](#-dépannage)

---

## 🗺️ Feuille de Route

### Version 2.1 (Actuelle) - ✅ TERMINE
- ✅ **Edge-TTS + Piper** : Moteurs TTS modernisés
- ✅ **Sécurité renforcée** : bind Flask sur 127.0.0.1, fix path traversal `/records`, suppression `exec()` des raccourcis (sandbox isolée), suppression des injections `shell=True`, chiffrement des clés API (Fernet/PBKDF2), SQL allowlist SELECT-only
- ✅ **Refactor architectural** : découpage de `window_manager.py` (package `window/`), `web_interface.py` (Flask Blueprints), `speech_recognition_module.py` (extraction `stt/finetune.py`)
- ✅ **Nettoyage** : suppression du code mort, fix du packaging (package fantôme `whisp_assistant`), séparation requirements runtime/dev
- ✅ **27 tests TTS** + tests de sécurité raccourcis (68 tests au total)
- ✅ **Backend audio universel v2.0** avec diagnostics
- ✅ Support multiplateforme (Windows, macOS, Linux)
- ✅ Reconnaissance offline avec Vosk
- ✅ Interface web moderne v2.0

### Version 2.2 (En cours)
- 🔄 Support plugins externes
- 🔄 Mode apprentissage automatique
- 🔄 Voix personnalisables avancées
- 🔄 Performance monitoring

### Version 3.0 (Futur)
- 📋 Intelligence artificielle conversationnelle avancée
- 📋 Support multilingue étendu
- 📋 Interface mobile

---

## 📝 Licence

Ce projet est sous licence **GPL v3.0** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- **OpenAI** : Modèles Whisper et GPT
- **Mistral AI** : Modèles de langage open-source performants
- **Microsoft** : Edge-TTS
- **Piper TTS** : Synthèse vocale rapide
- **Google** : API Speech-to-Text et Text-to-Speech
- **Mozilla** : Projet Common Voice
- **Alpha Cephei** : Moteur Vosk STT

---

## 📞 Contact & Support

- **GitHub Issues** : Pour bugs et fonctionnalités
- **Discord** : [Serveur communautaire](https://discord.gg/whisp)
- **Email** : support@whisp-assistant.com
- **Documentation** : https://docs.whisp-assistant.com

---

<div align="center">

**⭐ Si ce projet vous plaît, n'hésitez pas à laisser une étoile !**

Made with ❤️ by the Whisp Team

[![GitHub stars](https://img.shields.io/github/stars/duan78/whisp?style=social)](https://github.com/duan78/whisp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/duan78/whisp?style=social)](https://github.com/duan78/whisp/network/members)
[![GitHub issues](https://img.shields.io/github/issues/duan78/whisp)](https://github.com/duan78/whisp/issues)

**Reconnaissance vocale offline • faster-whisper • Edge-TTS • Piper TTS • Python 3.12**

</div>
