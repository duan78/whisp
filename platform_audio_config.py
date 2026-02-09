"""
Configuration audio spécifique par plateforme
Fournit les recommandations et configurations pour chaque système d'exploitation
"""

import os
import platform
import sys
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


# Configuration par plateforme
PLATFORM_CONFIGS = {
    'windows': {
        'recommended': 'vosk_sounddevice',
        'install_cmd': 'pip install sounddevice vosk',
        'notes': 'PyAudio difficile à installer sur Windows - nécessite compilation',
        'microphone_check': True,
        'sample_rate': 16000,
        'chunk_size': 1024,
        'dtype': 'int16',
    },
    'darwin': {  # macOS
        'recommended': 'vosk_sounddevice',
        'install_cmd': 'pip install sounddevice vosk',
        'notes': 'PortAudio requis pour PyAudio. Utilisez brew install portaudio',
        'microphone_check': True,
        'sample_rate': 16000,
        'chunk_size': 1024,
        'dtype': 'int16',
    },
    'linux': {
        'recommended': 'vosk_sounddevice',
        'install_cmd': 'pip install sounddevice vosk && sudo apt-get install portaudio19-dev',
        'notes': 'Paquets système requis pour PortAudio. Pour PulseAudio: libpulse-dev',
        'microphone_check': True,
        'sample_rate': 16000,
        'chunk_size': 1024,
        'dtype': 'int16',
    }
}


def get_platform_type() -> str:
    """Retourne le type de plateforme"""
    return platform.system().lower()


def get_platform_config() -> Dict:
    """
    Retourne la configuration pour la plateforme actuelle

    Returns:
        Dictionnaire de configuration
    """
    plat = get_platform_type()
    return PLATFORM_CONFIGS.get(plat, PLATFORM_CONFIGS['linux'])  # Défaut: Linux


def get_vosk_model_path() -> Optional[str]:
    """
    Retourne le chemin vers le modèle Vosk

    Recherche dans l'ordre:
    1. models/vosk-model-small-fr-0.22 (modèle léger français)
    2. models/vosk-model-fr-0.22 (modèle complet français)
    3. ~/.vosk/vosk-model-fr-0.22
    4. ~/.vosk/vosk-model-small-fr-0.22

    Returns:
        Chemin vers le modèle ou None
    """
    possible_paths = [
        "models/vosk-model-small-fr-0.22",
        "models/vosk-model-fr-0.22",
        os.path.expanduser("~/.vosk/vosk-model-small-fr-0.22"),
        os.path.expanduser("~/.vosk/vosk-model-fr-0.22"),
        "vosk-model-small-fr-0.22",
        "vosk-model-fr-0.22",
    ]

    for path in possible_paths:
        model_path = Path(path)
        if model_path.exists() and (model_path / "am").exists():
            logger.info(f"Modèle Vosk trouvé: {path}")
            return str(model_path)

    logger.warning("Aucun modèle Vosk trouvé")
    return None


def check_microphone_available() -> bool:
    """
    Vérifie si un microphone est disponible

    Returns:
        True si un microphone est détecté
    """
    try:
        import sounddevice as sd

        # Lister les périphériques d'entrée
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]

        if input_devices:
            logger.info(f"✅ {len(input_devices)} microphone(s) détecté(s)")
            for i, dev in enumerate(input_devices):
                logger.info(f"   - {dev['name']}")
            return True
        else:
            logger.warning("❌ Aucun microphone détecté")
            return False

    except ImportError:
        logger.warning("sounddevice non disponible - impossible de vérifier le microphone")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la détection du microphone: {e}")
        return False


def get_best_input_device() -> Optional[int]:
    """
    Retourne l'ID du meilleur périphérique d'entrée

    Returns:
        ID du device ou None
    """
    try:
        import sounddevice as sd

        devices = sd.query_devices()
        input_devices = [(i, d) for i, d in enumerate(devices) if d['max_input_channels'] > 0]

        if not input_devices:
            return None

        # Priorité: devices avec 'default' dans le nom
        for dev_id, dev in input_devices:
            if 'default' in dev['name'].lower():
                logger.info(f"Device par défaut sélectionné: {dev['name']}")
                return dev_id

        # Sinon, prendre le premier
        dev_id, dev = input_devices[0]
        logger.info(f"Premier device sélectionné: {dev['name']}")
        return dev_id

    except Exception as e:
        logger.error(f"Erreur lors de la sélection du device: {e}")
        return None


