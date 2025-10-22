"""
Script de diagnostic pour vérifier la disponibilité des modules STT
"""

import sys
import os
import site
import importlib.util

def check_module_installed(module_name):
    """Vérifie si un module est installé et donne des informations sur son emplacement"""
    print(f"\n--- Vérification du module {module_name} ---")
    
    # Vérifier si le module peut être importé
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✅ Module {module_name} trouvé!")
        print(f"   Emplacement: {spec.origin}")
        
        # Essayer d'importer le module pour vérifier qu'il fonctionne correctement
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ Module {module_name} importé avec succès!")
            
            # Afficher la version si disponible
            if hasattr(module, "__version__"):
                print(f"   Version: {module.__version__}")
            elif hasattr(module, "version") and callable(module.version):
                print(f"   Version: {module.version()}")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'importation de {module_name}: {e}")
            return False
    else:
        print(f"❌ Module {module_name} non trouvé")
        return False

def check_python_paths():
    """Affiche les chemins Python pour aider au débogage"""
    print("\n--- Chemins Python ---")
    for i, path in enumerate(sys.path):
        print(f"{i+1}. {path}")

def check_site_packages():
    """Vérifie les chemins des packages installés"""
    print("\n--- Chemins des packages Python ---")
    
    # Packages utilisateur
    user_site = site.getusersitepackages()
    print(f"Packages utilisateur: {user_site}")
    
    # Packages système
    site_packages = site.getsitepackages()
    print("Packages système:")
    for i, path in enumerate(site_packages):
        print(f"{i+1}. {path}")

def main():
    """Fonction principale"""
    print("=== Diagnostic des modules STT ===")
    print(f"Python {sys.version} sur {sys.platform}")
    print(f"Interpréteur: {sys.executable}")
    
    # Vérifier les modules STT
    check_module_installed("speech_recognition")
    check_module_installed("vosk")
    check_module_installed("faster_whisper")
    check_module_installed("ctranslate2")
    
    # Vérifier les dépendances
    check_module_installed("numpy")
    check_module_installed("requests")
    
    # Afficher les chemins Python pour aider au débogage
    check_python_paths()
    check_site_packages()
    
    print("\n=== Recommandations ===")
    print("Si des modules sont manquants, installez-les avec pip:")
    print("- pip install vosk")
    print("- pip install ctranslate2 faster-whisper")
    print("\nSi les modules sont installés mais non détectés, essayez:")
    print("- Redémarrer l'application")
    print("- Vérifier que vous utilisez le bon environnement Python")
    print("- Installer les modules dans l'environnement utilisé par l'application")

if __name__ == "__main__":
    main()
