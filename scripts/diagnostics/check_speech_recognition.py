"""
Script de test de la reconnaissance vocale avec Vosk + sounddevice
Alternative a PyAudio - Fonctionne avec Python 3.14+
"""

import sys
import os

# Ajouter le repertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_vosk_stt():
    """Test la reconnaissance vocale Vosk + sounddevice"""

    print("="*70)
    print("  Test de Reconnaissance Vocale avec Vosk + sounddevice")
    print("="*70)
    print()

    # Verifier les dependances
    try:
        import sounddevice as sd
        print("[OK] sounddevice est installe")
    except ImportError:
        print("[ERROR] sounddevice n'est pas installe")
        print("        Installez-le avec: pip install sounddevice")
        return False

    try:
        import vosk
        print("[OK] vosk est installe")
    except ImportError:
        print("[ERROR] vosk n'est pas installe")
        print("        Installez-le avec: pip install vosk")
        return False

    # Verifier le modele
    model_paths = [
        "models/vosk-model-small-fr-0.22",
        "models/vosk-model-fr-0.22",
        os.path.expanduser("~/.vosk/vosk-model-small-fr-0.22"),
    ]

    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            print(f"[OK] Modele Vosk trouve: {path}")
            break

    if not model_path:
        print()
        print("[ERROR] Aucun modele Vosk trouve !")
        print()
        print("Pour installer un modele:")
        print("  python install_vosk_model.py")
        print()
        print("Ou telechargez-le manuellement:")
        print("  https://alphacephei.com/vosk/models")
        print()
        return False

    print()
    print("-" * 70)
    print("Peripheriques audio disponibles:")
    print("-" * 70)
    devices = sd.query_devices()
    input_devices = [dev for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]

    if not input_devices:
        print("[ERROR] Aucun micro trouve !")
        return False

    for i, dev in enumerate(input_devices):
        print(f"  {i+1}. {dev['name']}")

    print()
    print("-" * 70)
    print("Test de reconnaissance vocale")
    print("-" * 70)
    print()
    print("Parlez maintenant (phrase en francais)...")
    print("Appuyez sur Ctrl+C pour arreter")
    print()

    try:
        from vosk_sounddevice_stt import create_vosk_engine

        # Creer le moteur
        engine = create_vosk_engine(model_path)

        # Compteur de phrases reconnues
        phrase_count = 0

        def on_text(text):
            nonlocal phrase_count
            phrase_count += 1
            print(f"\n[PHRASE {phrase_count}] {text}")
            print("-" * 70)
            print("Ecoute... (Parlez ou Ctrl+C pour arreter)")

        # Demarrer l'ecoute
        engine.start_listening(on_text)
        print("[OK] Ecoute demarree")

        # Boucle principale
        import time
        start_time = time.time()

        while True:
            time.sleep(0.1)

            # Afficher un point toutes les 5 secondes pour montrer que c'est vivant
            if int(time.time() - start_time) % 5 == 0 and time.time() - start_time > 0:
                print(".", end='', flush=True)

    except KeyboardInterrupt:
        print()
        print()
        print("-" * 70)
        print(f"[FIN] Test termine - {phrase_count} phrase(s) reconnue(s)")
        print("-" * 70)
        engine.stop_listening()
        return True

    except Exception as e:
        print()
        print(f"[ERROR] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale"""
    try:
        success = test_vosk_stt()
        if success:
            print()
            print("[SUCCESS] Test de reconnaissance vocale reussi !")
            print()
            print("La reconnaissance vocale fonctionne avec Vosk + sounddevice")
            print("sans PyAudio sur Python 3.14")
            print()
            return 0
        else:
            print()
            print("[FAILED] Test de reconnaissance vocale echoue")
            print()
            return 1
    except Exception as e:
        print(f"[ERROR] Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
