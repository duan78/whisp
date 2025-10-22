"""
Configuration globale pour l'assistant vocal Whisp
"""
import os
import json
try:
    # Essayer d'abord l'import en tant que package
    from whisp_assistant.database_manager import (
        load_config, save_config, 
        save_user_preference, load_user_preferences
    )
except ImportError:
    # Sinon, utiliser l'import relatif
    from database_manager import (
        load_config, save_config, 
        save_user_preference, load_user_preferences
    )

# Variables globales pour contrôler l'assistant
running = True
mode_dictee = False
texte_dicte = ""

# Variables pour le mode traduction
mode_traduction = False
texte_a_traduire = ""
langue_cible = ""

# Configuration du moteur STT (valeur par défaut)
_stt_engine = "speechrecognition"  # Options: "speechrecognition", "nemo", "whisper", "vosk", "whisper_ct2"

# Clés API (valeurs par défaut)
_openai_api_key = ""
_mistral_api_key = ""

# Chemin vers le fichier de configuration des clés API (pour compatibilité)
_api_keys_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")

# Charger les clés API et configurations au démarrage
def _load_config_from_db():
    global _stt_engine, _openai_api_key, _mistral_api_key
    
    # Charger les configurations depuis la base de données
    config_dict = load_config()
    
    if config_dict:
        # Charger le moteur STT
        if "stt_engine" in config_dict:
            _stt_engine = config_dict["stt_engine"]
        
        # Charger les clés API
        if "openai_api_key" in config_dict:
            _openai_api_key = config_dict["openai_api_key"]
        
        if "mistral_api_key" in config_dict:
            _mistral_api_key = config_dict["mistral_api_key"]

# Charger les clés API depuis les sources traditionnelles (pour compatibilité)
def _load_api_keys():
    global _openai_api_key, _mistral_api_key
    try:
        # D'abord, essayer de charger depuis les variables d'environnement
        env_openai_key = os.environ.get("OPENAI_API_KEY", "")
        env_mistral_key = os.environ.get("MISTRAL_API_KEY", "")
        
        if env_openai_key:
            _openai_api_key = env_openai_key
        
        if env_mistral_key:
            _mistral_api_key = env_mistral_key
            
        # Ensuite, essayer de charger depuis le fichier (priorité plus basse)
        if os.path.exists(_api_keys_file):
            with open(_api_keys_file, 'r') as f:
                keys = json.load(f)
                
                # Ne pas écraser les clés des variables d'environnement
                if not _openai_api_key:
                    _openai_api_key = keys.get("openai", "")
                
                if not _mistral_api_key:
                    _mistral_api_key = keys.get("mistral", "")
                    
            # Migrer les clés vers la base de données
            _save_config_to_db()
    except Exception as e:
        print(f"Erreur lors du chargement des clés API: {e}")

# Sauvegarder les configurations dans la base de données
def _save_config_to_db():
    config_dict = {
        "stt_engine": _stt_engine,
        "openai_api_key": _openai_api_key,
        "mistral_api_key": _mistral_api_key
    }
    save_config(config_dict)

# Sauvegarder les clés API (pour compatibilité)
def _save_api_keys():
    try:
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(_api_keys_file), exist_ok=True)
        
        keys = {
            "openai": _openai_api_key,
            "mistral": _mistral_api_key
        }
        with open(_api_keys_file, 'w') as f:
            json.dump(keys, f, indent=4)
        print(f"Clés API sauvegardées dans {_api_keys_file}")
        
        # Également sauvegarder dans la base de données
        _save_config_to_db()
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des clés API: {e}")

# Définir les variables d'environnement
def _set_env_variables():
    if _openai_api_key:
        os.environ["OPENAI_API_KEY"] = _openai_api_key
    
    if _mistral_api_key:
        os.environ["MISTRAL_API_KEY"] = _mistral_api_key

# Charger les configurations depuis la base de données
_load_config_from_db()
# Charger les clés API depuis les sources traditionnelles (pour compatibilité)
_load_api_keys()
# Définir les variables d'environnement au démarrage
_set_env_variables()

# Fonction pour charger le moteur TTS au démarrage
def load_tts_engine():
    """Charge le moteur TTS depuis les préférences utilisateur"""
    tts_engine = get_preference("tts_engine")
    if tts_engine:
        print(f"Moteur TTS chargé depuis les préférences: {tts_engine}")
    return tts_engine

def set_running(state):
    """Définit l'état d'exécution de l'assistant"""
    global running
    running = state

def get_running():
    """Retourne l'état d'exécution de l'assistant"""
    global running
    return running

def set_dictation_mode(state, initial_text=""):
    """Définit l'état du mode dictée"""
    global mode_dictee, texte_dicte
    mode_dictee = state
    if state:
        texte_dicte = initial_text
    else:
        texte_dicte = ""
    
