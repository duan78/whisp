# 🎤 Whisp Assistant

<div align="center">

![Whisp Assistant Logo](https://img.shields.io/badge/Whisp-Assistant-blue?style=for-the-badge&logo=python)
![Python Version](https://img.shields.io/badge/python-3.8%2B-green?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/license-GPL%20v3-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=for-the-badge)

**Un assistant vocal personnel intelligent et multilingue**

[📖 Documentation](#documentation) • [🚀 Installation](#installation) • [💡 Utilisation](#utilisation) • [🔧 Configuration](#configuration) • [🤝 Contribuer](#contribuer)

</div>

## 🌟 Fonctionnalités Principales

### 🎙️ Reconnaissance Vocale Avancée
- **Multi-moteurs** : SpeechRecognition, NeMo, Whisper, Vosk
- **Support multilingue** avec optimisation française
- **Mode continu** intelligent et adaptatif
- **Optimisation CUDA** pour accélération GPU (Windows)

### 🔊 Synthèse Vocale de Haute Qualité
- **Plusieurs moteurs TTS** : pyttsx3 (offline), gTTS (online), CoquiTTS, Piper
- **Préchargement intelligent** des modèles
- **Cache audio** pour réponses rapides
- **Voices personnalisables** par langue

### 🖥️ Interface Web Complète
- **Tableau de bord** moderne et responsive
- **Configuration en temps réel**
- **Visualisation des métriques** et logs
- **Support multi-utilisateurs** avec authentification optionnelle

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

## 📋 Prérequis

- **Python 3.8+**
- **Microphone** (pour reconnaissance vocale)
- **Haut-parleurs/casque** (pour synthèse vocale)
- **Windows/macOS/Linux** (support multi-plateforme)

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
# Installation de base
pip install -r requirements.txt

# Installation optionnelle (fonctionnalités avancées)
pip install -r requirements_optional.txt
```

### 4. Configuration initiale
```bash
# Copier les fichiers de configuration
cp config.example.env config.env
cp api_keys.json.example api_keys.json

# Éditer le fichier config.env avec vos clés API
nano config.env  # ou votre éditeur préféré
```

### 5. Lancer l'assistant
```bash
python main.py
```

L'interface web sera accessible à **http://localhost:5000**

## 💡 Utilisation

### Commandes de Base
- `"Dites aide"` - Afficher l'aide générale
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

## 🔧 Configuration

### Variables d'Environnement (config.env)

```bash
# Moteurs de reconnaissance vocale
STT_ENGINE=speechrecognition  # Options: whisper, nemo, vosk

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
- **SpeechRecognition** : Support multi-API (Google, Wit.ai, etc.)
- **Whisper** : Modèles OpenAI haute précision
- **NeMo** : NVIDIA pour GPU/CPU optimisé
- **Vosk** : Reconnaissance offline légère

#### Synthèse Vocale (TTS)
- **gTTS** : Google Text-to-Speech (online)
- **pyttsx3** : Système natif (offline)
- **CoquiTTS** : Voix neuronales avancées
- **Piper** : Synthèse offline rapide

## 🏗️ Architecture

```
whisp-assistant/
├── 🎙️ Modules principaux
│   ├── main.py                    # Point d'entrée
│   ├── speech_recognition_module.py # Reconnaissance vocale
│   ├── tts_module.py              # Synthèse vocale
│   └── command_processor.py       # Cœur de traitement
├── 🖥️ Interface web
│   ├── web_interface.py           # Flask web app
│   ├── templates/                 # Templates HTML
│   └── static/                    # CSS/JS assets
├── ⚡ Modules de commande
│   ├── keyboard_commands.py       # Contrôle clavier
│   ├── mouse_commands.py          # Contrôle souris
│   ├── browser_commands.py        # Automatisation web
│   ├── system_commands.py         # Commandes système
│   ├── git_commands.py            # Intégration Git
│   └── ...                        # Autres modules
├── 🗄️ Gestion des données
│   ├── database_manager.py        # Base de données SQLite
│   ├── config.py                  # Configuration
│   └── shortcuts_database.py      # Raccourcis perso
└── 🔧 Utilitaires
    ├── error_handler.py           # Gestion d'erreurs
    ├── lazy_loader.py             # Chargement paresseux
    └── text_processing.py         # Traitement texte
```

## 🔌 API et Extensions

### Personnalisation des Commandes
```python
# Ajouter des commandes personnalisées dans shortcuts_database.py
from shortcuts_database import ajouter_raccourci_personnalise

ajouter_raccourci_personnalise(
    commande="lance ma musique",
    action="python -c 'import webbrowser; webbrowser.open(\"https://youtube.com/music\")'"
)
```

### Hooks de Personnalisation
```python
# Créer votre propre module de commande
class MonModuleCommande(BaseCommandModule):
    def executer_commande(self, commande):
        # Logique personnalisée ici
        pass
```

## 📊 Métriques et Performance

### Optimisations Intégrées
- **Chargement paresseux** des modules lourds
- **Cache intelligent** pour réponses TTS fréquentes
- **Threading async** pour non-bloquant
- **Préchargement GPU** CUDA optimisé

### Métriques Disponibles
- **Temps de reconnaissance** STT
- **Latence TTS** par réponse
- **Utilisation CPU/GPU**
- **Taux de succès** des commandes

## 🌐 Support Multilingue

- **Français** : Support natif et optimisé
- **Anglais** : Support complet
- **Espagnol, Allemand, Italien** : Support partiel
- **Extensible** : Ajout facile de nouvelles langues

## 🔒 Sécurité

- **Validation des entrées** pour prévenir injections
- **Stockage sécurisé** des clés API
- **Mode sandbox** pour commandes système
- **Authentification optionnelle** interface web

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
- Maintenir le style de code existant
- Documenter les changements

### 4. Soumettre une Pull Request
```bash
git push origin feature/nouvelle-fonctionnalite
# Créer une PR sur GitHub
```

### Guidelines de Contribution
- ✅ Code respectant PEP 8
- ✅ Tests pour nouvelles fonctionnalités
- ✅ Documentation mise à jour
- ✅ Messages de commit clairs

## 🐛 Rapport de Bugs

Pour signaler un bug :

1. **Vérifier** si le bug existe déjà
2. **Créer une issue** avec :
   - Description détaillée
   - Étapes de reproduction
   - Configuration système
   - Logs d'erreur

## 📖 Documentation Complète

- [📘 Guide d'Installation](docs/installation.md)
- [🔧 Configuration Avancée](docs/configuration.md)
- [🎤 Commandes Vocales](docs/commands.md)
- [🔌 Développement d'Extensions](docs/extensions.md)
- [🐛 Dépannage](docs/troubleshooting.md)

## 🗺️ Feuille de Route

### Version 1.0 (Actuelle)
- ✅ Reconnaissance vocale multi-moteurs
- ✅ Synthèse vocale avancée
- ✅ Interface web complète
- ✅ Automatisation système

### Version 1.1 (En cours)
- 🔄 Support plugins externe
- 🔄 Mode apprendissage automatique
- 🔄 Voix personnalisables

### Version 2.0 (Futur)
- 📋 Intelligence artificielle conversationnelle
- 📋 Intégration IA avancée
- 📋 Support multilingue étendu

## 📝 Licence

Ce projet est sous licence **GPL v3.0** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI** : Modèles Whisper et GPT
- **Google** : API Speech-to-Text et Text-to-Speech
- **Mozilla** : Projet Common Voice
- **NVIDIA** : NeMo pour GPU optimisé
- **Coqui** : Moteurs TTS open-source

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

</div>