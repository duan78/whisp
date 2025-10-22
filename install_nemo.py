"""
Script d'installation de NVIDIA NeMo pour l'assistant vocal Whisp
"""

import os
import sys
import subprocess
import platform

def check_cuda():
    """Vérifie si CUDA est installé et disponible"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"CUDA est disponible: {torch.cuda.get_device_name(0)}")
            print(f"Version CUDA: {torch.version.cuda}")
            return True
        else:
            print("CUDA n'est pas disponible. NeMo fonctionnera sur CPU (performances réduites).")
            return False
    except ImportError:
        print("PyTorch n'est pas installé. Installation de PyTorch...")
        return False

def install_pytorch():
    """Installe PyTorch avec le support CUDA approprié"""
    system = platform.system()
    if system == "Windows":
        # Installation de PyTorch pour Windows
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio", 
            "--index-url", "https://download.pytorch.org/whl/cu118"
        ]
    else:
        # Installation de PyTorch pour Linux/MacOS
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "torch", "torchvision", "torchaudio"
        ]
    
    print("Installation de PyTorch...")
    subprocess.run(cmd, check=True)
    print("PyTorch installé avec succès.")

def install_nemo():
    """Installe NVIDIA NeMo"""
    print("Installation de NVIDIA NeMo...")
    
    # Installer les dépendances
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "matplotlib", "numpy", "scipy", "librosa"
    ], check=True)
    
    # Installer NeMo
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "nemo_toolkit[asr]"
    ], check=True)
    
    print("NVIDIA NeMo installé avec succès.")

def download_french_model():
    """Télécharge le modèle français pour NeMo"""
    try:
        print("Téléchargement du modèle français pour NeMo...")
        import nemo.collections.asr as nemo_asr
        
        # Télécharger le modèle
        model = nemo_asr.models.EncDecCTCModel.from_pretrained("stt_fr_conformer_ctc_large")
        
        print("Modèle français téléchargé avec succès.")
        return True
    except Exception as e:
        print(f"Erreur lors du téléchargement du modèle: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Installation de NVIDIA NeMo pour Whisp Assistant ===")
    
    # Vérifier si CUDA est disponible
    cuda_available = check_cuda()
    
    # Installer PyTorch si nécessaire
    try:
        import torch
    except ImportError:
        install_pytorch()
    
    # Installer NeMo
    try:
        import nemo
        print("NVIDIA NeMo est déjà installé.")
    except ImportError:
        install_nemo()
    
    # Télécharger le modèle français
    download_french_model()
    
    print("\n=== Installation terminée ===")
    print("Vous pouvez maintenant utiliser NVIDIA NeMo comme moteur de reconnaissance vocale dans Whisp Assistant.")
    print("Redémarrez l'assistant et sélectionnez 'NVIDIA NeMo (continu)' dans l'interface web.")

if __name__ == "__main__":
    main()
