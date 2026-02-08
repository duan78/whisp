"""
Configuration globale pour l'assistant vocal Whisp
"""
import os
import json
import threading
from dataclasses import dataclass
from typing import Optional

# Import database functions using lazy import to avoid circular dependency
def _get_db_functions():
    """Lazy import database functions to avoid circular dependency"""
    try:
        from .database_manager import load_config, save_config, save_user_preference, load_user_preferences
        return load_config, save_config, save_user_preference, load_user_preferences
    except ImportError:
        # Fallback to old location during migration
        try:
            from database_manager import load_config, save_config, save_user_preference, load_user_preferences
            return load_config, save_config, save_user_preference, load_user_preferences
        except ImportError:
            # Return stubs if database_manager is not available yet
            def stub(*args, **kwargs):
                pass
            return stub, stub, stub, stub

# Import api_security functions using lazy import
def _get_api_security_functions():
    """Lazy import api_security functions"""
    try:
        from .api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys
        return get_secure_api_key, set_secure_api_key, migrate_api_keys
    except ImportError:
        # Fallback to old location during migration
        try:
            from api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys
            return get_secure_api_key, set_secure_api_key, migrate_api_keys
        except ImportError:
            # Return stubs if api_security is not available
            def stub_get(service: str) -> str:
                return ""
            def stub_set(service: str, key: str):
                pass
            def stub_migrate():
                pass
            return stub_get, stub_set, stub_migrate

# ==============================================================================
# CONFIGURATION CLASS - Thread-safe singleton pattern
# ==============================================================================

@dataclass
class WhispConfig:
    """Configuration centralisée et thread-safe de l'assistant"""

    # État de l'assistant
    running: bool = True
    mode_dictee: bool = False
    mode_traduction: bool = False

    # Moteurs
    stt_engine: str = "speechrecognition"  # Options: "speechrecognition", "nemo", "whisper", "vosk", "whisper_ct2"
    tts_engine: str = "gtts"

    # Texte
    texte_dicte: str = ""
    texte_a_traduire: str = ""
    langue_cible: str = ""

    # Thread-safe lock
    _lock: threading.Lock = threading.Lock()

    # Clés API (gérées de manière sécurisée)
    _api_keys: dict = None

    def __post_init__(self):
        if self._api_keys is None:
            self._api_keys = {}

    # ===== Getters/Setters Thread-Safe =====

    def get_running(self) -> bool:
        with self._lock:
            return self.running

    def set_running(self, state: bool):
        with self._lock:
            self.running = state

    def get_dictation_mode(self) -> bool:
        with self._lock:
            return self.mode_dictee

    def set_dictation_mode(self, state: bool, initial_text: str = ""):
        with self._lock:
            self.mode_dictee = state
            if state:
                self.texte_dicte = initial_text
            else:
                self.texte_dicte = ""

    def get_dictated_text(self) -> str:
        with self._lock:
            return self.texte_dicte

    def append_dictated_text(self, text: str, add_space: bool = True):
        with self._lock:
            if add_space and self.texte_dicte and not self.texte_dicte.endswith(" "):
                self.texte_dicte += " "
            self.texte_dicte += text

    def get_translation_mode(self) -> bool:
        with self._lock:
            return self.mode_traduction

    def set_translation_mode(self, state: bool, langue: str = "", initial_text: str = ""):
        with self._lock:
            self.mode_traduction = state
            if state:
                self.langue_cible = langue
                self.texte_a_traduire = initial_text
            else:
                self.texte_a_traduire = ""
                self.langue_cible = ""

    def get_translation_text(self) -> str:
        with self._lock:
            return self.texte_a_traduire

    def get_target_language(self) -> str:
        with self._lock:
            return self.langue_cible

    def append_translation_text(self, text: str, add_space: bool = True):
        with self._lock:
            if add_space and self.texte_a_traduire and not self.texte_a_traduire.endswith(" "):
                self.texte_a_traduire += " "
            self.texte_a_traduire += text

    def get_stt_engine(self) -> str:
        with self._lock:
            return self.stt_engine

    def set_stt_engine(self, engine: str) -> bool:
        valid_engines = ["speechrecognition", "nemo", "whisper", "vosk", "sherpa_ncnn",
                        "whisper_ct2", "whisper_french"]
        if engine not in valid_engines:
            print(f"Moteur STT non valide: {engine}")
            return False

        with self._lock:
            old_engine = self.stt_engine
            try:
                self.stt_engine = engine
                print(f"Moteur STT configuré: {self.stt_engine}")
                # Sauvegarder dans la base de données
                _, save_config, save_user_preference, _ = _get_db_functions()
                save_config({"stt_engine": engine})
                save_user_preference("stt_engine", engine)
                return True
            except Exception as e:
                print(f"Erreur lors de la configuration du moteur STT: {e}")
                self.stt_engine = old_engine
                print(f"Retour à l'ancien moteur STT: {self.stt_engine}")
                return False

    # ===== Gestion sécurisée des clés API =====

    def get_openai_api_key(self) -> str:
        """Récupère la clé API OpenAI depuis le stockage sécurisé"""
        # Priorité aux variables d'environnement
        env_key = os.environ.get("OPENAI_API_KEY", "")
        if env_key:
            return env_key

        # Sinon, utiliser le stockage sécurisé
        get_secure_api_key, _, _ = _get_api_security_functions()
        return get_secure_api_key("openai")

    def set_openai_api_key(self, key: str) -> bool:
        """Définit la clé API OpenAI de manière sécurisée"""
        try:
            # Définir la variable d'environnement
            if key:
                os.environ["OPENAI_API_KEY"] = key
            elif "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            # Stocker de manière sécurisée
            _, set_secure_api_key, _ = _get_api_security_functions()
            set_secure_api_key("openai", key)

            # Sauvegarder dans la base de données (indicateur uniquement)
            _, save_config, _, _ = _get_db_functions()
            save_config({"openai_api_key_configured": bool(key)})

            return True
        except Exception as e:
            print(f"Erreur lors de la configuration de la clé API OpenAI: {e}")
            return False

    def get_mistral_api_key(self) -> str:
        """Récupère la clé API Mistral depuis le stockage sécurisé"""
        # Priorité aux variables d'environnement
        env_key = os.environ.get("MISTRAL_API_KEY", "")
        if env_key:
            return env_key

        # Sinon, utiliser le stockage sécurisé
        get_secure_api_key, _, _ = _get_api_security_functions()
        return get_secure_api_key("mistral")

    def set_mistral_api_key(self, key: str) -> bool:
        """Définit la clé API Mistral de manière sécurisée"""
        try:
            # Définir la variable d'environnement
            if key:
                os.environ["MISTRAL_API_KEY"] = key
                print(f"Variable d'environnement MISTRAL_API_KEY définie: {key[:4]}...{key[-4:] if len(key) > 8 else ''}")
            elif "MISTRAL_API_KEY" in os.environ:
                del os.environ["MISTRAL_API_KEY"]
                print("Variable d'environnement MISTRAL_API_KEY supprimée")

            # Stocker de manière sécurisée
            _, set_secure_api_key, _ = _get_api_security_functions()
            set_secure_api_key("mistral", key)

            # Sauvegarder dans la base de données (indicateur uniquement)
            _, save_config, _, _ = _get_db_functions()
            save_config({"mistral_api_key_configured": bool(key)})

            return True
        except Exception as e:
            print(f"Erreur lors de la configuration de la clé API Mistral: {e}")
            return False

