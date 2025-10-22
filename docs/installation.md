# Guide d'Installation Complet

## 🚀 Installation en 3 étapes simples

### Prérequis Système
- **Windows 10+** (recommandé) ou **macOS 10.15+** ou **Ubuntu 20.04+**
- **Python 3.8+** (Python 3.10+ recommandé)
- **RAM** : 4GB minimum (8GB recommandé)
- **Stockage** : 2GB d'espace libre
- **Microphone** : Intégré ou USB
- **Haut-parleurs** : Pour écouter les réponses

---

## Étape 1: Cloner le Repository

```bash
git clone https://github.com/duan78/whisp.git
cd whisp-assistant
```

---

## Étape 2: Installation des Dépendances

```bash
# Créer un environnement virtuel (recommandé)
python -m venv venv

# Activer l'environnement
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

Pour le support GPU (optionnel) :
```bash
pip install -e ".[gpu]"
```

Pour les outils de développement (optionnel) :
```bash
pip install -e ".[dev]"
```

---

## Étape 3: Configuration Initiale

### Copier les fichiers de configuration

```bash
# Copier les templates de configuration
cp config.example.env config.env
cp api_keys.json.example api_keys.json
```

### Éditer la configuration

```bash
# Ouvrir le fichier de configuration
nano config.env  # ou votre éditeur préféré
```

Configuration minimale requise dans `config.env` :
```env
# Moteurs de reconnaissance vocale
STT_ENGINE=speechrecognition  # Options: speechrecognition, whisper, nemo, vosk
TTS_ENGINE=gtts              # Options: gtts, pyttsx3, coqui, piper
LANGUAGE=fr-FR                # Langue par défaut

# Interface web
WEB_PORT=5000
WEB_HOST=127.0.0.1

# Configuration audio
MAX_AUDIO_LENGTH=60
COMMAND_TIMEOUT=30
COMMAND_THREADS=4

# Niveau de logs
LOG_LEVEL=INFO
```

### Configuration des clés API (optionnel)

Si vous souhaitez utiliser les fonctionnalités avancées avec IA :

```bash
# Éditer api_keys.json
nano api_keys.json
```

Ajoutez vos clés API personnelles :
```json
{
  "openai_api_key": "sk-your-openai-api-key-here",
  "mistral_api_key": "your-mistral-api-key-here"
}
```

---

## Étape 4: Vérification de l'Installation

### Test des modules principaux

```bash
# Tester la reconnaissance vocale
python -c "import speech_recognition_module; print('✅ Module STT OK')"

# Tester la synthèse vocale
python -c "import tts_module; print('✅ Module TTS OK')"

# Tester l'interface web
python -c "import web_interface; print('✅ Interface web OK')"
```

### Test rapide du microphone

```bash
# Créer un script de test
cat > test_micro.py << 'EOF'
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
EOF

# Exécuter le test
python test_micro.py
```

---

## Étape 5: Lancer Whisp Assistant

```bash
# Lancer l'assistant
python main.py
```

L'interface web sera accessible à : **http://localhost:5000**

---

## 📋 Instructions par Plateforme

### Windows 10/11

#### Installation avec PowerShell (recommandé)

```powershell
# Installer Chocolatey si pas déjà installé
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Installer les dépendances
choco install python
choco install ffmpeg
choco install portaudio

# Vérifier l'installation
python --version
pip --version
```

#### Installation manuelle

1. **Télécharger Python** : https://www.python.org/downloads/
2. **Installer FFmpeg** : https://ffmpeg.org/download.html
3. **Installer PortAudio** : https://www.portaudio.com/download/

### macOS

#### Installation avec Homebrew

```bash
# Installer Homebrew si pas déjà fait
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer les dépendances
brew install python@3.10
brew install portaudio
brew install ffmpeg
```

### Linux (Ubuntu/Debian)

```bash
# Mettre à jour les paquets
sudo apt update && sudo apt upgrade -y

# Installer Python et outils
sudo apt install python3.10 python3.10-pip python3.10-venv git
sudo apt install portaudio19-dev python3-pyaudio ffmpeg

# Installer dépendances X11 (pour contrôle fenêtres)
sudo apt install python3-xlib python3-tk python3-dev

# Configuration des permissions audio
sudo usermod -a -G audio $USER
newgrp audio
```

---

## 🎯 Installation Rapide via pip

Quand le projet sera publié sur PyPI :

```bash
pip install whisp-assistant
```

---

## 🔧 Configuration Avancée

### Reconnaissance Vocale (STT)

#### SpeechRecognition (recommandé pour débuter)

```env
STT_ENGINE=speechrecognition
```

#### Whisper (plus précis, nécessite GPU)

```env
STT_ENGINE=whisper
OPENAI_API_KEY=sk-your-key-here
WHISPER_MODEL=base        # tiny, base, small, medium, large
WHISPER_LANGUAGE=fr
```

#### NeMo (GPU optimisé)

```env
STT_ENGINE=nemo
CUDA_VISIBLE_DEVICES=0
```

### Synthèse Vocale (TTS)

#### gTTS (recommandé, online)

```env
TTS_ENGINE=gtts
```

#### pyttsx3 (offline, pas de connexion internet requise)

```env
TTS_ENGINE=pyttsx3
TTS_VOICE_RATE=200
TTS_VOICE_VOLUME=0.9
```

#### CoquiTTS (voix neuronales)

```env
TTS_ENGINE=coqui
COQUI_MODEL_NAME=tts_models/fr/multi-dataset-female
```

---

## 🛠️ Dépannage

### Problèmes Courants

#### ModuleNotFoundError

```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

#### Erreur Microphone

1. **Vérifier les permissions système**
2. **Tester avec un autre logiciel**
3. **Réinstaller les drivers audio**
4. **Redémarrer l'ordinateur**

#### Problèmes de Performance

1. **Activer le support GPU** si disponible
2. **Utiliser des modèles plus légers**
3. **Augmenter la RAM système**
4. **Fermer les applications inutilisées**

---

## ✅ Vérification Finale

Après l'installation, vérifiez que tout fonctionne :

```bash
# Test complet
python -c "
import speech_recognition_module
import tts_module
import web_interface
print('🎉 Whisp Assistant est prêt !')
print('📍 Interface web : http://localhost:5000')
print('📚 Documentation : https://github.com/duan78/whisp/blob/main/docs/installation.md')
"
```

---

## 🎉 Félicitations !

Vous avez maintenant **Whisp Assistant** d'installé et prêt à utiliser !

### Prochaines Étapes

1. **Consultez le [Guide d'Utilisation](../utilisation.md)**
2. **Explorez les [fonctionnalités avancées](../configuration.md)**
3. **Rejoignez la [communauté](https://github.com/duan78/whisp/discussions)**

### Besoin d'Aide ?

- 📖 **Documentation complète** : https://docs.whisp-assistant.com
- 🐛 **Issues** : https://github.com/duan78/whisp/issues
- 💬 **Discord** : https://discord.gg/whisp
- 📧 **Email support** : support@whisp-assistant.com

---

*Installation testée sur Windows 10, macOS 13 et Ubuntu 22.04*