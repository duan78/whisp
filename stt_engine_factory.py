"""
Factory pour créer des moteurs STT (Speech-to-Text)
Gère les instances et fournit une interface unifiée
"""

import logging
import threading
from typing import Optional, Dict, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class STTEngineType(Enum):
    """Types de moteurs STT disponibles"""
    VOSK_SOUNDDEVICE = "vosk_sounddevice"
    SOUNDDEVICE_GOOGLE = "sounddevice_google"
    PYAUDIO_GOOGLE = "pyaudio_google"
    WEB_ONLY = "web_only"


class STTEngine:
    """Interface de base pour tous les moteurs STT"""

    def __init__(self, engine_type: STTEngineType):
        self.engine_type = engine_type
        self.is_listening = False

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Démarre l'écoute en continu"""
        raise NotImplementedError("Subclasses must implement start_listening")

    def stop_listening(self):
        """Arrête l'écoute"""
        raise NotImplementedError("Subclasses must implement stop_listening")

    def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """Écoute une seule phrase"""
        raise NotImplementedError("Subclasses must implement listen_once")

    def is_offline(self) -> bool:
        """Retourne True si le moteur fonctionne offline"""
        raise NotImplementedError("Subclasses must implement is_offline")


class VoskSTTEngine(STTEngine):
    """Moteur STT Vosk avec sounddevice"""

    def __init__(self, vosk_engine):
        super().__init__(STTEngineType.VOSK_SOUNDDEVICE)
        self.vosk_engine = vosk_engine
        self.callback_thread = None
        self.callback = None

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Démarre l'écoute en continu avec Vosk"""
        if self.is_listening:
            logger.warning("VoskSTT est déjà en écoute")
            return

        self.callback = callback
        self.vosk_engine.start_listening(callback)
        self.is_listening = True
        logger.info("Écoute Vosk démarrée")

    def stop_listening(self):
        """Arrête l'écoute Vosk"""
        if not self.is_listening:
            return

        self.vosk_engine.stop_listening()
        self.is_listening = False
        logger.info("Écoute Vosk arrêtée")

    def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """Écoute une seule phrase avec Vosk"""
        return self.vosk_engine.listen_once(duration=duration)

    def is_offline(self) -> bool:
        """Vosk fonctionne offline"""
        return True


class SoundDeviceGoogleSTT(STTEngine):
    """Moteur STT sounddevice + Google Speech"""

    def __init__(self, google_engine):
        super().__init__(STTEngineType.SOUNDDEVICE_GOOGLE)
        self.google_engine = google_engine

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Démarre l'écotte en continu avec Google Speech"""
        logger.warning("⚠️ L'écoute en continu n'est pas supportée avec Google Speech API")
        logger.info("Utilisez listen_once() pour des écoutes individuelles")
        self.callback = callback

    def stop_listening(self):
        """Arrête l'écoute (no-op pour Google Speech)"""
        pass

    def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """Écoute une seule phrase avec Google Speech"""
        return self.google_engine.listen_once(duration=duration)

    def is_offline(self) -> bool:
        """Google Speech nécessite une connexion internet"""
        return False


class PyAudioGoogleSTT(STTEngine):
    """Moteur STT PyAudio + Google Speech"""

    def __init__(self, google_engine):
        super().__init__(STTEngineType.PYAUDIO_GOOGLE)
        self.google_engine = google_engine

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Démarre l'écoute en continu avec Google Speech"""
        logger.warning("⚠️ L'écoute en continu n'est pas supportée avec Google Speech API")
        logger.info("Utilisez listen_once() pour des écoutes individuelles")
        self.callback = callback

    def stop_listening(self):
        """Arrête l'écoute (no-op pour Google Speech)"""
        pass

    def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """Écoute une seule phrase avec Google Speech"""
        return self.google_engine.listen_once(duration=duration)

    def is_offline(self) -> bool:
        """Google Speech nécessite une connexion internet"""
        return False


class WebOnlySTT(STTEngine):
    """Moteur STT factice pour mode web only"""

    def __init__(self):
        super().__init__(STTEngineType.WEB_ONLY)

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """Mode web only - pas de reconnaissance vocale"""
        logger.info("Mode web only - Utilisez l'interface web pour la reconnaissance")

    def stop_listening(self):
        """No-op"""
        pass

    def listen_once(self, duration: float = 5.0) -> Optional[str]:
        """Retourne toujours None (pas de reconnaissance)"""
        logger.info("Mode web only - Reconnaissance vocale non disponible")
        return None

    def is_offline(self) -> bool:
        """N/A pour web only"""
        return False


