"""
Package core - Modules fondamentaux de Whisp Assistant

Ce package contient les modules de base qui n'ont pas de dépendances cycliques
avec les modules de commandes.

Hiérarchie des dépendances:
1. api_security - Fondamental, aucune dépendance locale
2. error_handler - Fondamental, aucune dépendance locale
3. database_manager - Dépend de error_handler (lazy import)
4. config - Dépend de api_security et database_manager (lazy import)

Modules de commandes - Dépendent de config mais ne sont pas importés par config
"""

# Import error_handler first (no dependencies)
from .error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Import database_manager (uses lazy import of error_handler)
from .database_manager import (
    initialize_database,
    save_config, load_config,
    save_user_preference, load_user_preferences,
    save_command_aliases, load_command_aliases,
    add_command_alias, remove_command_alias
)

# Import config (uses lazy import of database_manager)
from .config import WhispConfig, get_config

# Import api_security (may fail if cryptography is not installed)
try:
    from .api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys
    _api_security_available = True
except ImportError:
    # cryptography not installed, provide stubs
    _api_security_available = False
    def get_secure_api_key(service: str) -> str:
        """Stub when cryptography is not available"""
        return ""
    def set_secure_api_key(service: str, api_key: str):
        """Stub when cryptography is not available"""
        pass
    def migrate_api_keys():
        """Stub when cryptography is not available"""
        pass

__all__ = [
    # API Security
    'get_secure_api_key',
    'set_secure_api_key',
    'migrate_api_keys',

    # Error Handler
    'get_error_handler',
    'ErrorCategory',
    'ErrorSeverity',
    'catch_errors',

    # Database Manager
    'initialize_database',
    'save_config',
    'load_config',
    'save_user_preference',
    'load_user_preferences',
    'save_command_aliases',
    'load_command_aliases',
    'add_command_alias',
    'remove_command_alias',

    # Config
    'WhispConfig',
    'get_config',
]
