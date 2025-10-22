# Guide d'Installation

Ce guide vous aidera à installer et configurer Whisp Assistant sur votre système.

## Prérequis

### Systèmes Supportés
- **Windows 10+** (recommandé)
- **macOS 10.15+**
- **Ubuntu 20.04+** ou équivalent

### Configuration Matérielle Minimum
- **RAM** : 4GB (8GB recommandé)
- **Stockage** : 2GB d'espace libre
- **Microphone** : Intégré ou externe
- **Haut-parleurs** : Pour les réponses vocales

### Logiciels Requis
- **Python 3.8+** (Python 3.10+ recommandé)
- **pip** (gestionnaire de paquets Python)
- **Git** (pour cloner le repository)

## Méthode 1: Installation depuis GitHub

### 1. Cloner le Repository

```bash
git clone https://github.com/votre-username/whisp-assistant.git
cd whisp-assistant
```

### 2. Créer un Environnement Virtuel

```bash
# Créer l'environnement
python -m venv venv

# Activer l'environnement

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Installer les Dépendances

```bash
# Installation des dépendances de base
pip install -r requirements.txt

# Pour le support GPU (optionnel, recommandé)
pip install -e ".[gpu]"

# Pour les outils de développement (optionnel)
pip install -e ".[dev]"
```

### 4. Configuration Initiale

```bash
# Copier les fichiers de configuration
cp config.example.env config.env
cp api_keys.json.example api_keys.json
```

#### Éditer config.env
```bash
nano config.env  # ou votre éditeur préféré
```

Configuration minimale requise :
```env
# Moteurs de reconnaissance et synthèse
STT_ENGINE=speechrecognition
TTS_ENGINE=gtts

# Interface web
WEB_PORT=5000
WEB_HOST=127.0.0.1

# Niveau de logs
LOG_LEVEL=INFO
```

#### Éditer api_keys.json (optionnel)
```json
{
  "openai_api_key": "sk-your-openai-api-key-here",
  "mistral_api_key": "your-mistral-api-key-here"
}
```

### 5. Vérifier l'Installation

```bash
python -c "import speech_recognition_module; print('✅ Module STT OK')"
python -c "import tts_module; print('✅ Module TTS OK')"
python -c "import web_interface; print('✅ Interface web OK')"
```

### 6. Lancer l'Assistant

```bash
python main.py
```

L'interface web sera accessible à http://localhost:5000

## Méthode 2: Installation via pip (quand disponible)

```bash
pip install whisp-assistant
```

## Installation Détaillée par Plateforme

### Windows

#### Dépendances Système
```powershell
# Installer chocolately si pas déjà fait
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Installer FFmpeg
choco install ffmpeg

# Installer PortAudio (optionnel, recommandé)
choco install portaudio
```

#### Installation Python
```powershell
# Télécharger et installer Python depuis python.org
# Assurer "Add Python to PATH" est coché

# Vérifier l'installation
python --version
pip --version
```

#### Variables d'Environnement
Ajouter au PATH si nécessaire :
- `C:\Python39\Scripts`
- `C:\Python39`

### macOS

#### Dépendances avec Homebrew
```bash
# Installer Homebrew si pas déjà fait
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer dépendances
brew install python@3.10
brew install portaudio
brew install ffmpeg
```

#### Configuration Audio
```bash
# Autoriser l'accès au microphone dans Préférences Système > Sécurité & Confidentialité
```

### Linux (Ubuntu/Debian)

#### Dépendances Système
```bash
# Mettre à jour les paquets
sudo apt update && sudo apt upgrade -y

# Installer Python et outils
sudo apt install python3.10 python3.10-pip python3.10-venv git

# Installer dépendances audio
sudo apt install portaudio19-dev python3-pyaudio ffmpeg

# Installer dépendances X11 (pour contrôle fenêtres)
sudo apt install python3-xlib python3-tk python3-dev
```

#### Permissions Audio
```bash
# Ajouter l'utilisateur au groupe audio
sudo usermod -a -G audio $USER

# Recharger les groupes (ou redémarrer)
newgrp audio
```

## Configuration des Moteurs

### Speech Recognition (STT)

#### SpeechRecognition (recommandé pour débuter)
```env
STT_ENGINE=speechrecognition
```

Aucune configuration supplémentaire requise.

#### Whisper (plus précis)
```env
STT_ENGINE=whisper
OPENAI_API_KEY=sk-your-key-here
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_LANGUAGE=fr
```

#### NeMo (GPU optimisé)
```env
STT_ENGINE=nemo
CUDA_VISIBLE_DEVICES=0
```

### Text-to-Speech (TTS)

#### gTTS (recommandé)
```env
TTS_ENGINE=gtts
```

#### pyttsx3 (offline)
```env
TTS_ENGINE=pyttsx3
TTS_VOICE_RATE=200
TTS_VOICE_VOLUME=0.9
```

#### CoquiTTS (voix neuronales)
```env
TTS_ENGINE=coqui
COQUI_MODEL_NAME=tts_models/fr/mai/tacotron2-DDC
```

## Test de l'Installation

### Test Microphone

```python
# test_microphone.py
import speech_recognition as sr

recognizer = sr.Recognizer()
with sr.Microphone() as source:
    print("Parlez dans le microphone...")
    audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="fr-FR")
        print(f"Reconnu: {text}")
    except sr.UnknownValueError:
        print("Non compris")
    except sr.RequestError as e:
        print(f"Erreur: {e}")
```

### Test Synthèse Vocale

```python
# test_tts.py
from tts_module import lire_texte

lire_texte("Bonjour, je suis Whisp Assistant")
```

### Test Interface Web

```python
# test_web.py
from web_interface import start_web_server
import threading

server_thread = threading.Thread(target=start_web_server)
server_thread.daemon = True
server_thread.start()

print("Interface web démarrée sur http://localhost:5000")
input("Appuyez sur Entrée pour arrêter...")
```

## Dépannage

### Problèmes Courants

#### Erreur "ModuleNotFoundError"
```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Vérifier l'environnement virtuel
which python  # Linux/macOS
where python  # Windows
```

#### Erreur Microphone
- Vérifier les permissions système
- Tester avec un autre logiciel
- Réinitialiser les drivers audio

#### Erreur PortAudio
```bash
# Linux
sudo apt install portaudio19-dev python3-pyaudio

# macOS
brew install portaudio

# Windows
pip install pipwin
pipwin install pyaudio
```

#### Performance Faible
- Activer le support GPU si disponible
- Utiliser des modèles plus légers
- Augmenter la RAM système

### Obtenir de l'Aide

- **Documentation complète** : https://docs.whisp-assistant.com
- **Issues GitHub** : https://github.com/votre-username/whisp-assistant/issues
- **Discord** : https://discord.gg/whisp
- **Email support** : support@whisp-assistant.com

## Mise à Jour

```bash
# Depuis GitHub
git pull origin main
pip install -r requirements.txt

# Via pip (quand disponible)
pip install --upgrade whisp-assistant
```

## Prochaine Étape

Une fois l'installation réussie, consultez le [Guide d'Utilisation](utilisation.md) pour commencer à utiliser Whisp Assistant.