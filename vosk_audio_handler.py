"""
Module de capture audio avec sounddevice pour Vosk
Solution alternative à PyAudio pour la reconnaissance vocale
"""

import threading
import queue
import numpy as np
import time
from typing import Optional, Callable

# Importer sounddevice
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("AVERTISSEMENT: sounddevice n'est pas disponible")

# Importer Vosk
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("AVERTISSEMENT: vosk n'est pas disponible")


class VoskAudioHandler:
    """Gestionnaire de capture audio et reconnaissance Vosk avec sounddevice"""

    def __init__(self, model_path: Optional[str] = None, sample_rate: int = 16000):
        """
        Initialise le gestionnaire audio Vosk

        Args:
            model_path: Chemin vers le modèle Vosk (None = modèle par défaut)
            sample_rate: Taux d'échantillonnage audio (défaut: 16000 Hz)
        """
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice n'est pas disponible. Installez-le avec: pip install sounddevice")

        if not VOSK_AVAILABLE:
            raise RuntimeError("vosk n'est pas disponible. Installez-le avec: pip install vosk")

        self.sample_rate = sample_rate
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.callback = None
        self.recognizer = None
        self.stream = None

        # Charger le modèle Vosk
        if model_path:
            self.model = vosk.Model(model_path)
        else:
            # Utiliser le modèle par défaut (doit être téléchargé)
            self.model = None
            print("Modèle Vosk non spécifié. Utilisez set_model() pour définir un modèle.")

    def set_model(self, model_path: str):
        """Définit le modèle Vosk à utiliser"""
        self.model = vosk.Model(model_path)
        print(f"Modèle Vosk chargé depuis: {model_path}")

    def audio_callback(self, indata, frames, time_info, status):
        """Callback appelé quand l'audio est disponible"""
        if status:
            print(f"Status audio: {status}")

        # Convertir en int16 pour Vosk
        audio_data = (indata * 32768).astype(np.int16)
        self.audio_queue.put(audio_data.tobytes())

    def start_listening(self, callback: Callable[[str], None]):
        """
        Démarre l'écoute en continu

        Args:
            callback: Fonction appelée avec le texte reconnu
        """
        if self.model is None:
            raise RuntimeError("Aucun modèle Vosk défini. Utilisez set_model() d'abord.")

        self.callback = callback
        self.is_running = True

        # Créer le recognizer Vosk
        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        # Démarrer le stream audio avec sounddevice
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,  # 0.5 seconde à 16000 Hz
            dtype=np.float32,
            channels=1,
            callback=self.audio_callback
        )

        self.stream.start()
        print("Écoute Vosk démarrée avec sounddevice")

        # Démarrer le thread de traitement
        self.process_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.process_thread.start()

    def _process_audio(self):
        """Traite l'audio et reconnaît le texte"""
        while self.is_running:
            try:
                # Récupérer l'audio de la queue avec timeout
                audio_data = self.audio_queue.get(timeout=0.5)

                # Reconnaissance avec Vosk
                if self.recognizer.AcceptWaveform(audio_data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()

                    if text and self.callback:
                        # Appeler le callback avec le texte reconnu
                        self.callback(text)
                else:
                    # Résultat partiel (pour dictée en continu)
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '').strip()

                    # Optionnel : utiliser le texte partiel pour la dictée
                    # if partial_text and self.callback:
                    #     self.callback(f"[PARTIAL] {partial_text}")

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erreur lors du traitement audio: {e}")
                continue

    def stop_listening(self):
        """Arrête l'écoute"""
        self.is_running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("Écoute Vosk arrêtée")

    def recognize_once(self, duration: float = 5.0) -> Optional[str]:
        """
        Reconnaît une seule phrase

        Args:
            duration: Durée d'écoute en secondes

        Returns:
            Texte reconnu ou None
        """
        if self.model is None:
            raise RuntimeError("Aucun modèle Vosk défini. Utilisez set_model() d'abord.")

        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        # Enregistrer l'audio
        recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()  # Attendre que l'enregistrement soit terminé

        # Convertir en int16 pour Vosk
        audio_data = (recording * 32768).astype(np.int16)

        # Reconnaître
        if self.recognizer.AcceptWaveform(audio_data.tobytes()):
            result = json.loads(self.recognizer.Result())
            return result.get('text', '').strip()

        return None


def test_vosk_audio():
    """Test la capture audio avec Vosk"""
    import json

    if not SOUNDDEVICE_AVAILABLE or not VOSK_AVAILABLE:
        print("sounddevice ou vosk non disponible")
        return

    print("=== Test Vosk + sounddevice ===\n")

    # Lister les périphériques audio
    print("Périphériques d'entrée disponibles:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"  {i}: {dev['name']}")

    print("\nPour tester la reconnaissance vocale:")
    print("1. Téléchargez un modèle Vosk:")
    print("   https://alphacephei.com/vosk/models")
    print("2. Extrayez le modèle dans un dossier")
    print("3. Utilisez le code suivant:")
    print("""
    handler = VoskAudioHandler()
    handler.set_model("chemin/vers/modele")

    def on_text(text):
        print(f"Reconnu: {text}")

    handler.start_listening(on_text)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        handler.stop_listening()
    """)


if __name__ == "__main__":
    test_vosk_audio()
