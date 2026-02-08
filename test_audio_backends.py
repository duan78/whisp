#!/usr/bin/env python3
"""
Script de test pour vérifier les backends audio disponibles
Teste la compatibilité avec Windows ARM64 et autres plateformes
"""

import sys
import traceback
from typing import Dict, List

def test_audio_backends() -> Dict[str, bool]:
    """
    Teste la disponibilité des différents backends audio.

    Returns:
        Dict mapping backend names to availability status
    """
    results = {}

    print("Microphone: Test des backends audio disponibles...\n")

    # Test 1: PyAudio (traditionnel)
    print("1. Test de PyAudio...")
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        device_count = pa.get_device_count()
        pa.terminate()
        results['pyaudio'] = True
        print(f"   [OK] PyAudio disponible - {device_count} appareils audio détectés")
    except Exception as e:
        results['pyaudio'] = False
        print(f"   [ERREUR] PyAudio non disponible: {e}")

    # Test 2: sounddevice (recommandé pour ARM64)
    print("\n2. Test de sounddevice...")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        results['sounddevice'] = True
        print(f"   ✅ sounddevice disponible - {len(devices)} appareils audio détectés")

        # Afficher quelques appareils
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if input_devices:
            print(f"      Appareils d'entrée: {len(input_devices)}")
            for i, device in enumerate(input_devices[:3]):  # Limiter à 3 pour la lisibilité
                print(f"         - {device['name']}")
    except Exception as e:
        results['sounddevice'] = False
        print(f"   ❌ sounddevice non disponible: {e}")

    # Test 3: soundfile (fallback basique)
    print("\n3. Test de soundfile...")
    try:
        import soundfile as sf
        import numpy as np
        # Test basique d'écriture/lecture
        test_data = np.random.randint(-32768, 32767, 1000, dtype=np.int16)
        with sf.SoundFile('test_audio.wav', 'w', 16000, 1, 'PCM_16') as f:
            f.write(test_data)
        results['soundfile'] = True
        print("   ✅ soundfile disponible - Test d'écriture réussi")
        import os
        os.remove('test_audio.wav')  # Nettoyer
    except Exception as e:
        results['soundfile'] = False
        print(f"   ❌ soundfile non disponible: {e}")

    # Test 4: SpeechRecognition (le wrapper principal)
    print("\n4. Test de SpeechRecognition...")
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()

        # Test de création de microphone (sans l'utiliser réellement)
        try:
            microphone = sr.Microphone()
            results['speechrecognition'] = True
            print("   ✅ SpeechRecognition disponible - Microphone détecté")
        except Exception as e:
            print(f"   ⚠️  SpeechRecognition disponible mais microphone inaccessible: {e}")
            results['speechrecognition'] = False
    except Exception as e:
        results['speechrecognition'] = False
        print(f"   ❌ SpeechRecognition non disponible: {e}")

    return results

def test_platform_info():
    """Affiche les informations sur la plateforme actuelle"""
    import platform
    import os

    print("🖥️  Informations sur la plateforme:")
    print(f"   Système: {platform.system()}")
    print(f"   Version: {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {platform.python_version()}")

    if platform.system() == "Windows":
        try:
            import ctypes
            is_arm64 = platform.machine() == "ARM64"
            if is_arm64:
                print(f"   ✅ Plateforme Windows ARM64 détectée")
            else:
                print(f"   ℹ️  Plateforme Windows {platform.machine()}")
        except (OSError, RuntimeError, AttributeError) as e:
            error_handler.log_error(ErrorCategory.AUDIO, f"Audio error: {e}", ErrorSeverity.MEDIUM)
            pass

def test_installation_recommendations(results: Dict[str, bool]):
    """Donne des recommandations d'installation basées sur les résultats"""
    print(f"\n💡 Recommandations d'installation:")

    if not results['pyaudio'] and not results['sounddevice']:
        print("   📦 Installation recommandée (priorité haute):")
        print("      pip install sounddevice numpy")
        print("   ")
        print("   📦 Alternative PyAudio (si sounddevice ne fonctionne pas):")
        print("      pip install pip-wheel")
        print("      pip install --only-binary :all: pyaudio")

    elif not results['pyaudio'] and results['sounddevice']:
        print("   ✅ sounddevice est disponible - Pas besoin de PyAudio!")
        print("   📦 sounddevice est recommandé pour votre architecture.")

    elif results['pyaudio'] and not results['sounddevice']:
        print("   ✅ PyAudio fonctionne mais sounddevice est recommandé:")
        print("   📦 Pour de meilleures performances:")
        print("      pip install sounddevice")

    else:
        print("   ✅ Plusieurs backends sont disponibles!")
        print("   🎯 Utilisation recommandée: sounddevice (plus stable)")

def main():
    """Fonction principale du test"""
    print("Test de Compatibilité Audio - Whisp Assistant")
    print("=" * 50)

    # Informations sur la plateforme
    test_platform_info()
    print()

    # Test des backends
    results = test_audio_backends()

    # Recommandations
    test_installation_recommendations(results)

    # Résumé
    print(f"\n📊 Résumé des backends audio:")
    available_count = sum(results.values())
    total_count = len(results)

    for backend, available in results.items():
        status = "✅ Disponible" if available else "❌ Non disponible"
        print(f"   {backend}: {status}")

    print(f"\n🎯 Résultat: {available_count}/{total_count} backends disponibles")

    if available_count == 0:
        print("\n⚠️  Aucun backend audio n'est disponible!")
        print("   Veuillez installer l'un des backends recommandés ci-dessus.")
        return False
    elif available_count < total_count:
        print("\n⚡ Au moins un backend est disponible - L'application fonctionnera.")
        print("   Pour de meilleures performances, installez les backends manquants.")
        return True
    else:
        print("\n🎉 Tous les backends sont disponibles - Performance optimale garantie!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)