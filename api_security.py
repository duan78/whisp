"""
Module de sécurité pour la gestion des clés API

Ce fichier maintient la compatibilité avec l'ancien code tout en déléguant
au nouveau package core pour éviter les imports circulaires.
"""

# Import everything from core for backward compatibility
from core.api_security import *

# Export all symbols for backward compatibility
__all__ = [
    'get_secure_api_key',
    'set_secure_api_key',
    'migrate_api_keys',
    'APIKeyManager',
    'api_key_manager',
]
