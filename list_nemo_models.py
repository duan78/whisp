"""
Script pour lister les modèles NeMo disponibles
"""

import sys
import signal

# Correction pour l'erreur SIGKILL sur Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM

try:
    import nemo.collections.asr as nemo_asr
    
    print("=== Modèles NeMo ASR disponibles ===")
    
    # Lister tous les modèles disponibles
    available_models = nemo_asr.models.EncDecCTCModel.list_available_models()
    
    print(f"Nombre total de modèles: {len(available_models)}")
    
    # Filtrer par langue
    print("\n=== Modèles par langue ===")
    languages = {}
    
    for model_info in available_models:
        # Obtenir le nom du modèle
        model_name = model_info.pretrained_model_name
        
        # Extraire le code de langue du nom du modèle
        parts = model_name.split('_')
        if len(parts) > 1:
            lang_code = parts[1]  # Généralement le format est stt_XX_...
            if lang_code not in languages:
                languages[lang_code] = []
            languages[lang_code].append(model_name)
    
    # Afficher les modèles par langue
    for lang, models in sorted(languages.items()):
        print(f"\n{lang.upper()} ({len(models)} modèles):")
        for model in models:
            print(f"  - {model}")
    
    # Afficher spécifiquement les modèles français
    print("\n=== Modèles français ===")
    fr_models = [m.pretrained_model_name for m in available_models if "_fr_" in m.pretrained_model_name]
    if fr_models:
        for model in fr_models:
            print(f"  - {model}")
    else:
        print("Aucun modèle français trouvé")
        
    # Afficher tous les modèles disponibles avec leurs détails
    print("\n=== Détails de tous les modèles disponibles ===")
    for i, model_info in enumerate(available_models):
        print(f"\nModèle {i+1}: {model_info.pretrained_model_name}")
        print(f"  Description: {model_info.description}")
        print(f"  URL: {model_info.location}")
    
except ImportError:
    print("NVIDIA NeMo n'est pas installé. Veuillez l'installer avec 'pip install nemo_toolkit[asr]'")
    sys.exit(1)
except Exception as e:
    print(f"Erreur: {e}")
    # Supprimer l'avertissement concernant ffmpeg
    if "ffmpeg" in str(e):
        print("Note: Vous pouvez installer ffmpeg en exécutant 'python whisp_assistant\\install_ffmpeg.py'")
    sys.exit(1)
