"""
Module de gestion de la base de données SQLite pour l'assistant Whisp

Ce fichier maintient la compatibilité avec l'ancien code tout en déléguant
au nouveau package core pour éviter les imports circulaires.
"""

# Import everything from core for backward compatibility
from core.database_manager import *

# Export all symbols for backward compatibility
__all__ = [
    'initialize_database',
    'save_config',
    'load_config',
    'save_user_preference',
    'load_user_preferences',
    'save_command_aliases',
    'load_command_aliases',
    'add_command_alias',
    'remove_command_alias',
    'save_web_log',
    'get_web_logs',
    'save_stt_metric',
    'get_stt_metrics',
    'save_stt_metrics_history',
    'get_stt_metrics_history',
    'reset_stt_metrics_db',
    'save_error_log',
    'get_error_logs',
    'save_tts_cache',
    'get_tts_cache',
    'save_custom_shortcut',
    'get_custom_shortcuts',
    'get_custom_shortcut_by_command',
    'update_custom_shortcut',
    'delete_custom_shortcut',
    'update_custom_shortcut_usage',
    'save_stt_settings',
    'load_stt_settings',
    'get_db_info',
    'ensure_connection',
    'DB_PATH',
]
