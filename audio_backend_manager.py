"""
Gestionnaire des backends audio pour la reconnaissance vocale
Permet de basculer entre différentes bibliothèques audio selon la disponibilité
"""

import sys
import logging
from typing import Tuple, Optional, Any

logger = logging.getLogger(__name__)

class AudioBackendManager:
    """
    Gère les différents backends audio disponibles pour la reconnaissance vocale.
    Essaie plusieurs options dans l'ordre de préférence.
    """

    def __init__(self):
        self.available_backends = []
        self.current_backend = None
        self._detect_available_backends()

    def _detect_available_backends(self):
        """Détecte les backends audio disponibles sur le système"""

        # Option 1: sounddevice (recommandé pour Windows ARM64)
        try:
            import sounddevice
            self.available_backends.append({
                'name': 'sounddevice',
                'library': sounddevice,
                'priority': 1,
                'description': 'sounddevice - Recommended for ARM64'
            })
            logger.info("✅ sounddevice backend disponible")
        except ImportError:
            logger.info("❌ sounddevice non disponible")

        # Option 2: PyAudio (option traditionnelle)
        try:
            import pyaudio
            self.available_backends.append({
                'name': 'pyaudio',
                'library': pyaudio,
                'priority': 2,
                'description': 'PyAudio - Backend traditionnel'
            })
            logger.info("✅ PyAudio backend disponible")
        except ImportError:
            logger.info("❌ PyAudio non disponible")

        # Option 3: python-soundfile (fallback basique)
        try:
            import soundfile as sf
            import numpy as np
            self.available_backends.append({
                'name': 'soundfile',
                'library': {'soundfile': sf, 'numpy': np},
                'priority': 3,
                'description': 'SoundFile - Fallback basique'
            })
            logger.info("✅ SoundFile backend disponible")
        except ImportError:
            logger.info("❌ SoundFile non disponible")

        # Option 4: Mode simulation (pour tests/développement)
        self.available_backends.append({
            'name': 'simulation',
            'library': None,
            'priority': 99,
            'description': 'Simulation mode - Tests uniquement'
        })
        logger.info("ℹ️ Mode simulation toujours disponible")

        # Trier par priorité
        self.available_backends.sort(key=lambda x: x['priority'])

        logger.info(f"Backends audio détectés: {[b['name'] for b in self.available_backends]}")

    def create_microphone(self, backend_name: Optional[str] = None):
        """
        Crée une instance de microphone en utilisant le backend spécifié ou le meilleur disponible.

        Args:
            backend_name: Nom du backend à utiliser (None = auto-sélection)

        Returns:
            Tuple: (recognizer, microphone, backend_info) ou (None, None, None) si échec
        """
        import speech_recognition as sr

        # Sélection du backend
        if backend_name:
            backend = next((b for b in self.available_backends if b['name'] == backend_name), None)
            if not backend:
                logger.error(f"Backend '{backend_name}' non disponible")
                backend = self.available_backends[0] if self.available_backends else None
        else:
            backend = self.available_backends[0] if self.available_backends else None

        if not backend:
            logger.error("Aucun backend audio disponible")
            return None, None, None

        self.current_backend = backend['name']
        logger.info(f"Tentative d'utilisation du backend: {backend['description']}")

        try:
            if backend['name'] == 'sounddevice':
                return self._create_sounddevice_microphone(sr)
            elif backend['name'] == 'pyaudio':
                return self._create_pyaudio_microphone(sr)
            elif backend['name'] == 'soundfile':
                return self._create_soundfile_microphone(sr)
            elif backend['name'] == 'simulation':
                return self._create_simulation_microphone(sr)
            else:
                logger.error(f"Backend non implémenté: {backend['name']}")
                return None, None, None

        except Exception as e:
            logger.error(f"Erreur avec backend {backend['name']}: {e}")
            # Essayer le backend suivant
            if len(self.available_backends) > 1:
                next_backend_index = next(
                    i for i, b in enumerate(self.available_backends)
                    if b['name'] == backend['name']
                ) + 1
                if next_backend_index < len(self.available_backends):
                    logger.info("Tentative avec le backend suivant...")
                    return self.create_microphone(self.available_backends[next_backend_index]['name'])

            return None, None, None

    def _create_sounddevice_microphone(self, sr):
        """Crée un microphone en utilisant sounddevice"""
        import sounddevice as sd
        import numpy as np

        class SoundDeviceMicrophone:
            def __init__(self):
                self.sample_rate = 16000
                self.channels = 1
                self.dtype = np.int16
                self.recording = False
                self.audio_queue = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def start_recording(self):
                self.recording = True
                self.audio_queue = []

                def audio_callback(indata, frames, time, status):
                    if self.recording:
                        self.audio_queue.append(indata.copy())

                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype=self.dtype,
                    callback=audio_callback
                )
                self.stream.start()

            def stop_recording(self):
                if hasattr(self, 'stream'):
                    self.stream.stop()
                    self.stream.close()
                self.recording = False

            def read_audio(self):
                if self.audio_queue:
                    audio_data = np.concatenate(self.audio_queue)
                    self.audio_queue = []
                    return audio_data.tobytes()
                return b''

        recognizer = sr.Recognizer()
        microphone = SoundDeviceMicrophone()

        # Configuration du recognizer
        recognizer.pause_threshold = 1.5
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True

        return recognizer, microphone, {'backend': 'sounddevice', 'info': 'Backend sounddevice utilisé avec succès'}

    def _create_pyaudio_microphone(self, sr):
        """Crée un microphone en utilisant PyAudio (méthode traditionnelle)"""
        microphone = sr.Microphone()
        recognizer = sr.Recognizer()

        # Configuration du recognizer
        recognizer.pause_threshold = 1.5
        recognizer.energy_threshold = 200
        recognizer.dynamic_energy_threshold = True

        return recognizer, microphone, {'backend': 'pyaudio', 'info': 'Backend PyAudio utilisé avec succès'}

    def _create_soundfile_microphone(self, sr):
        """Crée un microphone basique en utilisant soundfile (fallback)"""
        import soundfile as sf
        import numpy as np
        import tempfile
        import os

        class SoundFileMicrophone:
            def __init__(self):
                self.sample_rate = 16000
                self.temp_file = None

            def __enter__(self):
                self.temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.temp_file and os.path.exists(self.temp_file.name):
                    try:
                        self.temp_file.close()
                        os.unlink(self.temp_file.name)
                    except:
                        pass

            def record_audio(self, duration=5):
                """Enregistre une portion audio de durée fixe"""
                try:
                    # Simulation d'enregistrement (implémentation basique)
                    silence = np.zeros(int(self.sample_rate * duration), dtype=np.int16)
                    sf.write(self.temp_file.name, silence, self.sample_rate)
                    return self.temp_file.name
                except Exception as e:
                    logger.error(f"Erreur enregistrement SoundFile: {e}")
                    return None

        # Avertissement pour l'utilisateur
        logger.warning("⚠️  Utilisation du backend SoundFile limité")
        logger.warning("⚠️  Pour une reconnaissance vocale complète, installez sounddevice: pip install sounddevice")

        recognizer = sr.Recognizer()
        microphone = SoundFileMicrophone()

        return recognizer, microphone, {'backend': 'soundfile', 'info': 'Backend SoundFile limité utilisé'}

    def _create_simulation_microphone(self, sr):
        """Crée un microphone de simulation pour les tests"""
        logger.warning("🔧 Mode simulation activé - Reconnaissance vocale simulée")
        logger.warning("🔧 Pour une vraie reconnaissance vocale, installez: pip install sounddevice")

        class SimulationMicrophone:
            def __init__(self):
                self.sample_rate = 16000

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        recognizer = sr.Recognizer()
        microphone = SimulationMicrophone()

        return recognizer, microphone, {'backend': 'simulation', 'info': 'Mode simulation - Tests uniquement'}

    def get_backend_info(self):
        """Retourne des informations sur les backends disponibles"""
        return {
            'current_backend': self.current_backend,
            'available_backends': self.available_backends,
            'recommended_install': self._get_installation_recommendation()
        }

    def _get_installation_recommendation(self):
        """Retourne la commande d'installation recommandée"""
        if not any(b['name'] in ['sounddevice', 'pyaudio'] for b in self.available_backends):
            return {
                'command': 'pip install sounddevice',
                'reason': 'sounddevice est recommandé pour Windows ARM64 et fonctionne partout',
                'priority': 'high'
            }
        return None

# Instance globale du gestionnaire de backends
audio_backend_manager = AudioBackendManager()

def create_microphone_with_fallback():
    """
    Fonction pratique pour créer un microphone avec fallback automatique.

    Returns:
        Tuple: (recognizer, microphone, backend_info)
    """
    return audio_backend_manager.create_microphone()

def get_audio_backend_status():
    """Retourne le statut des backends audio"""
    return audio_backend_manager.get_backend_info()