class STTEngineFactory:
    """
    Factory pour créer des moteurs STT avec caching
    """

    def __init__(self):
        self._engine_cache: Dict[STTEngineType, STTEngine] = {}
        self._current_engine: Optional[STTEngine] = None
        self._lock = threading.Lock()

    def create_engine(self, engine_type: STTEngineType, raw_engine=None) -> STTEngine:
        """
        Crée ou récupère un moteur STT depuis le cache

        Args:
            engine_type: Type de moteur à créer
            raw_engine: Moteur brut (venant de universal_audio_backend)

        Returns:
            Instance de STTEngine
        """
        with self._lock:
            # Vérifier le cache
            if engine_type in self._engine_cache:
                logger.info(f"Utilisation du moteur STT en cache: {engine_type.value}")
                return self._engine_cache[engine_type]

            # Créer le moteur
            if engine_type == STTEngineType.VOSK_SOUNDDEVICE:
                if raw_engine is None:
                    raise ValueError("raw_engine est requis pour VOSK_SOUNDDEVICE")
                engine = VoskSTTEngine(raw_engine)

            elif engine_type == STTEngineType.SOUNDDEVICE_GOOGLE:
                if raw_engine is None:
                    raise ValueError("raw_engine est requis pour SOUNDDEVICE_GOOGLE")
                engine = SoundDeviceGoogleSTT(raw_engine)

            elif engine_type == STTEngineType.PYAUDIO_GOOGLE:
                if raw_engine is None:
                    raise ValueError("raw_engine est requis pour PYAUDIO_GOOGLE")
                engine = PyAudioGoogleSTT(raw_engine)

            elif engine_type == STTEngineType.WEB_ONLY:
                engine = WebOnlySTT()

            else:
                raise ValueError(f"Type de moteur inconnu: {engine_type}")

            # Mettre en cache
            self._engine_cache[engine_type] = engine
            logger.info(f"Moteur STT créé: {engine_type.value}")

            return engine

    def get_current_engine(self) -> Optional[STTEngine]:
        """Retourne le moteur STT actuel"""
        return self._current_engine

    def set_current_engine(self, engine: STTEngine):
        """Définit le moteur STT actuel"""
        self._current_engine = engine
        logger.info(f"Moteur STT actuel changé pour: {engine.engine_type.value}")

    def create_best_engine(self, backend_manager=None) -> Optional[STTEngine]:
        """
        Crée le meilleur moteur STT disponible

        Args:
            backend_manager: Instance de UniversalAudioBackend (optionnel)

        Returns:
            STTEngine ou None
        """
        if backend_manager is None:
            from universal_audio_backend import get_universal_backend
            backend_manager = get_universal_backend()

        # Obtenir le meilleur backend
        best_backend = backend_manager.get_best_backend()

        if best_backend is None or best_backend.name == 'web_only':
            engine = self.create_engine(STTEngineType.WEB_ONLY)
        else:
            # Mapper le nom du backend vers le type de moteur
            engine_type_map = {
                'vosk_sounddevice': STTEngineType.VOSK_SOUNDDEVICE,
                'sounddevice_google': STTEngineType.SOUNDDEVICE_GOOGLE,
                'pyaudio_google': STTEngineType.PYAUDIO_GOOGLE,
            }

            engine_type = engine_type_map.get(best_backend.name, STTEngineType.WEB_ONLY)
            engine = self.create_engine(engine_type, backend_manager.current_engine)

        self._current_engine = engine
        return engine

    def clear_cache(self):
        """Vide le cache des moteurs"""
        with self._lock:
            # Arrêter tous les moteurs en cours d'écoute
            for engine in self._engine_cache.values():
                if engine.is_listening:
                    engine.stop_listening()

            self._engine_cache.clear()
            logger.info("Cache des moteurs STT vidé")


# Instance globale de la factory
_stt_factory = None
_factory_lock = threading.Lock()


def get_stt_factory() -> STTEngineFactory:
    """Retourne l'instance de la factory STT"""
    global _stt_factory
    with _factory_lock:
        if _stt_factory is None:
            _stt_factory = STTEngineFactory()
        return _stt_factory


def create_unified_stt_engine() -> Optional[STTEngine]:
    """
    Fonction pratique pour créer le meilleur moteur STT disponible

    Returns:
        STTEngine ou None
    """
    factory = get_stt_factory()
    return factory.create_best_engine()


if __name__ == "__main__":
    # Test de la factory
    print("=== Test STT Engine Factory ===\n")

    factory = get_stt_factory()

    # Créer le meilleur moteur
    engine = create_unified_stt_engine()

    if engine:
        print(f"✅ Moteur STT créé: {engine.engine_type.value}")
        print(f"   Offline: {engine.is_offline()}")
        print(f"   En écoute: {engine.is_listening}")

        # Tester listen_once si pas web_only
        if engine.engine_type != STTEngineType.WEB_ONLY:
            print("\nTest de listen_once (5 secondes)...")
            text = engine.listen_once(duration=5.0)
            if text:
                print(f"✅ Texte reconnu: {text}")
            else:
                print("⚠️ Aucun texte reconnu")
    else:
        print("❌ Aucun moteur STT disponible")