# ==============================================================================
# SINGLETON INSTANCE
# ==============================================================================

_config_instance: Optional[WhispConfig] = None
_config_lock = threading.Lock()

def get_config() -> WhispConfig:
    """Retourne l'instance singleton de la configuration"""
    global _config_instance
    if _config_instance is None:
        with _config_lock:
            if _config_instance is None:
                _config_instance = WhispConfig()

                # Charger les configurations depuis la base de données
                _load_config_from_db(_config_instance)

    return _config_instance

def _load_config_from_db(config: WhispConfig):
    """Charge les configurations depuis la base de données"""
    try:
        load_config, _, _, _ = _get_db_functions()
        config_dict = load_config()

        if config_dict:
            # Charger le moteur STT
            if "stt_engine" in config_dict:
                config.stt_engine = config_dict["stt_engine"]

            # Charger le moteur TTS
            if "tts_engine" in config_dict:
                config.tts_engine = config_dict["tts_engine"]
    except Exception as e:
        print(f"Erreur lors du chargement de la configuration: {e}")

# ==============================================================================
# COMPATIBILITY FUNCTIONS - Backward compatibility with old code
# ==============================================================================

# These functions maintain backward compatibility while using the new secure system
# They proxy to the singleton config instance

def set_running(state):
    """Définit l'état d'exécution de l'assistant"""
    get_config().set_running(state)

def get_running():
    """Retourne l'état d'exécution de l'assistant"""
    return get_config().get_running()

def set_dictation_mode(state, initial_text=""):
    """Définit l'état du mode dictée"""
    get_config().set_dictation_mode(state, initial_text)

def get_dictation_mode():
    """Retourne l'état du mode dictée"""
    return get_config().get_dictation_mode()

def get_dictated_text():
    """Retourne le texte dicté"""
    return get_config().get_dictated_text()

def append_dictated_text(text, add_space=True):
    """Ajoute du texte à la dictée en cours"""
    get_config().append_dictated_text(text, add_space)

def set_translation_mode(state, langue="", initial_text=""):
    """Définit l'état du mode traduction"""
    get_config().set_translation_mode(state, langue, initial_text)

