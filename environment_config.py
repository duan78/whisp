"""
Gestionnaire de configuration basé sur l'environnement
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class EnvironmentConfig:
    """Gestionnaire de configuration centralisé basé sur les variables d'environnement"""
    
    def __init__(self):
        self._load_env_file()
        self._config_cache: Dict[str, Any] = {}
        self.environment = self.get('WHISP_ENV', 'development')
    
    def _load_env_file(self):
        """Charge le fichier .env s'il existe"""
        # Chercher le fichier .env dans différents emplacements
        possible_paths = [
            Path('.env'),
            Path(__file__).parent / '.env',
            Path(__file__).parent.parent / '.env',
            Path.home() / '.whisp' / '.env'
        ]
        
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                print(f"Configuration chargée depuis: {env_path}")
                break
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtient une valeur de configuration
        
        Args:
            key: Clé de configuration
            default: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration
        """
        # Vérifier le cache
        if key in self._config_cache:
            return self._config_cache[key]
        
        # Obtenir depuis l'environnement
        value = os.environ.get(key, default)
        
        # Convertir les types si nécessaire
        if value is not None:
            value = self._convert_type(value)
        
        # Mettre en cache
        self._config_cache[key] = value
        
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Obtient une valeur booléenne"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Obtient une valeur entière"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Obtient une valeur flottante"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_path(self, key: str, default: Optional[str] = None) -> Path:
        """Obtient un chemin en expandant les variables"""
        value = self.get(key, default)
        if value:
            path = Path(value).expanduser()
            # Créer le répertoire s'il n'existe pas (pour les répertoires de config)
            if key.endswith('_DIR') and not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            return path
        return Path(default) if default else Path.home()
    
    def _convert_type(self, value: str) -> Any:
        """Convertit automatiquement les types courants"""
        # Booléens
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Nombres
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Chaîne par défaut
        return value
    
    def is_development(self) -> bool:
        """Vérifie si on est en environnement de développement"""
        return self.environment == 'development'
    
    def is_production(self) -> bool:
        """Vérifie si on est en environnement de production"""
        return self.environment == 'production'
    
    def is_test(self) -> bool:
        """Vérifie si on est en environnement de test"""
        return self.environment == 'test'

# Instance globale
env_config = EnvironmentConfig()

# === Configuration de l'application ===

class AppConfig:
    """Configuration de l'application basée sur l'environnement"""
    
    # Environnement
    ENVIRONMENT = env_config.environment
    DEBUG = env_config.is_development()
    
    # API Keys (depuis le stockage sécurisé si disponible)
    OPENAI_API_KEY = env_config.get('OPENAI_API_KEY', '')
    MISTRAL_API_KEY = env_config.get('MISTRAL_API_KEY', '')
    
    # STT Configuration
    STT_ENGINE = env_config.get('STT_ENGINE', 'speechrecognition')
    WHISPER_MODEL = env_config.get('WHISPER_MODEL', 'base')
    WHISPER_LANGUAGE = env_config.get('WHISPER_LANGUAGE', 'fr')
    WHISPER_COMPUTE_TYPE = env_config.get('WHISPER_COMPUTE_TYPE', 'float16')
    
    # TTS Configuration
    TTS_ENGINE = env_config.get('TTS_ENGINE', 'gtts')
    COQUI_MODEL_NAME = env_config.get('COQUI_MODEL_NAME', 'tts_models/fr/mai/tacotron2-DDC')
    
    # Web Interface
    WEB_PORT = env_config.get_int('WEB_PORT', 5000)
    WEB_HOST = env_config.get('WEB_HOST', '127.0.0.1')
    FLASK_DEBUG = env_config.get_bool('FLASK_DEBUG', False)
    
    # Security
    SECRET_KEY = env_config.get('SECRET_KEY', 'dev-secret-key-change-this')
    WEB_AUTH_ENABLED = env_config.get_bool('WEB_AUTH_ENABLED', False)
    WEB_USERNAME = env_config.get('WEB_USERNAME', 'admin')
    WEB_PASSWORD = env_config.get('WEB_PASSWORD', 'changeme')
    
    # Logging
    LOG_LEVEL = env_config.get('LOG_LEVEL', 'INFO')
    LOG_DIR = env_config.get_path('LOG_DIR', '~/.whisp/logs')
    LOG_MAX_SIZE = env_config.get_int('LOG_MAX_SIZE', 10) * 1024 * 1024  # Convert to bytes
    LOG_BACKUP_COUNT = env_config.get_int('LOG_BACKUP_COUNT', 5)
    
    # Performance
    COMMAND_THREADS = env_config.get_int('COMMAND_THREADS', 4)
    COMMAND_TIMEOUT = env_config.get_int('COMMAND_TIMEOUT', 30)
    TTS_CACHE_SIZE = env_config.get_int('TTS_CACHE_SIZE', 100)
    
    # Paths
    DATA_DIR = env_config.get_path('DATA_DIR', '~/.whisp/data')
    CACHE_DIR = env_config.get_path('CACHE_DIR', '~/.whisp/cache')
    BACKUP_DIR = env_config.get_path('BACKUP_DIR', '~/.whisp/backups')
    
    # Development
    AUTO_RELOAD = env_config.get_bool('AUTO_RELOAD', False)
    VERBOSE = env_config.get_bool('VERBOSE', False)
    ENABLE_METRICS = env_config.get_bool('ENABLE_METRICS', True)
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Retourne la configuration sous forme de dictionnaire"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and key.isupper()
        }