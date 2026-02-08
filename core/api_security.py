"""
Module de sécurité pour la gestion des clés API
"""

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pathlib import Path

class APIKeyManager:
    """Gestionnaire sécurisé pour les clés API"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".whisp" / "secure"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.config_dir / "api_keys.enc"
        self.master_key = self._get_or_create_master_key()
        self.cipher = Fernet(self.master_key)
    
    def _get_or_create_master_key(self):
        """Obtient ou crée une clé de chiffrement principale"""
        key_path = self.config_dir / ".key"
        
        if key_path.exists():
            with open(key_path, 'rb') as f:
                return f.read()
        
        # Générer une nouvelle clé basée sur l'identifiant machine
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Utiliser une combinaison d'identifiants système comme base
        system_id = f"{os.environ.get('COMPUTERNAME', '')}{os.environ.get('USERNAME', '')}"
        if not system_id:
            system_id = f"{os.uname().nodename}{os.getuid()}"
        
        key_material = system_id.encode() + salt
        key = base64.urlsafe_b64encode(kdf.derive(key_material[:32]))
        
        # Sauvegarder la clé
        with open(key_path, 'wb') as f:
            f.write(key)
        
        # Protéger le fichier (lecture seule pour le propriétaire)
        os.chmod(key_path, 0o600)
        
        return key
    
    def store_api_key(self, service: str, api_key: str):
        """Stocke une clé API de manière sécurisée"""
        # Charger les clés existantes
        keys = self._load_keys()
        
        # Ajouter/mettre à jour la clé
        keys[service] = api_key
        
        # Chiffrer et sauvegarder
        encrypted_data = self.cipher.encrypt(json.dumps(keys).encode())
        with open(self.key_file, 'wb') as f:
            f.write(encrypted_data)
        
        # Protéger le fichier
        os.chmod(self.key_file, 0o600)
    
    def get_api_key(self, service: str) -> str:
        """Récupère une clé API de manière sécurisée"""
        # D'abord vérifier les variables d'environnement
        env_var_name = f"{service.upper()}_API_KEY"
        env_key = os.environ.get(env_var_name)
        if env_key:
            return env_key
        
        # Sinon, charger depuis le stockage sécurisé
        keys = self._load_keys()
        return keys.get(service, "")
    
    def _load_keys(self) -> dict:
        """Charge les clés depuis le fichier chiffré"""
        if not self.key_file.exists():
            return {}
        
        try:
            with open(self.key_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception:
            return {}
    
    def remove_api_key(self, service: str):
        """Supprime une clé API"""
        keys = self._load_keys()
        if service in keys:
            del keys[service]
            
            if keys:
                # Sauvegarder les clés restantes
                encrypted_data = self.cipher.encrypt(json.dumps(keys).encode())
                with open(self.key_file, 'wb') as f:
                    f.write(encrypted_data)
            else:
                # Supprimer le fichier s'il n'y a plus de clés
                self.key_file.unlink(missing_ok=True)
    
    def migrate_from_plaintext(self, plaintext_file: str):
        """Migre les clés depuis un fichier en clair"""
        if not os.path.exists(plaintext_file):
            return False
        
        try:
            with open(plaintext_file, 'r') as f:
                keys = json.load(f)
            
            # Stocker chaque clé de manière sécurisée
            for service, api_key in keys.items():
                if api_key:
                    self.store_api_key(service, api_key)
            
            # Supprimer le fichier en clair après migration
            os.remove(plaintext_file)
            print(f"Migration réussie: {plaintext_file} -> stockage sécurisé")
            return True
            
        except Exception as e:
            print(f"Erreur lors de la migration: {e}")
            return False

# Instance globale du gestionnaire
api_key_manager = APIKeyManager()

def get_secure_api_key(service: str) -> str:
    """Interface simple pour obtenir une clé API"""
    return api_key_manager.get_api_key(service)

def set_secure_api_key(service: str, api_key: str):
    """Interface simple pour définir une clé API"""
    api_key_manager.store_api_key(service, api_key)

def migrate_api_keys():
    """Migre les clés API depuis l'ancien système"""
    old_api_keys_file = os.path.join(os.path.dirname(__file__), "api_keys.json")
    if os.path.exists(old_api_keys_file):
        api_key_manager.migrate_from_plaintext(old_api_keys_file)