#!/usr/bin/env python3
"""
Script de test simple pour verifier les backends audio disponibles
Compatible Windows ARM64 et autres plateformes
"""

import sys
import platform

def test_pyaudio():
    """Test PyAudio availability"""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        device_count = pa.get_device_count()
        pa.terminate()
        print(f"[OK] PyAudio disponible - {device_count} appareils audio detectes")
        return True
    except Exception as e:
        print(f"[ERREUR] PyAudio non disponible: {e}")
        return False

def test_sounddevice():
    """Test sounddevice availability"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        print(f"[OK] sounddevice disponible - {len(input_devices)} appareils d'entree detectes")
        return True
    except Exception as e:
        print(f"[ERREUR] sounddevice non disponible: {e}")
        return False

def test_speechrecognition():
    """Test SpeechRecognition availability"""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        try:
            microphone = sr.Microphone()
            print("[OK] SpeechRecognition disponible - Microphone detecte")
            return True
        except Exception as e:
            print(f"[AVERTISSEMENT] SpeechRecognition disponible mais microphone inaccessible: {e}")
            return False
    except Exception as e:
        print(f"[ERREUR] SpeechRecognition non disponible: {e}")
        return False

def get_platform_info():
    """Get platform information"""
    print(f"Systeme: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {platform.python_version()}")

    if platform.system() == "Windows" and platform.machine() == "ARM64":
        print("Plateforme Windows ARM64 detectee")
        print("Recommandation: pip install sounddevice")

def main():
    """Main test function"""
    print("Test de Compatibilite Audio - Whisp Assistant")
    print("=" * 50)

    # Platform info
    get_platform_info()
    print()

    # Test backends
    print("Test des backends audio...")

    pyaudio_available = test_pyaudio()
    sounddevice_available = test_sounddevice()
    speechrecognition_available = test_speechrecognition()

    print("\nRecommandations:")

    if not pyaudio_available and not sounddevice_available:
        print("Installation recommandee (priorite haute):")
        print("  pip install sounddevice numpy")
        print()
        print("Alternative PyAudio (si sounddevice ne fonctionne pas):")
        print("  pip install pip-wheel")
        print("  pip install --only-binary :all: pyaudio")

    elif not pyaudio_available and sounddevice_available:
        print("sounddevice est disponible - Pas besoin de PyAudio!")
        print("sounddevice est recommande pour votre architecture.")

    elif pyaudio_available and not sounddevice_available:
        print("PyAudio fonctionne mais sounddevice est recommande:")
        print("Pour de meilleures performances: pip install sounddevice")

    else:
        print("Plusieurs backends sont disponibles!")
        print("Utilisation recommandee: sounddevice (plus stable)")

    # Summary
    available_count = sum([pyaudio_available, sounddevice_available, speechrecognition_available])
    total_count = 3

    print(f"\nResultat: {available_count}/{total_count} backends disponibles")

    if available_count == 0:
        print("AVERTISSEMENT: Aucun backend audio n'est disponible!")
        return False
    else:
        print("Au moins un backend est disponible - L'application fonctionnera.")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)