def get_dictation_mode():
    """Retourne l'état du mode dictée"""
    return mode_dictee

def get_dictated_text():
    """Retourne le texte dicté"""
    return texte_dicte

def append_dictated_text(text, add_space=True):
    """Ajoute du texte à la dictée en cours
    
    Args:
        text (str): Le texte à ajouter
        add_space (bool): Si True, ajoute un espace avant le nouveau texte si nécessaire
    """
    global texte_dicte
    if add_space and texte_dicte and not texte_dicte.endswith(" "):
        texte_dicte += " "
    texte_dicte += text

# Fonctions pour le mode traduction
def set_translation_mode(state, langue="", initial_text=""):
    """Définit l'état du mode traduction
    
    Args:
        state (bool): True pour activer, False pour désactiver
        langue (str): La langue cible pour la traduction
        initial_text (str): Le texte initial à traduire
    """
    global mode_traduction, texte_a_traduire, langue_cible
    mode_traduction = state
    if state:
        langue_cible = langue
        texte_a_traduire = initial_text
    else:
        texte_a_traduire = ""
        langue_cible = ""

def get_translation_mode():
    """Retourne l'état du mode traduction"""
    return mode_traduction

def get_translation_text():
    """Retourne le texte à traduire"""
    return texte_a_traduire

def get_target_language():
    """Retourne la langue cible pour la traduction"""
    return langue_cible

def append_translation_text(text, add_space=True):
    """Ajoute du texte à la traduction en cours
    
    Args:
        text (str): Le texte à ajouter
        add_space (bool): Si True, ajoute un espace avant le nouveau texte si nécessaire
    """
    global texte_a_traduire
    if add_space and texte_a_traduire and not texte_a_traduire.endswith(" "):
        texte_a_traduire += " "
    texte_a_traduire += text

def set_stt_engine(engine):
    """Définit le moteur STT à utiliser"""
    global _stt_engine
    
    # Vérifier que le moteur est valide
    valid_engines = ["speechrecognition", "nemo", "whisper", "vosk", "sherpa_ncnn", "whisper_ct2", "whisper_french"]
    if engine not in valid_engines:
        print(f"Moteur STT non valide: {engine}")
        return False
    
    # Sauvegarder l'ancien moteur pour pouvoir revenir en arrière en cas d'erreur
    old_engine = _stt_engine
    
    try:
        _stt_engine = engine
        print(f"Moteur STT configuré: {_stt_engine}")
        
        # Sauvegarder dans la base de données
        save_config({"stt_engine": engine})
        
        # Sauvegarder comme préférence utilisateur
        save_user_preference("stt_engine", engine)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la configuration du moteur STT: {e}")
        # En cas d'erreur, revenir à l'ancien moteur
        _stt_engine = old_engine
        print(f"Retour à l'ancien moteur STT: {_stt_engine}")
        return False

def get_stt_engine():
    """Retourne le moteur STT actuel"""
    global _stt_engine
    return _stt_engine

def set_openai_api_key(key):
    """Définit la clé API OpenAI"""
    global _openai_api_key
    _openai_api_key = key
    
    # Définir la variable d'environnement
    if key:
        os.environ["OPENAI_API_KEY"] = key
    elif "OPENAI_API_KEY" in os.environ:
        # Supprimer la variable d'environnement si la clé est vide
        del os.environ["OPENAI_API_KEY"]
    
    # Sauvegarder dans la base de données
    save_config({"openai_api_key": key})
    
    # Sauvegarder dans le fichier pour compatibilité
    _save_api_keys()
    
    return True

def get_openai_api_key():
    """Retourne la clé API OpenAI"""
    # Priorité à la variable d'environnement
    env_key = os.environ.get("OPENAI_API_KEY", "")
    if env_key:
        return env_key
    return _openai_api_key

def set_mistral_api_key(key):
    """Définit la clé API Mistral"""
    global _mistral_api_key
    _mistral_api_key = key
    
    # Définir la variable d'environnement
    if key:
        try:
            os.environ["MISTRAL_API_KEY"] = key
            print(f"Variable d'environnement MISTRAL_API_KEY définie: {key[:4]}...{key[-4:] if len(key) > 8 else ''}")
        except Exception as e:
            print(f"Erreur lors de la définition de la variable d'environnement MISTRAL_API_KEY: {e}")
            return False
    elif "MISTRAL_API_KEY" in os.environ:
        # Supprimer la variable d'environnement si la clé est vide
        try:
            del os.environ["MISTRAL_API_KEY"]
            print("Variable d'environnement MISTRAL_API_KEY supprimée")
        except Exception as e:
            print(f"Erreur lors de la suppression de la variable d'environnement MISTRAL_API_KEY: {e}")
    
    # Sauvegarder dans la base de données
    save_config({"mistral_api_key": key})
    
    # Sauvegarder dans le fichier pour compatibilité
    _save_api_keys()
    
    # Vérifier que la clé est bien définie
    env_key = os.environ.get("MISTRAL_API_KEY", "")
    if key and not env_key:
        print("AVERTISSEMENT: La variable d'environnement MISTRAL_API_KEY n'a pas été correctement définie")
        print("Veuillez définir la variable d'environnement manuellement ou redémarrer l'application")
    
    return True

