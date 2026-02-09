# 🎤 Whisp Assistant

<div align="center">

![Whisp Assistant Logo](https://img.shields.io/badge/Whisp-Assistant-blue?style=for-the-badge&logo=python)
![Python Version](https://img.shields.io/badge/python-3.8%2B-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-GPL%20v3-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Un assistant vocal personnel intelligent et multiplateforme avec backend audio universel**

[📖 Documentation](#documentation) • [🚀 Installation](#installation) • [💡 Utilisation](#utilisation) • [🔧 Configuration](#configuration) • [🤝 Contribuer](#contribuer)

</div>

---

## 🎉 Nouveautés v2.0 - Backend Audio Universel

### ✨ Nouveau Système Audio Unifié
- **🎯 Détection automatique** du meilleur backend audio disponible
- **🌐 Cross-platform** : Fonctionne sur Windows, macOS, Linux sans modification
- **🔧 Sans PyAudio** : Utilise sounddevice comme alternative moderne
- **📡 Offline natif** : Reconnaissance vocale offline avec Vosk
- **🔄 Fallback intelligent** : Bascule automatiquement entre les backends
- **🚀 Python 3.14+** : Compatible avec les dernières versions de Python

**Backend audio prioritaire :**
1. **Vosk + sounddevice** (offline, recommandé)
2. **sounddevice + Google Speech** (online)
3. **PyAudio + Google Speech** (si disponible)
4. **Web only** (mode dégradé)

---

## 🌟 Fonctionnalités Principales

### 🎙️ Reconnaissance Vocale Avancée
- **Backend audio universel** avec détection automatique
- **Multi-moteurs** : SpeechRecognition, NeMo, Whisper, Vosk, Whisper CT2
- **Support multilingue** avec optimisation française
- **Mode continu** intelligent et adaptatif
- **Reconnaissance offline** avec Vosk
- **Optimisation CUDA** pour accélération GPU (Windows)

### 🔊 Synthèse Vocale de Haute Qualité
- **Plusieurs moteurs TTS** : pyttsx3 (offline), gTTS (online), CoquiTTS, Piper
- **Préchargement intelligent** des modèles
- **Cache audio** pour réponses rapides
- **Voices personnalisables** par langue

### 🖥️ Interface Web Moderne
- **Tableau de bord** responsive et élégant
- **Configuration en temps réel**
- **Visualisation des métriques** et logs
- **Support multi-utilisateurs** avec authentification optionnelle
- **Mode sombre/clair** automatique

### ⚡ Automatisation & Productivité
- **Contrôle système** complet par commandes vocales
- **Automatisation navigateur** et applications
- **Intégration Git** pour développeurs
- **Mode dictée** continue pour rédaction
- **Raccourcis personnalisables**

### 🛠️ Outils Intégrés
- **Gestion de fenêtres** intelligente
- **Lecteur d'écran** avancé
- **Traduction automatique**
- **Analyse de code** et assistance développement
- **Gestionnaire de rappels**

---

## 📋 Prérequis

- **Python 3.8+** (testé jusqu'à Python 3.14)
- **Microphone** (pour reconnaissance vocale)
- **Haut-parleurs/casque** (pour synthèse vocale)
- **Windows 10+/macOS 10.15+/Linux** (support multiplateforme complet)

---

## 🚀 Installation Rapide

### 1. Cloner le repository
```bash
git clone https://github.com/votre-username/whisp-assistant.git
cd whisp-assistant
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
# Installation recommandée (backend audio universel)
pip install sounddevice vosk

# Installation des dépendances core
pip install -r requirements.txt

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

### 5. Lancer l'assistant
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
STT_ENGINE=vosk  # Options: speechrecognition, whisper, nemo, vosk, whisper_ct2

# Moteurs de synthèse vocale
TTS_ENGINE=gtts  # Options: pyttsx3, coqui, piper

# Clés API (optionnelles)
OPENAI_API_KEY=votre-clé-openai
MISTRAL_API_KEY=votre-clé-mistral

# Interface web
WEB_PORT=5000
WEB_HOST=127.0.0.1
```

### Moteurs Disponibles

#### Reconnaissance Vocale (STT)
- **Vosk + sounddevice** : ⭐ **Recommandé** - Reconnaissance offline, fonctionne partout
- **SpeechRecognition** : Support multi-API (Google, Wit.ai, etc.)
- **Whisper** : Modèles OpenAI haute précision
- **Whisper CT2** : Version optimisée avec CTranslate2
- **NeMo** : NVIDIA pour GPU/CPU optimisé

#### Synthèse Vocale (TTS)
- **gTTS** : Google Text-to-Speech (online)
- **pyttsx3** : Système natif (offline)
- **CoquiTTS** : Voix neuronales avancées
- **Piper** : Synthèse offline rapide

---

## 🏗️ Architecture

```
whisp-assistant/
├── 🎙️ Système Audio Universel (NOUVEAU v2.0)
│   ├── universal_audio_backend.py  # Gestionnaire audio unifié
│   ├── platform_audio_config.py    # Configuration par plateforme
│   ├── stt_engine_factory.py       # Factory pour moteurs STT
│   ├── vosk_audio_handler.py       # Handler Vosk + sounddevice
│   └── vosk_sounddevice_stt.py     # Moteur STT Vosk complet
├── 🎯 Modules principaux
│   ├── main.py                      # Point d'entrée
│   ├── speech_recognition_module.py # Reconnaissance vocale
│   ├── tts_module.py                # Synthèse vocale
│   └── command_processor.py         # Cœur de traitement
├── 🖥️ Interface web
│   ├── web_interface.py             # Flask web app
│   ├── templates/                   # Templates HTML
│   └── static/                      # CSS/JS assets
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
│   │   └── api_security.py          # Sécurité API
│   └── shortcuts_database.py        # Raccourcis perso
└── 🔧 Utilitaires
    ├── error_handler.py             # Gestion d'erreurs
    ├── lazy_loader.py               # Chargement paresseux
    ├── dependency_manager.py        # Gestion dépendances
    └── text_processing.py           # Traitement texte
```

---

## 🧪 Tests

### Tester le Backend Audio

```bash
# Test complet du système audio universel
python test_universal_audio.py

# Le script vérifie:
# - Détection des backends disponibles
# - Microphone détecté
# - Modèle Vosk présent
# - Meilleur backend sélectionné
```

### Tests Unitaires

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=.

# Tests spécifiques
pytest tests/test_audio_backend.py
```

---

## 📊 Métriques et Performance

### Optimisations Intégrées
- **Backend audio universel** avec sélection automatique
- **Chargement paresseux** des modules lourds
- **Cache intelligent** pour réponses TTS fréquentes
- **Threading async** pour non-bloquant
- **Préchargement GPU** CUDA optimisé

### Performance par Backend

| Backend | Latence | Offline | CPU | Qualité |
|---------|---------|---------|-----|---------|
| Vosk + sounddevice | ~100-200ms | ✅ | 5-15% | ⭐⭐⭐⭐⭐ |
| sounddevice + Google | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| PyAudio + Google | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| SpeechRecognition | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| Whisper | ~500-1000ms | ✅ | 10-30% | ⭐⭐⭐⭐⭐ |

---

## 🌐 Support Multilingue

- **Français** : Support natif et optimisé (modèle Vosk français)
- **Anglais** : Support complet
- **Espagnol, Allemand, Italien** : Support partiel
- **Extensible** : Ajout facile de nouvelles langues

---

## 🔒 Sécurité

- **Validation des entrées** pour prévenir injections
- **Stockage sécurisé** des clés API (encryption)
- **Mode sandbox** pour commandes système
- **Authentification optionnelle** interface web

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

### Problème: "Aucun microphone détecté"

**Solution:**
1. Vérifiez que votre microphone est connecté
2. Vérifiez les paramètres audio de votre système
3. Vérifiez les permissions d'accès au microphone

Pour plus d'aide, consultez [QUICKSTART_AUDIO.md](QUICKSTART_AUDIO.md)

---

## 🤝 Contribuer

Les contributions sont les bienvenues ! Voici comment participer :

### 1. Fork le projet
```bash
git clone https://github.com/votre-username/whisp-assistant.git
```

### 2. Créer une branche
```bash
git checkout -b feature/nouvelle-fonctionnalite
```

### 3. Faire les changements
- Ajouter des tests pour nouvelles fonctionnalités
- Maintenir le style de code existant (PEP 8)
- Documenter les changements

### 4. Soumettre une Pull Request
```bash
git push origin feature/nouvelle-fonctionnalite
# Créer une PR sur GitHub
```

---

## 📖 Documentation Complète

- [📘 Guide d'Installation](QUICKSTART_AUDIO.md)
- [🔧 Configuration Avancée](UNIVERSAL_AUDIO_IMPLEMENTATION.md)
- [🎤 Commandes Vocales](docs/commands.md)
- [🔌 Développement d'Extensions](docs/extensions.md)
- [🐛 Dépannage](docs/troubleshooting.md)

---

## 🗺️ Feuille de Route

### Version 2.0 (Actuelle) - ✅ TERMINE
- ✅ **Backend audio universel** avec détection automatique
- ✅ Support multiplateforme (Windows, macOS, Linux)
- ✅ Reconnaissance offline avec Vosk
- ✅ Compatible Python 3.14+
- ✅ Interface web moderne
- ✅ Automatisation système complète

### Version 2.1 (En cours)
- 🔄 Support plugins externes
- 🔄 Mode apprentissage automatique
- 🔄 Voix personnalisables avancées
- 🔄 Performance monitoring

### Version 3.0 (Futur)
- 📋 Intelligence artificielle conversationnelle
- 📋 Intégration IA avancée (LLM)
- 📋 Support multilingue étendu
- 📋 Interface mobile

---

## 📝 Licence

Ce projet est sous licence **GPL v3.0** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- **OpenAI** : Modèles Whisper et GPT
- **Google** : API Speech-to-Text et Text-to-Speech
- **Mozilla** : Projet Common Voice
- **NVIDIA** : NeMo pour GPU optimisé
- **Coqui** : Moteurs TTS open-source
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

[![GitHub stars](https://img.shields.io/github/stars/votre-username/whisp-assistant?style=social)](https://github.com/votre-username/whisp-assistant/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/votre-username/whisp-assistant?style=social)](https://github.com/votre-username/whisp-assistant/network/members)
[![GitHub issues](https://img.shields.io/github/issues/votre-username/whisp-assistant)](https://github.com/votre-username/whisp-assistant/issues)

**Reconnaissance vocale offline • Multiplateforme • Python 3.14+**

</div>
