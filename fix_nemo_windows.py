"""
Script de correction pour NeMo sur Windows
Ce script corrige l'erreur 'signal.SIGKILL' sur Windows
"""

import os
import sys

def fix_nemo_exp_manager():
    """Corrige le fichier exp_manager.py de NeMo pour Windows"""
    try:
        # Trouver le chemin du package NeMo
        import nemo
        nemo_path = os.path.dirname(nemo.__file__)
        exp_manager_path = os.path.join(nemo_path, 'utils', 'exp_manager.py')
        
        if not os.path.exists(exp_manager_path):
            print(f"Fichier exp_manager.py introuvable: {exp_manager_path}")
            return False
        
        # Lire le contenu du fichier
        with open(exp_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si le fichier contient déjà la correction
        if "# Windows compatibility fix" in content:
            print("Le fichier exp_manager.py a déjà été corrigé.")
            return True
        
        # Remplacer la ligne problématique
        if "rank_termination_signal: signal.Signals = signal.SIGKILL" in content:
            content = content.replace(
                "rank_termination_signal: signal.Signals = signal.SIGKILL",
                "# Windows compatibility fix\n    rank_termination_signal: signal.Signals = getattr(signal, 'SIGKILL', signal.SIGTERM)"
            )
            
            # Écrire le contenu modifié
            with open(exp_manager_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Correction appliquée avec succès à {exp_manager_path}")
            return True
        else:
            print("La ligne problématique n'a pas été trouvée dans le fichier.")
            return False
    
    except Exception as e:
        print(f"Erreur lors de la correction du fichier: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Correction de NeMo pour Windows ===")
    
    try:
        import nemo
        print(f"NeMo version {nemo.__version__} trouvé.")
    except ImportError:
        print("NeMo n'est pas installé. Veuillez l'installer d'abord.")
        return
    
    success = fix_nemo_exp_manager()
    
    if success:
        print("\n=== Correction terminée avec succès ===")
        print("Vous pouvez maintenant utiliser NeMo sur Windows.")
    else:
        print("\n=== Échec de la correction ===")
        print("Veuillez utiliser SpeechRecognition comme moteur STT pour le moment.")

if __name__ == "__main__":
    main()
