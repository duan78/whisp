"""
Utilitaire pour gérer les imports relatifs et absolus de manière cohérente
"""

import sys
import os
from typing import Any, Optional

def safe_import(module_name: str, attribute: Optional[str] = None) -> Any:
    """
    Importe un module de manière sûre en gérant les imports relatifs et absolus
    
    Args:
        module_name: Nom du module à importer
        attribute: Attribut spécifique à extraire du module
        
    Returns:
        Le module importé ou l'attribut demandé
    """
    try:
        # Essayer d'abord l'import en tant que package
        if attribute:
            module = __import__(f'whisp_assistant.{module_name}', fromlist=[attribute])
            return getattr(module, attribute)
        else:
            return __import__(f'whisp_assistant.{module_name}')
    except ImportError:
        try:
            # Sinon, utiliser l'import relatif
            if attribute:
                module = __import__(module_name, fromlist=[attribute])
                return getattr(module, attribute)
            else:
                return __import__(module_name)
        except ImportError as e:
            print(f"Impossible d'importer {module_name}: {e}")
            return None

def ensure_module_path():
    """S'assure que le chemin du module est dans sys.path"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Appeler au chargement du module
ensure_module_path()

# Dictionnaire pour cacher les modules importés
_module_cache = {}

def get_module(module_name: str) -> Any:
    """
    Obtient un module depuis le cache ou l'importe
    
    Args:
        module_name: Nom du module
        
    Returns:
        Le module importé
    """
    if module_name not in _module_cache:
        _module_cache[module_name] = safe_import(module_name)
    
    return _module_cache[module_name]

def get_function(module_name: str, function_name: str) -> Any:
    """
    Obtient une fonction spécifique d'un module
    
    Args:
        module_name: Nom du module
        function_name: Nom de la fonction
        
    Returns:
        La fonction ou None si non trouvée
    """
    module = get_module(module_name)
    if module and hasattr(module, function_name):
        return getattr(module, function_name)
    return None

# Alias pour les imports courants
def import_config():
    """Importe le module config"""
    return get_module('config')

def import_tts():
    """Importe le module TTS"""
    return get_module('tts_module')

def import_stt():
    """Importe le module STT"""
    return get_module('speech_recognition_module')

def import_web_interface():
    """Importe le module interface web"""
    return get_module('web_interface')

def import_error_handler():
    """Importe le gestionnaire d'erreurs"""
    return get_module('error_handler')