def get_mistral_api_key():
    """Retourne la clé API Mistral"""
    # Priorité à la variable d'environnement
    env_key = os.environ.get("MISTRAL_API_KEY", "")
    if env_key:
        return env_key
    
    # Si pas dans l'environnement mais dans la variable globale, essayer de définir l'environnement
    if _mistral_api_key and not env_key:
        try:
            os.environ["MISTRAL_API_KEY"] = _mistral_api_key
            print(f"Variable d'environnement MISTRAL_API_KEY redéfinie depuis la variable globale")
        except Exception as e:
            print(f"Erreur lors de la redéfinition de la variable d'environnement: {e}")
    
    return _mistral_api_key

# Fonctions pour les préférences utilisateur
def save_preference(key, value):
    """
    Sauvegarde une préférence utilisateur
    
    Args:
        key (str): Clé de la préférence
        value: Valeur de la préférence
    """
    return save_user_preference(key, value)

def get_preference(key, default=None):
    """
    Récupère une préférence utilisateur
    
    Args:
        key (str): Clé de la préférence
        default: Valeur par défaut si la préférence n'existe pas
        
    Returns:
        La valeur de la préférence ou la valeur par défaut
    """
    value = load_user_preferences(key)
    return value if value is not None else default

def get_all_preferences():
    """
    Récupère toutes les préférences utilisateur
    
    Returns:
        dict: Dictionnaire des préférences
    """
    return load_user_preferences()

# Fonction pour vérifier les clés API
def verify_api_keys():
    """Vérifie que les clés API sont correctement définies"""
    openai_key = get_openai_api_key()
    mistral_key = get_mistral_api_key()
    
    if openai_key:
        print(f"Clé API OpenAI détectée: {openai_key[:4]}...{openai_key[-4:] if len(openai_key) > 8 else ''}")
        # Vérifier que la variable d'environnement est définie
        env_key = os.environ.get("OPENAI_API_KEY", "")
        if not env_key:
            print("AVERTISSEMENT: La variable d'environnement OPENAI_API_KEY n'est pas définie")
            # Essayer de la définir à nouveau
            os.environ["OPENAI_API_KEY"] = openai_key
            print("Variable d'environnement OPENAI_API_KEY redéfinie")
    
    if mistral_key:
        print(f"Clé API Mistral détectée: {mistral_key[:4]}...{mistral_key[-4:] if len(mistral_key) > 8 else ''}")
        # Vérifier que la variable d'environnement est définie
        env_key = os.environ.get("MISTRAL_API_KEY", "")
        if not env_key:
            print("AVERTISSEMENT: La variable d'environnement MISTRAL_API_KEY n'est pas définie")
            # Essayer de la définir à nouveau
            os.environ["MISTRAL_API_KEY"] = mistral_key
            print("Variable d'environnement MISTRAL_API_KEY redéfinie")

# Fonction pour forcer la définition des variables d'environnement
def force_set_env_variables():
    """Force la définition des variables d'environnement pour les clés API"""
    global _openai_api_key, _mistral_api_key
    
    if _openai_api_key:
        try:
            os.environ["OPENAI_API_KEY"] = _openai_api_key
            print(f"Variable d'environnement OPENAI_API_KEY forcée: {_openai_api_key[:4]}...{_openai_api_key[-4:] if len(_openai_api_key) > 8 else ''}")
        except Exception as e:
            print(f"Erreur lors de la définition forcée de OPENAI_API_KEY: {e}")
    
    if _mistral_api_key:
        try:
            os.environ["MISTRAL_API_KEY"] = _mistral_api_key
            print(f"Variable d'environnement MISTRAL_API_KEY forcée: {_mistral_api_key[:4]}...{_mistral_api_key[-4:] if len(_mistral_api_key) > 8 else ''}")
        except Exception as e:
            print(f"Erreur lors de la définition forcée de MISTRAL_API_KEY: {e}")

# Vérifier les clés API après avoir défini toutes les fonctions nécessaires
verify_api_keys()
# Forcer la définition des variables d'environnement
force_set_env_variables()