def get_translation_mode():
    """Retourne l'état du mode traduction"""
    return get_config().get_translation_mode()

def get_translation_text():
    """Retourne le texte à traduire"""
    return get_config().get_translation_text()

def get_target_language():
    """Retourne la langue cible pour la traduction"""
    return get_config().get_target_language()

def append_translation_text(text, add_space=True):
    """Ajoute du texte à la traduction en cours"""
    get_config().append_translation_text(text, add_space)

def setstt_engine(engine):
    """Définit le moteur STT à utiliser"""
    return get_config().set_stt_engine(engine)

def getstt_engine():
    """Retourne le moteur STT actuel"""
    return get_config().get_stt_engine()

def setopenai_api_key(key):
    """Définit la clé API OpenAI"""
    return get_config().set_openai_api_key(key)

def getopenai_api_key():
    """Retourne la clé API OpenAI"""
    return get_config().get_openai_api_key()

def setmistral_api_key(key):
    """Définit la clé API Mistral"""
    return get_config().set_mistral_api_key(key)

def getmistral_api_key():
    """Retourne la clé API Mistral"""
    return get_config().get_mistral_api_key()

# Fonctions pour les préférences utilisateur
def save_preference(key, value):
    """Sauvegarde une préférence utilisateur"""
    _, _, save_user_preference, _ = _get_db_functions()
    return save_user_preference(key, value)

def get_preference(key, default=None):
    """Récupère une préférence utilisateur"""
    _, _, _, load_user_preferences = _get_db_functions()
    value = load_user_preferences(key)
    return value if value is not None else default

def get_all_preferences():
    """Récupère toutes les préférences utilisateur"""
    _, _, _, load_user_preferences = _get_db_functions()
    return load_user_preferences()

# Fonction pour charger le moteur TTS au démarrage
def load_tts_engine():
    """Charge le moteur TTS depuis les préférences utilisateur"""
    tts_engine = get_preference("tts_engine")
    if tts_engine:
        print(f"Moteur TTS chargé depuis les préférences: {tts_engine}")
    return tts_engine

# Fonction pour vérifier les clés API
def verify_api_keys():
    """Vérifie que les clés API sont correctement définies"""
    config = get_config()
    openai_key = config.get_openai_api_key()
    mistral_key = config.get_mistral_api_key()

    if openai_key:
        print(f"Clé API OpenAI détectée: {openai_key[:4]}...{openai_key[-4:] if len(openai_key) > 8 else ''}")

    if mistral_key:
        print(f"Clé API Mistral détectée: {mistral_key[:4]}...{mistral_key[-4:] if len(mistral_key) > 8 else ''}")

# Fonction pour forcer la définition des variables d'environnement
def force_set_env_variables():
    """Force la définition des variables d'environnement pour les clés API"""
    config = get_config()

    openai_key = config.get_openai_api_key()
    if openai_key:
        try:
            os.environ["OPENAI_API_KEY"] = openai_key
            print(f"Variable d'environnement OPENAI_API_KEY forcée: {openai_key[:4]}...{openai_key[-4:] if len(openai_key) > 8 else ''}")
        except Exception as e:
            print(f"Erreur lors de la définition forcée de OPENAI_API_KEY: {e}")

    mistral_key = config.get_mistral_api_key()
    if mistral_key:
        try:
            os.environ["MISTRAL_API_KEY"] = mistral_key
            print(f"Variable d'environnement MISTRAL_API_KEY forcée: {mistral_key[:4]}...{mistral_key[-4:] if len(mistral_key) > 8 else ''}")
        except Exception as e:
            print(f"Erreur lors de la définition forcée de MISTRAL_API_KEY: {e}")

# Alias de compatibilité pour les imports existants
def get_stt_engine():
    """Alias de compatibilité pour getstt_engine"""
    return getstt_engine()

def set_stt_engine(engine):
    """Alias de compatibilité pour setstt_engine"""
    return setstt_engine(engine)

def get_openai_api_key():
    """Alias de compatibilité pour getopenai_api_key"""
    return getopenai_api_key()

def set_openai_api_key(key):
    """Alias de compatibilité pour setopenai_api_key"""
    return setopenai_api_key(key)

def get_mistral_api_key():
    """Alias de compatibilité pour getmistral_api_key"""
    return getmistral_api_key()

def set_mistral_api_key(key):
    """Alias de compatibilité pour setmistral_api_key"""
    return setmistral_api_key(key)

# ==============================================================================
# INITIALIZATION
# ==============================================================================

# Migrer les anciennes clés API vers le stockage sécurisé
try:
    _, _, migrate_api_keys = _get_api_security_functions()
    migrate_api_keys()
except Exception as e:
    print(f"Note: Migration des clés API: {e}")

# Vérifier les clés API après avoir défini toutes les fonctions nécessaires
verify_api_keys()
# Forcer la définition des variables d'environnement
force_set_env_variables()
