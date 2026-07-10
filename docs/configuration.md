# 🔧 Configuration Avancée

## 📋 Table des Matières

- [Paramètres Audio](#configuration-audio)
- [Moteurs STT](#configuration-stt)
- [Moteurs TTS](#configuration-tts)
- [Intégrations API](#configuration-api)
- [Variables d'Environnement](#configuration-environnement)
- [Optimisations GPU](#configuration-gpu)
- [Personnalisation](#configuration-personnalisation)
- [Dépannage](#configuration-depannage)

---

## 🎙️ Configuration Audio

### Paramètres Audio de Base

Ces paramètres contrôlent les flux audio entrants et sortants.

```bash
# Configuration audio par défaut
MAX_AUDIO_LENGTH=60      # Durée maximale en secondes
AUDIO_SAMPLE_RATE=16000   # Taux d'échantillonage (Hz)
CHANNELS=1               # Audio stéréo (1=mono, 2=stéréo)
AUDIO_FORMAT=WAV          # Format des fichiers temporaires
```

### Configuration des Haut-parleurs

```bash
# Volume système (0-100)
SYSTEM_VOLUME=80

# Volume par défaut pour les réponses vocales
TTS_VOICE_VOLUME=0.9

# Ajustement fin
VOLUME_STEP=5
```

---

## 🎤 Reconnaissance Vocale (STT)

### Moteurs STT Disponibles

| Moteur | Description | Requis | Performance |
|--------|------------|--------|---------|------------|
| **SpeechRecognition** | API Google (online) | Microphone | Bonne |
| **Whisper** | Modèles OpenAI (offline) | Microphone + GPU recommandé | Excellente |
| **Vosk** | Reconnaissance offline légère | Microphone | Moyenne |
| **whisper_ct2** | Whisper accéléré via CTranslate2 (offline) | Microphone + GPU recommandé | Excellente |
| **whisper_french** | Whisper spécialisé français (offline) | Microphone + GPU recommandé | Excellente |

### Configuration des Moteurs

#### SpeechRecognition (Recommandé)

```env
# Configuration SpeechRecognition
STT_ENGINE=speechrecognition
STT_LANGUAGE=fr-FR
STT_TIMEOUT=10
STT_ENERGY_THRESHOLD=300
STT_DYNAMIC_ENERGY_THRESHOLD=False
STT_PAUSE_THRESHOLD=0.8
```

#### Whisper (Plus précis, nécessite GPU)

```env
# Configuration Whisper
STT_ENGINE=whisper
WHISPER_MODEL=base             # tiny, base, small, medium, large
WHISPER_LANGUAGE=fr
OPENAI_API_KEY=votre_clé_ici    # Requis pour Whisper
WHISPER_DEVICE=cuda              # cuda, cpu (auto)
WHISPER_COMPUTE_TYPE=float16
```

#### Vosk (Offline léger)

```env
# Configuration Vosk
STT_ENGINE=vosk
VOSK_MODEL_PATH=./models/vosk-model-fr/0.4/2
```

---

## 🔊 Synthèse Vocale (TTS)

### Moteurs TTS Disponibles

| Moteur | Description | Requis | Performance | Qualité |
|--------|------------|--------|-----------|---------|
| **Edge-TTS** | Microsoft Edge (online, recommandé) | Connexion internet | Excellente | Très naturelle |
| **gTTS** | Google Text-to-Speech (online) | Connexion internet | Bonne | Naturelle |
| **pyttsx3** | Système natif (offline) | Aucun | Moyenne | Robotique |
| **Piper** | Synthèse rapide (offline) | Aucun | Excellente | Très claire |
| **CoquiTTS** | Voix neuronales (online) | Connexion + GPU | Bonne | Très humaine |

### Configuration des Moteurs

#### Edge-TTS (Recommandé, online, voix naturelles)

```env
# Configuration Edge-TTS
TTS_ENGINE=edge_tts
EDGE_TTS_VOICE=fr-FR-DeniseNeural   # Voix neuronale française
EDGE_TTS_RATE=+0%                    # Vitesse (ex: +10%, -10%)
EDGE_TTS_VOLUME=+0%                  # Volume (ex: +20%, -20%)
```

#### gTTS (Online)

```env
# Configuration gTTS
TTS_ENGINE=gtts
GTTT_LANGUAGE=fr
GTTT_SLOW=false         # false=normal, true=lent
GTTT_TLD=com
```

#### pyttsx3 (Offline)

```env
# Configuration pyttsx3
TTS_ENGINE=pyttsx3
TTS_VOICE_ID=1          # ID de la voix (varie par système)
TTS_VOICE_RATE=200        # Mots par minute (150-200)
TTS_VOICE_VOLUME=0.9     # Volume (0.0-1.0)
```

#### Piper (Synthèse ultra-rapide)

```env
# Configuration Piper
TTS_ENGINE=piper
PIPER_MODEL_PATH=./models/piper_fr.onnx
PIPER_VOICE_SPEED=1.0     # 0.1=rapide, 1.0=normale
PIPER_NOISE_SCALE=0.667    # Réduction du bruit
```

#### CoquiTTS (Voix neuronales avancées)

```env
# Configuration CoquiTTS
TTS_ENGINE=coqui
COQUI_MODEL_NAME=tts_models/fr/multi-dataset-female
COQUI_VOICE_SPEED=1.0
COQUI_VOICE_VARIANCE=0.0   # 0.0=par défaut
```

---

## 🔌 Intégrations API

### Clés API pour Fonctionnalités Avancées

Les clés API permettent d'accéder à des fonctionnalités supplémentaires comme :

- **Traitement du langage naturel** avec OpenAI/Mistral
- **Voix neuronales personnalisées** avec CoquiTTS
- **Reconnaissance améliorée** avec Whisper premium
- **Traduction automatique** via API
- **Analyse contextuelle** intelligente

### Configuration des Clés API

```bash
# Template de configuration API
OPENAI_API_KEY=sk-your-openai-api-key-here
MISTRAL_API_KEY=your-mistral-api-key-here
COQUI_API_KEY=your-coqui-api-key-here
GOOGLE_TRANSLATE_API_KEY=your-google-translate-key-here
```

### Sécurité des Clés API

```bash
# Méthodes de sécurisation recommandées
1. Utiliser des variables d'environnement
2. Ne jamais inclure les clés dans le code source
3. Rotation régulière des clés
4. Limiter les permissions des clés API
5. Surveiller l'utilisation via les logs
```

---

## 🖥️ Variables d'Environnement

### Liste Complète

| Variable | Description | Valeur par Défaut | Usage |
|----------|------------|-------------------|-------|
| `STT_ENGINE` | Moteur reconnaissance vocale | speechrecognition | Définit le moteur STT |
| `TTS_ENGINE` | Moteur synthèse vocale | gtts | Définit le moteur TTS |
| `LANGUAGE` | Langue principale | fr-FR | Langue pour reconnaissance/synthèse |
| `WEB_PORT` | Port interface web | 5000 | Port d'accès à l'interface |
| `WEB_HOST` | Hôte interface web | 127.0.0.1 | Interface locale seulement |
| `MAX_AUDIO_LENGTH` | Durée audio max | 60 | Durée maximale en secondes |
| `COMMAND_TIMEOUT` | Timeout commandes | 30 | Timeout pour commandes système |
| `COMMAND_THREADS` | Threads parallèles | 4 | Nombre de threads simultanés |
| `LOG_LEVEL` | Niveau de logs | INFO | Niveau: DEBUG, INFO, WARNING, ERROR |
| `DEBUG` | Mode débogage | false | Active les logs détaillés |

### Variables GPU

| Variable | Description | Valeur par Défaut | Usage |
|----------|------------|-------------------|-------|
| `CUDA_VISIBLE_DEVICES` | GPU NVIDIA | (vide) | Auto-détection GPU |
| `WHISPER_DEVICE` | Appareil Whisper | cpu | cpu ou cuda |

### Variables de Personnalisation

| Variable | Description | Exemple | Usage |
|----------|------------|---------|-------|
| `CUSTOM_TTS_VOICE` | Voix personnalisée | female | Voix masculine/féminine |
| `CUSTOM_STT_ACCENT` | Accent STT | french | Accent pour reconnaissance |
| `CUSTOM_PROMPT_PREFIX` | Préfixe commande | Jarvis | Préfixe personnalisé |

---

## 🚀 Optimisations GPU

### Activation du Support GPU

Pour activer l'accélération matérielle :

```bash
# Detection automatique du GPU
export CUDA_VISIBLE_DEVICES=0

# Optimisation pour PyTorch
export TORCH_CUDA_ARCH_LIST=6.0  # Pour RTX 20xx/30xx
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Configuration des Modèles

```bash
# Modèles Whisper optimisés
WHISPER_MODEL=small      # Plus précis que base
WHISPER_COMPUTE_TYPE=float16
```

---

## 🔧 Personnalisation

### Thèmes Vocaux

#### Voix Masculines

```env
TTS_VOICE_ID=2          # Voix masculine profonde
TTS_VOICE_RATE=180        # Parle plus lentement
TTS_VOICE_VOLUME=1.0      # Volume légèrement plus élevé
```

#### Voix Féminines

```env
TTS_VOICE_ID=3          # Voix féminine douce
TTS_VOICE_RATE=220        # Parle plus rapidement
TTS_VOICE_VOLUME=0.8      # Volume légèrement plus faible
```

#### Voix Robotiques

```env
TTS_VOICE_ID=4          # Voix synthétique
TTS_VOICE_RATE=150        # Débit robotique
TTS_VOICE_VOLUME=0.7      # Volume métallique
```

### Personnalisation Avancée

#### Scripts de Configuration Automatique

```python
# Exemple de script de personnalisation
def configurer_voix_personnalisee():
    """
    Script pour configurer une voix personnalisée
    via les variables d'environnement de configuration.
    """
    import os

    # Demander les préférences utilisateur
    print("=== Configuration de Voix Personnalisée ===")
    print("1. Moteur TTS (edge_tts, pyttsx3, piper, ...)")
    tts_engine = input("Moteur : ").strip() or "edge_tts"

    print("2. Voix / ID de voix (dépend du moteur)")
    voice = input("Voix : ").strip()

    print("3. Vitesse (ex: pyttsx3 -> mots/minute, edge_tts -> +10%)")
    rate = input("Vitesse : ").strip()

    # Appliquer la configuration via config.env / variables d'environnement
    os.environ["TTS_ENGINE"] = tts_engine
    if voice:
        os.environ["EDGE_TTS_VOICE"] = voice      # pour Edge-TTS
        os.environ["TTS_VOICE_ID"] = voice        # pour pyttsx3
    if rate:
        os.environ["EDGE_TTS_RATE"] = rate        # pour Edge-TTS
        os.environ["TTS_VOICE_RATE"] = rate       # pour pyttsx3

    print("✅ Configuration appliquée via les variables d'environnement !")

if __name__ == "__main__":
    configurer_voix_personnalisee()
```

---

## 🛠️ Dépannage

### Solutions aux Problèmes Courants

#### Problèmes de Reconnaissance Vocale

**Symptôme** : Microphone non détecté
```bash
# Solutions
# 1. Vérifier les permissions du microphone
ls -l /dev/snd/

# 2. Tester avec un autre logiciel
arecord -d 5
python -c "import sounddevice as sd; print(sd.getDefaultInputDevice())"

# 3. Réinstaller les drivers audio
sudo apt-get install --reinstall alsa-base pulseaudio
```

**Symptôme** : Reconnaissance imprécise
```bash
# Solutions
# Améliorer l'acoustique
sudo apt-get install noise-cancelling
export STT_ENERGY_THRESHOLD=200

# Utiliser des modèles plus performants
export WHISPER_MODEL=base
export WHISPER_LANGUAGE=fr
```

#### Problèmes de Synthèse Vocale

**Symptôme** : Pas de son
```bash
# Solutions
# Vérifier le volume système
pactl list

# Tester un autre moteur TTS
TTS_ENGINE=edge_tts python main.py

# Vérifier la configuration audio
python -c "
import pyttsx3
engine = pyttsx3.init()
print('Voix disponibles :', [v.id for v in engine.getProperty('voices')])
"
```

**Symptôme** : Qualité audio faible
```bash
# Solutions
# Améliorer la qualité
export TTS_VOICE_RATE=150
export TTS_VOICE_VOLUME=1.0

# Utiliser des haut-parleurs externes
export TTS_EXTERNAL_DEVICE=hw:0,0
```

#### Problèmes d'Interface Web

**Symptôme** : Interface inaccessible
```bash
# Solutions
# Changer le port
export WEB_PORT=5001

# Vérifier le firewall
sudo ufw allow 5001/tcp

# Redémarrer l'application
python main.py
```

**Symptôme** : Erreur 500
```bash
# Solutions
# Vérifier les logs
tail -f logs/whisp.log | grep ERROR

# Redémarrer en mode debug
export LOG_LEVEL=DEBUG
python main.py
```

---

## 📊 Monitoring et Statistiques

### Métriques Disponibles

Le système peut tracker différentes métriques de performance :

```bash
# Activer le monitoring détaillé
export METRICS_ENABLED=true
export METRICS_UPDATE_INTERVAL=60
```

### Statistiques en Temps Réel

```python
# Script de monitoring des performances
import time
import psutil

def monitor_system():
    while True:
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{timestamp}] CPU: {cpu}%, RAM: {memory}%")
        time.sleep(30)

if __name__ == "__main__":
    monitor_system()
```

### Journalisation Structurée

```bash
# Configuration des logs avancés
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_DATE_FORMAT=%Y-%m-%d
LOG_MAX_SIZE=100MB
LOG_ROTATION=daily
```

---

## 🎯 Bonnes Pratiques

### Recommandations

1. **Utiliser des mots-clairs clairs**
   - Éviter les ambigüités dans les commandes vocales
   - Préférez "Ouvre Chrome" plutôt que "Lance le navigateur web"

2. **Configurer pour l'environnement**
   - Adapter la langue et les voix aux préférences
   - Utiliser des volumes adaptés à l'heure

3. **Tester avant utilisation**
   - Vérifier le microphone et les haut-parleurs
   - Tester la reconnaissance et la synthèse

4. **Maintenir à jour**
   - Mettre à jour les dépendances régulièrement
   - Surveiller les performances du système

---

*Ce guide couvre toutes les options de configuration avancées de Whisp Assistant. Pour une configuration de base, référez-vous au [Guide d'Installation](installation.md).*