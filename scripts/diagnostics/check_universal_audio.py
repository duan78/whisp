"""
Test complet du systeme audio universel pour Whisp Assistant

Ce script teste:
1. La detection des backends audio
2. La selection automatique du meilleur backend
3. Le fonctionnement de chaque backend
4. Les messages d'erreur coherents
5. La compatibilite multi-plateforme
"""

import sys
import time
import platform
from typing import Optional

# Afficher les informations systeme
print("\n" + "="*70)
print("TEST DU SYSTEME AUDIO UNIVERSEL - WHISP ASSISTANT")
print("="*70)

print(f"\nSysteme d'exploitation: {platform.system()}")
print(f"Version Python: {sys.version}")
print(f"Architecture: {platform.machine()}")

# Test 1: Import des modules
print("\n" + "-"*70)
print("TEST 1: Import des modules universels")
print("-"*70)

try:
    from universal_audio_backend import get_universal_backend
    print("[OK] universal_audio_backend importe")
except ImportError as e:
    print(f"[ERREUR] Erreur import universal_audio_backend: {e}")
    sys.exit(1)

try:
    from platform_audio_config import (
        get_platform_config,
        get_vosk_model_path,
        check_microphone_available,
        get_installation_instructions,
        check_audio_dependencies
    )
    print("[OK] platform_audio_config importe")
except ImportError as e:
    print(f"[ERREUR] Erreur import platform_audio_config: {e}")
    sys.exit(1)

try:
    from stt_engine_factory import (
        get_stt_factory,
        create_unified_stt_engine,
        STTEngineType
    )
    print("[OK] stt_engine_factory importe")
except ImportError as e:
    print(f"[ERREUR] Erreur import stt_engine_factory: {e}")
    sys.exit(1)

# Test 2: Detection des dependances audio
print("\n" + "-"*70)
print("TEST 2: Detection des dependances audio")
print("-"*70)

deps = check_audio_dependencies()

for dep, available in deps.items():
    icon = "[OK]" if available else "[X]"
    status = "disponible" if available else "non disponible"
    print(f"  {icon} {dep}: {status}")

# Test 3: Detection du microphone
print("\n" + "-"*70)
print("TEST 3: Detection du microphone")
print("-"*70)

mic_available = check_microphone_available()
if mic_available:
    print("[OK] Microphone detecte")
else:
    print("[X] Aucun microphone detecte")
    print("\nMode degrade: L'assistant fonctionnera en mode web uniquement")

# Test 4: Configuration plateforme
print("\n" + "-"*70)
print("TEST 4: Configuration plateforme")
print("-"*70)

platform_cfg = get_platform_config()
print(f"Plateforme: {platform.system()}")
print(f"Backend recommande: {platform_cfg.get('recommended', 'N/A')}")
print(f"Commande d'installation: {platform_cfg.get('install_cmd', 'N/A')}")
print(f"Notes: {platform_cfg.get('notes', 'N/A')}")

# Test 5: Modele Vosk
print("\n" + "-"*70)
print("TEST 5: Detection du modele Vosk")
print("-"*70)

vosk_model_path = get_vosk_model_path()
if vosk_model_path:
    print(f"[OK] Modele Vosk trouve: {vosk_model_path}")
else:
    print("[X] Aucun modele Vosk trouve")
    print("\nPour telecharger un modele:")
    print("  https://alphacephei.com/vosk/models")
    print("  Recommande: vosk-model-small-fr-0.22")

# Test 6: Backend universel
print("\n" + "-"*70)
print("TEST 6: Initialisation du backend universel")
print("-"*70)

backend = get_universal_backend()
info = backend.get_backend_info()

print(f"\nBackends detectes: {len(info['available_backends'])}")
for b in info['available_backends']:
    if b['status'] == 'available':
        icon = "[OK]"
    else:
        icon = "[X]"
    offline = " (offline)" if b.get('offline') else " (online)"
    print(f"  {icon} {b['name']}{offline}")
    if b.get('error'):
        print(f"      Erreur: {b['error']}")

