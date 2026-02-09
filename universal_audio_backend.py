"""
Backend Audio Universel pour Whisp Assistant
Système unifié avec détection automatique et fallbacks intelligents
"""

import sys
import os
import platform
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import Enum

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackendStatus(Enum):
    """Statut des backends audio"""
    AVAILABLE = "available"
    MISSING_DEPENDENCY = "missing_dependency"
    NO_MICROPHONE = "no_microphone"
    ERROR = "error"


class AudioBackend:
    """Représente un backend audio disponible"""

    def __init__(self, name: str, priority: int, offline: bool = False,
                 setup_func: Optional[Callable] = None, check_func: Optional[Callable] = None):
        self.name = name
        self.priority = priority
        self.offline = offline
        self.setup_func = setup_func
        self.check_func = check_func
        self.status = BackendStatus.AVAILABLE
        self.error_message = None

    def is_available(self) -> bool:
        """Vérifie si le backend est disponible"""
        if self.check_func:
            try:
                available, error = self.check_func()
                self.status = BackendStatus.AVAILABLE if available else BackendStatus.MISSING_DEPENDENCY
                self.error_message = error
                return available
            except Exception as e:
                self.status = BackendStatus.ERROR
                self.error_message = str(e)
                return False
        return True

    def setup(self) -> Tuple[bool, Any]:
        """Initialise le backend"""
        if self.setup_func:
            try:
                result = self.setup_func()
                return True, result
            except Exception as e:
                self.status = BackendStatus.ERROR
                self.error_message = str(e)
                logger.error(f"Erreur lors de l'initialisation de {self.name}: {e}")
                return False, None
        return True, None


