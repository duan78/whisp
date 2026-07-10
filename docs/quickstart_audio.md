# Guide de Démarrage Rapide - Backend Audio Universel

## Installation Rapide

```bash
# 1. Installer les dépendances
pip install sounddevice vosk

# 2. Télécharger un modèle Vosk français
# https://alphacephei.com/vosk/models
# Recommandé: vosk-model-small-fr-0.22 (~50 Mo)

# 3. Extraire le modèle dans le dossier models/
# Votre structure devrait ressembler à:
# whisp/
#   ├── models/
#   │   └── vosk-model-small-fr-0.22/
#   │       ├── am/
#   │       ├── conf/
#   │       ├── graph/
#   │       └── ...
#   ├── main.py
#   └── ...

# 4. Tester l'installation
python test_universal_audio.py

# 5. Lancer l'assistant
python main.py
```

## Résolution de Problèmes

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

### Problème: sounddevice ne s'installe pas sur Linux

**Solution:**
```bash
sudo apt-get install libportaudio2
pip install sounddevice
```

### Problème: sounddevice ne s'installe pas sur macOS

**Solution:**
```bash
brew install portaudio
pip install sounddevice
```

## Test du Système

```bash
# Test complet
python test_universal_audio.py

# Attendu:
# ✅ sounddevice: disponible
# ✅ vosk: disponible
# ✅ microphone: disponible
# ✅ vosk_model: disponible
# ✅ Backend sélectionné: vosk_sounddevice
```

## Utilisation Avancée

### Forcer un Backend Spécifique

```python
from core.config import set_audio_backend

# Vosk + sounddevice (recommandé)
set_audio_backend("vosk_sounddevice")

# sounddevice + Google Speech
set_audio_backend("sounddevice_google")

# PyAudio + Google Speech
set_audio_backend("pyaudio_google")

# Web only (pas de reconnaissance vocale)
set_audio_backend("web_only")

# Auto (sélection automatique)
set_audio_backend("auto")
```

### Vérifier le Backend Actif

```python
from universal_audio_backend import get_universal_backend

backend = get_universal_backend()
info = backend.get_backend_info()

print(f"Backend actuel: {info['current_backend']}")
print(f"Plateforme: {info['platform']}")
print(f"Backends disponibles: {len([b for b in info['available_backends'] if b['status'] == 'available'])}")
```

## Compatibilité

| Plateforme | Python | Vosk + sounddevice | PyAudio |
|-----------|--------|-------------------|---------|
| Windows 10/11 | 3.8-3.14+ | ✅ Recommandé | ⚠️ Difficile |
| Linux (Ubuntu/Debian) | 3.8+ | ✅ Recommandé | ⚠️ PortAudio requis |
| macOS 10.15+ | 3.8+ | ✅ Recommandé | ⚠️ PortAudio requis |

## Performance

| Backend | Latence | Offline | CPU | Qualité |
|---------|---------|---------|-----|---------|
| Vosk + sounddevice | ~100-200ms | ✅ | 5-15% | ⭐⭐⭐⭐⭐ |
| sounddevice + Google | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| PyAudio + Google | ~300-500ms | ❌ | 1-5% | ⭐⭐⭐⭐ |
| Web only | N/A | N/A | 0% | N/A |

## Support

Pour plus d'informations, consultez:
- `UNIVERSAL_AUDIO_IMPLEMENTATION.md` - Documentation complète
- `test_universal_audio.py` - Tests et diagnostics
- `universal_audio_backend.py` - Code source
- `platform_audio_config.py` - Configuration par plateforme
