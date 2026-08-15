"""
Configuration globale pour l'assistant vocal Whisp

Ce fichier maintient la compatibilité avec l'ancien code tout en déléguant
au nouveau package core pour éviter les imports circulaires.
"""

# Import everything from core for backward compatibility
# Note: We import from core package to ensure proper initialization order
try:
    from core.config import *
    from core.database_manager import *
    # api_security might not be available if cryptography is not installed
    try:
        from core.api_security import *
    except ImportError:
        # Provide stubs if cryptography is not available
        def get_secure_api_key(service: str) -> str:
            return ""
        def set_secure_api_key(service: str, api_key: str):
            pass
        def migrate_api_keys():
            pass
except ImportError as e:
    print(f"Error importing from core: {e}")
    raise

# Export all symbols for backward compatibility
__all__ = [
    # From core.config
    'WhispConfig',
    'get_config',
    'set_running',
    'get_running',
    'set_dictation_mode',
    'get_dictation_mode',
    'get_dictated_text',
    'append_dictated_text',
    'set_translation_mode',
    'get_translation_mode',
    'get_translation_text',
    'get_target_language',
    'append_translation_text',
    'setstt_engine',
    'getstt_engine',
    'setopenai_api_key',
    'getopenai_api_key',
    'setmistral_api_key',
    'getmistral_api_key',
    'save_preference',
    'get_preference',
    'get_all_preferences',
    'load_tts_engine',
    'verify_api_keys',
    'force_set_env_variables',
    'get_stt_engine',
    'set_stt_engine',
    'get_openai_api_key',
    'set_openai_api_key',
    'get_mistral_api_key',
    'set_mistral_api_key',
    'get_audio_backend',
    'set_audio_backend',
    'is_audio_backend_auto_detected',
    'set_audio_backend_auto_detected',

    # From core.api_security (may be stubs)
    'get_secure_api_key',
    'set_secure_api_key',
    'migrate_api_keys',

    # From core.database_manager
    'initialize_database',
    'save_config',
    'load_config',
    'save_user_preference',
    'load_user_preferences',
    'save_command_aliases',
    'load_command_aliases',
    'add_command_alias',
    'remove_command_alias',
]