class UniversalAudioBackend:
    """
    Backend audio universel avec fallbacks intelligents

    Priorité des backends:
    1. Vosk + sounddevice (recommandé, offline)
    2. sounddevice + Google Speech (online)
    3. PyAudio + Google Speech (si disponible)
    4. Web only (pas de reconnaissance vocale)
    """

    def __init__(self):
        self.backends: List[AudioBackend] = []
        self.current_backend: Optional[AudioBackend] = None
        self.current_engine = None
        self.platform = platform.system()
        self.python_version = sys.version_info

        logger.info(f"Initialisation du backend audio universel (Platform: {self.platform}, Python: {self.python_version.major}.{self.python_version.minor})")

        # Détecter les backends disponibles
        self._detect_available_backends()

    def _detect_available_backends(self):
        """Détecte tous les backends disponibles sur le système"""

        # 1. Vosk + sounddevice (recommandé, offline)
        def check_vosk_sounddevice():
            try:
                import sounddevice
                import vosk
                return True, None
            except ImportError as e:
                missing = []
                try:
                    import sounddevice
                except ImportError:
                    missing.append("sounddevice")
                try:
                    import vosk
                except ImportError:
                    missing.append("vosk")
                return False, f"Manquant: {', '.join(missing)}"

        def setup_vosk_sounddevice():
            from vosk_sounddevice_stt import create_vosk_engine
            from platform_audio_config import get_vosk_model_path

            model_path = get_vosk_model_path()
            engine = create_vosk_engine(model_path)
            logger.info("✅ Backend Vosk + sounddevice initialisé")
            return engine

        vosk_backend = AudioBackend(
            name='vosk_sounddevice',
            priority=1,
            offline=True,
            check_func=check_vosk_sounddevice,
            setup_func=setup_vosk_sounddevice
        )

        if vosk_backend.is_available():
            self.backends.append(vosk_backend)
            logger.info("✅ Backend Vosk + sounddevice disponible")
        else:
            logger.info(f"❌ Backend Vosk + sounddevice non disponible: {vosk_backend.error_message}")

        # 2. sounddevice + Google Speech (online)
        def check_sounddevice():
            try:
                import sounddevice
                return True, None
            except ImportError:
                return False, "Manquant: sounddevice"

        def setup_sounddevice_google():
            import sounddevice as sd
            import speech_recognition as sr

            class SoundDeviceGoogleSTT:
                """Wrapper pour sounddevice + Google Speech"""

                def __init__(self):
                    self.sample_rate = 16000
                    self.recognizer = sr.Recognizer()

                def listen_once(self, duration=5.0):
                    """Écoute une seule phrase avec Google Speech"""
                    import numpy as np

                    recording = sd.rec(
                        int(duration * self.sample_rate),
                        samplerate=self.sample_rate,
                        channels=1,
                        dtype='int16'
                    )
                    sd.wait()

                    # Convertir en format SpeechRecognition
                    audio_data = sr.AudioData(recording.tobytes(), self.sample_rate, 2)
                    try:
                        text = self.recognizer.recognize_google(audio_data, language="fr-FR")
                        return text
                    except sr.UnknownValueError:
                        return None
                    except sr.RequestError as e:
                        logger.error(f"Erreur Google Speech: {e}")
                        return None

            logger.info("✅ Backend sounddevice + Google Speech initialisé")
            return SoundDeviceGoogleSTT()

        sounddevice_backend = AudioBackend(
            name='sounddevice_google',
            priority=2,
            offline=False,
            check_func=check_sounddevice,
            setup_func=setup_sounddevice_google
        )

        if sounddevice_backend.is_available():
            self.backends.append(sounddevice_backend)
            logger.info("✅ Backend sounddevice + Google Speech disponible")
        else:
            logger.info(f"❌ Backend sounddevice + Google Speech non disponible: {sounddevice_backend.error_message}")

        # 3. PyAudio + Google Speech (optionnel)
        def check_pyaudio():
            try:
                import pyaudio
                return True, None
            except ImportError:
                return False, "Manquant: pyaudio"

        def setup_pyaudio_google():
            import speech_recognition as sr

            class PyAudioGoogleSTT:
                """Wrapper pour PyAudio + Google Speech"""

                def __init__(self):
                    self.recognizer = sr.Recognizer()
                    self.microphone = sr.Microphone()

                def listen_once(self, duration=5.0):
                    """Écoute une seule phrase avec Google Speech"""
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source)
                        try:
                            audio = self.recognizer.listen(source, timeout=duration)
                            text = self.recognizer.recognize_google(audio, language="fr-FR")
                            return text
                        except sr.WaitTimeoutError:
                            return None
                        except sr.UnknownValueError:
                            return None
                        except sr.RequestError as e:
                            logger.error(f"Erreur Google Speech: {e}")
                            return None

            logger.info("✅ Backend PyAudio + Google Speech initialisé")
            return PyAudioGoogleSTT()

        pyaudio_backend = AudioBackend(
            name='pyaudio_google',
            priority=3,
            offline=False,
            check_func=check_pyaudio,
            setup_func=setup_pyaudio_google
        )

        if pyaudio_backend.is_available():
            self.backends.append(pyaudio_backend)
            logger.info("✅ Backend PyAudio + Google Speech disponible")
        else:
            logger.info(f"❌ Backend PyAudio + Google Speech non disponible: {pyaudio_backend.error_message}")

        # 4. Web only (fallback ultime)
        def setup_web_only():
            logger.warning("⚠️ Mode web uniquement - Pas de reconnaissance vocale")
            return None

        web_backend = AudioBackend(
            name='web_only',
            priority=99,
            offline=False,
            setup_func=setup_web_only
        )
        self.backends.append(web_backend)

        # Trier par priorité
        self.backends.sort(key=lambda x: x.priority)

        logger.info(f"Backends détectés: {len(self.backends)}")
        for backend in self.backends:
            logger.info(f"  - {backend.name} (priorité: {backend.priority}, offline: {backend.offline})")

    def get_best_backend(self) -> Optional[AudioBackend]:
        """
        Retourne le meilleur backend disponible

        Returns:
            AudioBackend ou None
        """
        for backend in self.backends:
            if backend.is_available():
                try:
                    success, engine = backend.setup()
                    if success:
                        self.current_backend = backend
                        self.current_engine = engine
                        logger.info(f"✅ Backend sélectionné: {backend.name}")
                        return backend
                    else:
                        logger.warning(f"⚠️ Backend {backend.name} a échoué lors de l'initialisation")
                except Exception as e:
                    logger.warning(f"⚠️ Backend {backend.name} a échoué: {e}")
                    continue

        # Fallback ultime: web_only
        logger.warning("⚠️ Aucun backend fonctionnel - Mode web uniquement")
        web_backend = next((b for b in self.backends if b.name == 'web_only'), None)
        if web_backend:
            self.current_backend = web_backend
            return web_backend

        return None

    def get_backend_info(self) -> Dict[str, Any]:
        """Retourne des informations sur les backends"""
        return {
            'platform': self.platform,
            'python_version': f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            'current_backend': self.current_backend.name if self.current_backend else None,
            'available_backends': [
                {
                    'name': b.name,
                    'priority': b.priority,
                    'offline': b.offline,
                    'status': b.status.value,
                    'error': b.error_message
                }
                for b in self.backends
            ],
            'recommended_install': self._get_installation_recommendation()
        }

    def _get_installation_recommendation(self) -> Optional[Dict[str, str]]:
        """Retourne la recommandation d'installation"""
        # Vérifier si aucun backend n'est disponible
        has_working_backend = any(
            b.is_available() and b.name != 'web_only'
            for b in self.backends
        )

        if not has_working_backend:
            from platform_audio_config import PLATFORM_CONFIGS
            config = PLATFORM_CONFIGS.get(self.platform.lower(), {})
            return {
                'command': config.get('install_cmd', 'pip install sounddevice vosk'),
                'reason': config.get('notes', 'Pour activer la reconnaissance vocale'),
                'priority': 'high'
            }

        return None

    def create_unified_stt(self):
        """
        Crée un moteur STT unifié

        Returns:
            Moteur STT ou None (mode web only)
        """
        backend = self.get_best_backend()

        if backend and backend.name == 'web_only':
            return None

        return self.current_engine


# Instance globale
_universal_backend = None


def get_universal_backend() -> UniversalAudioBackend:
    """Retourne l'instance du backend universel"""
    global _universal_backend
    if _universal_backend is None:
        _universal_backend = UniversalAudioBackend()
    return _universal_backend


def create_unified_stt():
    """
    Fonction pratique pour créer un moteur STT unifié

    Returns:
        Moteur STT ou None
    """
    backend = get_universal_backend()
    return backend.create_unified_stt()


if __name__ == "__main__":
    # Test du backend universel
    print("=== Test du Backend Audio Universel ===\n")

    backend = get_universal_backend()
    info = backend.get_backend_info()

    print(f"Plateforme: {info['platform']}")
    print(f"Python: {info['python_version']}")
    print(f"\nBackends disponibles:")

    for b in info['available_backends']:
        status_icon = "✅" if b['status'] == 'available' else "❌"
        print(f"  {status_icon} {b['name']} (priorité: {b.get('priority', 'N/A')})")
        if b['error']:
            print(f"      Erreur: {b['error']}")

    best = backend.get_best_backend()
    if best:
        print(f"\n✅ Meilleur backend: {best.name}")
    else:
        print("\n❌ Aucun backend disponible")

    if info['recommended_install']:
        print(f"\n📦 Installation recommandée:")
        print(f"   Commande: {info['recommended_install']['command']}")
        print(f"   Raison: {info['recommended_install']['reason']}")
