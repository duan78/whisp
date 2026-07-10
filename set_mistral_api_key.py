"""
Script pour définir manuellement la clé API Mistral
"""
import os
import json
import sys

def set_mistral_api_key(key):
    """Définit la clé API Mistral de manière sécurisée et comme variable d'environnement.

    La clé est stockée chiffrée via APIKeyManager (Fernet/PBKDF2) dans
    ~/.whisp/secure/api_keys.enc. Le stockage plaintext dans api_keys.json
    n'est utilisé qu'en repli si la bibliothèque cryptography est absente.
    """
    # Définir la variable d'environnement pour la session courante
    os.environ["MISTRAL_API_KEY"] = key

    # Stockage chiffré (méthode privilégiée)
    try:
        from api_security import set_secure_api_key
        set_secure_api_key("mistral", key)
        print("Clé API Mistral stockée de manière chiffrée (~/.whisp/secure/)")
    except ImportError:
        # Repli : stockage plaintext si cryptography n'est pas disponible
        api_keys_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")
        keys = {}
        if os.path.exists(api_keys_file):
            try:
                with open(api_keys_file, 'r') as f:
                    keys = json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des clés API: {e}")
        keys["mistral"] = key
        os.makedirs(os.path.dirname(api_keys_file), exist_ok=True)
        try:
            with open(api_keys_file, 'w') as f:
                json.dump(keys, f, indent=4)
            print(f"AVERTISSEMENT: cryptography indisponible — clé stockée en clair dans {api_keys_file}")
            print("Installez 'cryptography' pour un stockage chiffré.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la clé API Mistral: {e}")
            return False
    except Exception as e:
        print(f"Erreur lors du stockage chiffré de la clé API: {e}")
        return False


    # Définir la variable d'environnement
    try:
        os.environ["MISTRAL_API_KEY"] = key
        print(f"Variable d'environnement MISTRAL_API_KEY définie")

        # Vérifier que la variable d'environnement est bien définie
        env_key = os.environ.get("MISTRAL_API_KEY", "")
        if not env_key:
            print("AVERTISSEMENT: La variable d'environnement MISTRAL_API_KEY n'a pas été correctement définie")
    except Exception as e:
        print(f"Erreur lors de la définition de la variable d'environnement: {e}")
        return False
    
    # Essayer d'importer et d'utiliser la fonction de config.py si disponible
    try:
        import importlib.util
        spec = importlib.util.find_spec("config")
        if spec:
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            if hasattr(config_module, "set_mistral_api_key"):
                config_module.set_mistral_api_key(key)
                print("Clé API Mistral définie via le module config")
    except Exception as e:
        print(f"Erreur lors de l'utilisation du module config: {e}")
    
    return True

def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python set_mistral_api_key.py <votre_clé_api>")
        return
    
    key = sys.argv[1]
    if not key:
        print("La clé API ne peut pas être vide")
        return
    
    if set_mistral_api_key(key):
        print("Clé API Mistral configurée avec succès")
        
        # Vérifier que la variable d'environnement est bien définie
        env_key = os.environ.get("MISTRAL_API_KEY", "")
        if env_key:
            print(f"Variable d'environnement MISTRAL_API_KEY vérifiée: {env_key[:4]}...{env_key[-4:] if len(env_key) > 8 else ''}")
        else:
            print("AVERTISSEMENT: La variable d'environnement MISTRAL_API_KEY n'est pas définie")
            
            # Afficher toutes les variables d'environnement pour le débogage
            print("\nVariables d'environnement actuelles:")
            for key, value in os.environ.items():
                if "API" in key:
                    masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else value
                    print(f"{key}: {masked_value}")
    else:
        print("Échec de la configuration de la clé API Mistral")

if __name__ == "__main__":
    main()
