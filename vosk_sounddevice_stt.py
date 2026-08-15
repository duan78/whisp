"""
Module de reconnaissance vocale Vosk avec sounddevice
Alternative complète à PyAudio pour Windows et Python 3.14+
"""

import os
import json
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable, Dict, Any

# Imports conditionnels
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


class VoskSTTEngine:
    """
    Moteur STT utilisant Vosk + sounddevice
    Ne nécessite PAS PyAudio
    """

    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 16000):
        """
        Initialise le moteur STT Vosk

        Args:
            model_path: Chemin vers le modèle Vosk (None = auto-détection)
            sample_rate: Taux d'échantillonnage (défaut: 16000 Hz)
        """
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                "sounddevice n'est pas disponible. "
                "Installez-le avec: pip install sounddevice"
            )

        if not VOSK_AVAILABLE:
            raise RuntimeError(
                "vosk n'est pas disponible. "
                "Installez-le avec: pip install vosk"
            )

        self.sample_rate = sample_rate
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.stream = None
        self.process_thread = None

        # Charger le modèle
        self._load_model()

    def _load_model(self):
        """Charge le modèle Vosk"""
        if self.model_path:
            # Chemin spécifié
            self.model = vosk.Model(self.model_path)
            print(f"Modèle Vosk chargé depuis: {self.model_path}")
        else:
            # Chercher dans les emplacements par défaut
            possible_paths = [
                "models/vosk-model-fr-0.22",  # Modèle français
                "models/vosk-model-small-fr-0.22",  # Modèle français léger
                os.path.expanduser("~/.vosk/vosk-model-fr-0.22"),
                "vosk-model-fr-0.22",
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    self.model = vosk.Model(path)
                    self.model_path = path
                    print(f"Modèle Vosk trouvé et chargé: {path}")
                    break

            if self.model is None:
                raise RuntimeError(
                    "Aucun modèle Vosk trouvé. "
                    "Téléchargez un modèle depuis: https://alphacephei.com/vosk/models "
                    "et extrayez-le dans le dossier 'models/'"
                )

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback appelé par sounddevice quand l'audio est disponible
        """
        if status:
            print(f"Status audio: {status}")

        # Convertir float32 en int16 pour Vosk
        audio_data = (indata * 32768).astype(np.int16)
        self.audio_queue.put(audio_data.tobytes())

    def _process_audio(self):
        """
        Thread qui traite l'audio et effectue la reconnaissance
        """
        while self.is_running:
            try:
                # Récupérer l'audio de la queue
                audio_data = self.audio_queue.get(timeout=0.5)

                # Reconnaissance avec Vosk
                if self.recognizer.AcceptWaveform(audio_data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()

                    if text:
                        self.result_queue.put({
                            'type': 'final',
                            'text': text
                        })
                else:
                    # Résultat partiel (optionnel)
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '').strip()

                    if partial_text:
                        self.result_queue.put({
                            'type': 'partial',
                            'text': partial_text
                        })

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erreur lors du traitement audio: {e}")
                continue

    def start_listening(self, callback: Optional[Callable[[str], None]] = None):
        """
        Démarre l'écoute en continu

        Args:
            callback: Fonction appelée avec le texte reconnu (optionnel)
        """
        if self.model is None:
            raise RuntimeError("Modèle Vosk non chargé")

        self.is_running = True

        # Créer le recognizer
        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        # Démarrer le stream audio
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,  # 0.5 seconde
                dtype=np.float32,
                channels=1,
                callback=self._audio_callback
            )
            self.stream.start()
        except Exception as e:
            raise RuntimeError(f"Erreur lors du démarrage du stream audio: {e}")

        # Démarrer le thread de traitement
        self.process_thread = threading.Thread(
            target=self._process_audio,
            daemon=True,
            name="vosk_audio_processor"
        )
        self.process_thread.start()

        print("Écoute Vosk démarrée")

        # Si un callback est fourni, démarrer un thread pour gérer les résultats
        if callback:
            self.callback_thread = threading.Thread(
                target=self._handle_results,
                args=(callback,),
                daemon=True,
                name="vosk_callback_handler"
            )
            self.callback_thread.start()

    def _handle_results(self, callback: Callable[[str], None]):
        """
        Gère les résultats de reconnaissance et appelle le callback
        """
        while self.is_running:
            try:
                result = self.result_queue.get(timeout=0.5)

                if result['type'] == 'final' and result['text']:
                    # Appeler le callback avec le texte final
                    callback(result['text'])

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erreur lors du traitement des résultats: {e}")
                continue

    def get_result(self, timeout: float = None) -> Optional[Dict[str, Any]]:
        """
        Récupère un résultat de reconnaissance (bloquant)

        Args:
            timeout: Timeout en secondes (None = bloquant indéfiniment)

        Returns:
            Dictionnaire avec 'type' ('final' ou 'partial') et 'text'
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def listen_once(self, duration: float = 5.0, phrase_timeout: float = 1.0) -> Optional[str]:
        """
        Écoute une seule phrase

        Args:
            duration: Durée maximale d'écoute en secondes
            phrase_timeout: Silence considéré comme fin de phrase

        Returns:
            Texte reconnu ou None
        """
        if self.model is None:
            raise RuntimeError("Modèle Vosk non chargé")

        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        # Enregistrer l'audio
        print(f"Écoute pendant {duration} secondes...")
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()

        # Convertir en int16
        audio_data = (recording * 32768).astype(np.int16)

        # Reconnaître
        if self.recognizer.AcceptWaveform(audio_data.tobytes()):
            result = json.loads(self.recognizer.Result())
            return result.get('text', '').strip()

        return None

    def stop_listening(self, wait_for_stop: bool = False):
        """Arrête l'écoute.

        ``wait_for_stop`` est accepté (et ignoré) pour être compatible avec
        l'API des autres fonctions stop, appelées avec ce paramètre par le
        gestionnaire d'arrêt de l'application.
        """
        self.is_running = False

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass  # le flux peut déjà être fermé
            self.stream = None

        print("Écoute Vosk arrêtée")

    def __del__(self):
        """Nettoyage à la destruction"""
        try:
            self.stop_listening()
        except Exception:
            pass


def create_vosk_engine(model_path: Optional[str] = None) -> VoskSTTEngine:
    """
    Crée et initialise un moteur Vosk

    Args:
        model_path: Chemin vers le modèle Vosk (optionnel)

    Returns:
        Instance de VoskSTTEngine
    """
    return VoskSTTEngine(model_path=model_path)


def test_vosk_stt():
    """Test du moteur Vosk + sounddevice"""
    print("=== Test Reconnaissance Vocale Vosk + sounddevice ===\n")

    if not SOUNDDEVICE_AVAILABLE:
        print("[X] sounddevice n'est pas installe")
        print("   Installez-le avec: pip install sounddevice")
        return

    if not VOSK_AVAILABLE:
        print("[X] vosk n'est pas installe")
        print("   Installez-le avec: pip install vosk")
        return

    # Lister les périphériques audio
    print("[OK] Peripheriques d'entree disponibles:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"   {i}: {dev['name']} (entrees: {dev['max_input_channels']})")

    print("\n" + "="*60)
    print("Pour utiliser la reconnaissance vocale:")
    print("="*60)
    print("\n1. Telechargez un modele Vosk francais:")
    print("   https://alphacephei.com/vosk/models")
    print("   Recommande: vosk-model-small-fr-0.22 (~50 Mo)")
    print("\n2. Extrayez le modele dans le dossier 'models/'")
    print("\n3. Utilisez le code:")
    print("""
    from vosk_sounddevice_stt import create_vosk_engine

    # Creer le moteur
    engine = create_vosk_engine("models/vosk-model-small-fr-0.22")

    # Definir le callback
    def on_text(text):
        print(f"Reconnu: {text}")

    # Demarrer l'ecoute
    engine.start_listening(on_text)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        engine.stop_listening()
    """)


if __name__ == "__main__":
    test_vosk_stt()