def get_installation_instructions() -> str:
    """
    Retourne les instructions d'installation pour la plateforme actuelle

    Returns:
        Chaîne avec les instructions
    """
    config = get_platform_config()
    plat = get_platform_type()

    instructions = f"""
Installation des dépendances audio pour {plat.capitalize()}
{'='*60}

Recommandé: {config['recommended']}

Commande d'installation:
{config['install_cmd']}

Notes:
{config['notes']}

Modèles Vosk:
1. Téléchargez un modèle français depuis:
   https://alphacephei.com/vosk/models

2. Recommandé: vosk-model-small-fr-0.22 (~50 Mo)

3. Extrayez le modèle dans le dossier 'models/' à la racine du projet

Vérification:
python -c "import sounddevice, vosk; print('✅ Dépendances OK')"
"""

    return instructions


def get_audio_error_message(error_type: str) -> str:
    """
    Retourne un message d'erreur cohérent selon le type

    Args:
        error_type: Type d'erreur ('no_backend', 'no_microphone', 'no_model')

    Returns:
        Message d'erreur formaté
    """
    config = get_platform_config()

    messages = {
        'no_backend': f"""
╔════════════════════════════════════════════════════════════╗
║  Aucun backend audio n'est disponible                      ║
╚════════════════════════════════════════════════════════════╝

Pour installer la reconnaissance vocale:

  {config['install_cmd']}

Notes:
  {config['notes']}

Modèles Vosk:
  1. Téléchargez: https://alphacephei.com/vosk/models
  2. Extrayez dans: models/
  3. Recommandé: vosk-model-small-fr-0.22

L'assistant fonctionnera en mode web uniquement.
""",

        'no_microphone': """
╔════════════════════════════════════════════════════════════╗
║  Aucun microphone détecté                                  ║
╚════════════════════════════════════════════════════════════╝

Vérifiez:
  1. Que votre microphone est connecté
  2. Les paramètres audio de votre système
  3. Les permissions d'accès au microphone

L'assistant fonctionnera en mode web uniquement.
""",

        'no_model': """
╔════════════════════════════════════════════════════════════╗
║  Aucun modèle Vosk trouvé                                  ║
╚════════════════════════════════════════════════════════════╝

Pour installer un modèle Vosk:

  1. Téléchargez un modèle français:
     https://alphacephei.com/vosk/models

  2. Recommandé: vosk-model-small-fr-0.22 (~50 Mo)

  3. Extrayez le modèle dans: models/

     Ou utilisez le script d'installation:
     python install_vosk_model.py

L'assistant utilisera un backend online si disponible.
"""
    }

    return messages.get(error_type, "Erreur inconnue")


def check_audio_dependencies() -> Dict[str, bool]:
    """
    Vérifie quelles dépendances audio sont disponibles

    Returns:
        Dictionnaire avec le statut de chaque dépendance
    """
    dependencies = {
        'sounddevice': False,
        'vosk': False,
        'pyaudio': False,
        'microphone': False,
        'vosk_model': False
    }

    # Vérifier sounddevice
    try:
        import sounddevice
        dependencies['sounddevice'] = True
    except ImportError:
        pass

    # Vérifier vosk
    try:
        import vosk
        dependencies['vosk'] = True
    except ImportError:
        pass

    # Vérifier pyaudio
    try:
        import pyaudio
        dependencies['pyaudio'] = True
    except ImportError:
        pass

    # Vérifier microphone
    if dependencies['sounddevice']:
        dependencies['microphone'] = check_microphone_available()

    # Vérifier modèle Vosk
    dependencies['vosk_model'] = get_vosk_model_path() is not None

    return dependencies


def print_audio_status():
    """Affiche le statut des dépendances audio"""
    print("\n=== Statut des Dépendances Audio ===\n")

    deps = check_audio_dependencies()

    for dep, available in deps.items():
        icon = "✅" if available else "❌"
        print(f"  {icon} {dep}")

    print("\n" + "="*60)

    if not any([deps['sounddevice'], deps['pyaudio']]):
        print("\n⚠️ Aucun backend audio disponible")
        print(get_installation_instructions())

    if deps['vosk'] and not deps['vosk_model']:
        print("\n⚠️ Vosk est installé mais aucun modèle n'est trouvé")
        print(get_audio_error_message('no_model'))

    if not deps['microphone']:
        print(get_audio_error_message('no_microphone'))


if __name__ == "__main__":
    print_audio_status()