# Test 7: Selection du meilleur backend
print("\n" + "-"*70)
print("TEST 7: Selection du meilleur backend")
print("-"*70)

best_backend = backend.get_best_backend()
if best_backend:
    print(f"[OK] Meilleur backend selectionne: {best_backend.name}")
    print(f"   Offline: {best_backend.offline}")
    print(f"   Priorite: {best_backend.priority}")
else:
    print("[X] Aucun backend disponible")

# Test 8: Factory STT
print("\n" + "-"*70)
print("TEST 8: Factory STT")
print("-"*70)

try:
    factory = get_stt_factory()
    print("[OK] Factory STT cree")

    stt_engine = create_unified_stt_engine()
    if stt_engine:
        print(f"[OK] Moteur STT cree: {stt_engine.engine_type.value}")
        print(f"   Offline: {stt_engine.is_offline()}")
    else:
        print("[!] Moteur STT: web_only (pas de reconnaissance vocale)")

except Exception as e:
    print(f"[X] Erreur Factory STT: {e}")
    import traceback
    traceback.print_exc()

# Test 9: Instructions d'installation
print("\n" + "-"*70)
print("TEST 9: Instructions d'installation")
print("-"*70)

if info['recommended_install']:
    rec = info['recommended_install']
    print("Installation recommandee:")
    print(f"  Commande: {rec['command']}")
    print(f"  Raison: {rec['reason']}")
else:
    print("[OK] Toutes les dependances sont installees")

# Test 10: Test d'ecoute (si possible)
print("\n" + "-"*70)
print("TEST 10: Test d'ecoute (optionnel)")
print("-"*70)

if best_backend and best_backend.name != 'web_only' and deps.get('microphone'):
    print("\nTest d'ecoute (5 secondes)...")

    try:
        if best_backend.name == 'vosk_sounddevice':
            # Test avec Vosk
            from vosk_sounddevice_stt import create_vosk_engine
            model_path = get_vosk_model_path()

            if model_path:
                print("Creation du moteur Vosk...")
                engine = create_vosk_engine(model_path)

                print("Ecoute pendant 5 secondes...")
                text = engine.listen_once(duration=5.0)

                if text:
                    print(f"[OK] Texte reconnu: {text}")
                else:
                    print("[!] Aucun texte reconnu (parlez plus fort ou plus clairement)")
            else:
                print("[!] Impossible de tester Vosk: aucun modele trouve")

        elif best_backend.name in ['sounddevice_google', 'pyaudio_google']:
            # Test avec Google Speech
            print("Test avec Google Speech API...")
            print("[!] Test non implemente pour Google Speech (necessite une connexion internet)")

    except Exception as e:
        print(f"[X] Erreur lors du test d'ecoute: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[!] Test d'ecoute non disponible (pas de microphone ou pas de backend)")

# Resume
print("\n" + "="*70)
print("RESUME DU TEST")
print("="*70)

available_backends = sum(1 for b in info['available_backends'] if b['status'] == 'available' and b['name'] != 'web_only')
print(f"\nBackends audio disponibles: {available_backends}")
print(f"Backend selectionne: {best_backend.name if best_backend else 'Aucun'}")
print(f"Microphone detecte: {'Oui' if mic_available else 'Non'}")
print(f"Modele Vosk: {'Oui' if vosk_model_path else 'Non'}")

# Recommandations
if available_backends == 0:
    print("\n[!] ACTION REQUISE:")
    print(get_installation_instructions())
elif not vosk_model_path and best_backend and best_backend.name != 'vosk_sounddevice':
    print("\n[!] RECOMMANDATION:")
    print("Telechargez un modele Vosk pour une reconnaissance offline:")
    print("  https://alphacephei.com/vosk/models")
    print("  Modele recommande: vosk-model-small-fr-0.22")

print("\n" + "="*70)
print("TEST TERMINE")
print("="*70 + "\n")

# Code de sortie
if available_backends > 0:
    sys.exit(0)
else:
    sys.exit(1)
