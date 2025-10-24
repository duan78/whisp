"""
Module de reconnaissance vocale pour l'assistant Whisp
"""

import queue
import threading
import time
import sys
import os
import statistics
import json
import tempfile
import wave
import hashlib
import concurrent.futures
from datetime import datetime
from collections import OrderedDict
from pathlib import Path
from config import get_dictation_mode, get_running, get_stt_engine, set_stt_engine, get_openai_api_key, get_translation_mode
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Imports audio pour fallback (sounddevice pour ARM64)
try:
    import sounddevice as sd
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    print("sounddevice non disponible, fallback sur PyAudio")
    SOUNDDEVICE_AVAILABLE = False

# Import des optimisations Numba
try:
    from audio_optimization import optimize_audio_processing, is_speech_active, audio_optimizer
    NUMBA_AVAILABLE = True
except ImportError as e:
    print(f"Numba non disponible, utilisation des fonctions standards: {e}")
    NUMBA_AVAILABLE = False

# Configurer les chemins CUDA pour les packages installés via pip
def set_cuda_paths():
    """Configure les chemins CUDA/cuDNN pour les packages installés via pip"""
    try:
        venv_base = Path(sys.executable).parent.parent
        nvidia_base_path = venv_base / 'Lib' / 'site-packages' / 'nvidia'
        
        if not nvidia_base_path.exists():
            print(f"Dossier packages NVIDIA non trouvé à {nvidia_base_path}")
            return False
            
        # Chemins des DLLs pour différents packages
        paths_to_add = []
        for subdir in ['cuda_runtime', 'cublas', 'cudnn', 'cuda_nvrtc']:
            dll_path = nvidia_base_path / subdir / 'bin'
            if dll_path.exists():
                paths_to_add.append(str(dll_path))
                print(f"Chemin CUDA trouvé: {dll_path}")
        
        if not paths_to_add:
            print("Aucun chemin CUDA trouvé dans les packages pip")
            return False
            
        # Variables d'environnement à mettre à jour
        env_vars = ['CUDA_PATH', 'CUDA_PATH_V12_4', 'PATH']
        
        # Mettre à jour les variables d'environnement
        for env_var in env_vars:
            current_value = os.environ.get(env_var, '')
            new_value = os.pathsep.join(paths_to_add + [current_value] if current_value else paths_to_add)
            os.environ[env_var] = new_value
            
        print(f"Variables d'environnement CUDA mises à jour avec {len(paths_to_add)} chemins")
        return True
    except Exception as e:
        print(f"Erreur lors de la configuration des chemins CUDA via pip: {e}")
        return False

# Configurer les chemins CUDA au démarrage
set_cuda_paths()

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

# Importations conditionnelles - chargées à la demande
import speech_recognition as sr
np = None
requests = None

# Variables pour les modules optionnels
VOSK_AVAILABLE = False
WHISPER_CT2_AVAILABLE = False
Model = None
KaldiRecognizer = None
SetLogLevel = None
WhisperModel = None

# Tenter de précharger les modules optionnels au démarrage
try:
    from vosk import Model as VoskModel, KaldiRecognizer as VoskRecognizer, SetLogLevel as VoskSetLogLevel
    Model = VoskModel
    KaldiRecognizer = VoskRecognizer
    SetLogLevel = VoskSetLogLevel
    # Réduire la verbosité des logs Vosk
    SetLogLevel(-1)
    VOSK_AVAILABLE = True
    print("Module Vosk importé avec succès au démarrage")
except ImportError:
    print("Module Vosk non disponible au démarrage. Sera essayé à nouveau si nécessaire.")
    VOSK_AVAILABLE = False

try:
    from faster_whisper import WhisperModel as FasterWhisperModel
    WhisperModel = FasterWhisperModel
    WHISPER_CT2_AVAILABLE = True
    print("Module Whisper CT2 importé avec succès au démarrage")
except ImportError:
    print("Module Whisper CT2 non disponible au démarrage. Sera essayé à nouveau si nécessaire.")
    WHISPER_CT2_AVAILABLE = False

# Fonction pour importer speech_recognition à la demande
def import_speech_recognition():
    global sr
    # Le module est déjà importé directement au début du fichier
    # pour éviter les problèmes de récursion
    if sr is not None:
        print("Module speech_recognition déjà importé")
        return True
    try:
        # Vérifier si le module est accessible
        if not hasattr(sr, 'Recognizer'):
            print("Erreur: Module speech_recognition importé mais incomplet")
            return False
        print("Module speech_recognition vérifié avec succès")
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification de speech_recognition: {e}")
        return False

# Fonction pour importer numpy à la demande
def import_numpy():
    global np
    if np is None:
        try:
            import numpy as np_module
            np = np_module
            print("Module numpy importé avec succès")
            return True
        except ImportError as e:
            print(f"Erreur lors de l'importation de numpy: {e}")
            return False
    return True

# Fonction pour importer requests à la demande
def import_requests():
    global requests
    if requests is None:
        try:
            import requests as requests_module
            requests = requests_module
            print("Module requests importé avec succès")
            return True
        except ImportError as e:
            print(f"Erreur lors de l'importation de requests: {e}")
            return False
    return True

# Fonction de capture audio alternative avec sounddevice (pour ARM64/PyAudio incompatible)
class SoundDeviceInputStream:
    """Flux d'entrée audio utilisant sounddevice comme alternative à PyAudio"""

    def __init__(self, sample_rate=16000, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.stream = None
        self.is_open = False

    def __enter__(self):
        """Ouvre le flux audio (compatibilité avec context manager)"""
        self.open()
        return self

    def open(self):
        """Ouvre le flux audio"""
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                blocksize=self.chunk_size
            )
            self.stream.start()
            self.is_open = True
        except Exception as e:
            print(f"Erreur lors de l'ouverture du flux sounddevice: {e}")
            raise

    def start(self):
        """Démarre le flux audio (si pas déjà démarré)"""
        if not self.is_open:
            self.open()
        elif self.stream and not self.stream.active:
            self.stream.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ferme le flux audio"""
        self.close()

    def read(self, chunk_size=None):
        """Lit un chunk audio du flux"""
        if not self.is_open or self.stream is None:
            raise RuntimeError("Le flux n'est pas ouvert")

        try:
            chunk_size = chunk_size or self.chunk_size
            data, overflowed = self.stream.read(chunk_size)
            if overflowed:
                print("Avertissement: Buffer overflow audio")
            return data.tobytes()
        except Exception as e:
            print(f"Erreur lors de la lecture audio: {e}")
            # Retourner un buffer vide en cas d'erreur
            return bytes(chunk_size * 2 if chunk_size else self.chunk_size * 2)

    def close(self):
        """Ferme le flux audio"""
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture du flux: {e}")
            finally:
                self.stream = None
                self.is_open = False

def create_microphone_alternative(sample_rate=16000):
    """Crée un microphone alternative utilisant sounddevice si PyAudio n'est pas disponible"""
    if SOUNDDEVICE_AVAILABLE:
        try:
            # Créer un objet qui imite sr.Microphone mais utilise sounddevice
            class AlternativeMicrophone:
                def __init__(self, sample_rate=16000):
                    self.sample_rate = sample_rate
                    self.stream = None

                def __enter__(self):
                    self.stream = SoundDeviceInputStream(sample_rate=self.sample_rate)
                    # Forcer l'ouverture immédiate du flux sounddevice
                    self.stream.open()
                    return self  # Retourner self (comme sr.Microphone)

                def __exit__(self, exc_type, exc_val, exc_tb):
                    if self.stream:
                        self.stream.close()

            print(f"Microphone alternative créé avec sounddevice (taux: {sample_rate} Hz)")
            return AlternativeMicrophone(sample_rate=sample_rate)
        except Exception as e:
            print(f"Erreur lors de la création du microphone alternative: {e}")
            return None
    else:
        print("sounddevice n'est pas disponible pour créer un microphone alternative")
        return None

# Fonction pour importer Vosk à la demande avec plusieurs tentatives
def import_vosk():
    global VOSK_AVAILABLE, Model, KaldiRecognizer, SetLogLevel
    
    # Si déjà importé avec succès, retourner directement
    if VOSK_AVAILABLE and Model is not None:
        return True
    
    # Tentative d'importation avec recherche dans différents chemins
    try:
        # 1. Tentative d'importation directe
        from vosk import Model as VoskModel, KaldiRecognizer as VoskRecognizer, SetLogLevel as VoskSetLogLevel
        Model = VoskModel
        KaldiRecognizer = VoskRecognizer
        SetLogLevel = VoskSetLogLevel
        # Réduire la verbosité des logs Vosk
        SetLogLevel(-1)
        VOSK_AVAILABLE = True
        print("Module Vosk importé avec succès")
        return True
    except ImportError as e:
        print(f"Première tentative d'importation Vosk échouée: {e}")
        
        # 2. Tentative avec sys.path modifié
        import sys
        import site
        import os
        
        # Ajouter les chemins potentiels où Vosk pourrait être installé
        potential_paths = []
        
        # Chemins des packages utilisateur
        site_packages = site.getusersitepackages()
        if isinstance(site_packages, str):
            potential_paths.append(site_packages)
        elif isinstance(site_packages, list):
            potential_paths.extend(site_packages)
            
        # Chemins des packages système
        site_paths = site.getsitepackages()
        potential_paths.extend(site_paths)
        
        # Chercher dans les sous-répertoires potentiels
        for path in list(potential_paths):
            if os.path.exists(path):
                for subdir in os.listdir(path):
                    if "vosk" in subdir.lower():
                        subpath = os.path.join(path, subdir)
                        if os.path.isdir(subpath):
                            potential_paths.append(subpath)
        
        # Ajouter temporairement ces chemins à sys.path
        original_path = sys.path.copy()
        for path in potential_paths:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        try:
            # Nouvelle tentative d'importation
            from vosk import Model as VoskModel, KaldiRecognizer as VoskRecognizer, SetLogLevel as VoskSetLogLevel
            Model = VoskModel
            KaldiRecognizer = VoskRecognizer
            SetLogLevel = VoskSetLogLevel
            SetLogLevel(-1)
            VOSK_AVAILABLE = True
            print(f"Module Vosk importé avec succès après ajustement du chemin Python")
            return True
        except ImportError as e2:
            print(f"Deuxième tentative d'importation Vosk échouée: {e2}")
            print("Vérifiez que Vosk est bien installé avec: pip install vosk")
            print("Chemins Python actuels:", sys.path)
            VOSK_AVAILABLE = False
            return False
        finally:
            # Restaurer le chemin Python original
            sys.path = original_path
    
    return VOSK_AVAILABLE

# Fonction pour importer Whisper CT2 à la demande avec plusieurs tentatives
def import_whisper_ct2():
    global WHISPER_CT2_AVAILABLE, WhisperModel
    
    # Si déjà importé avec succès, retourner directement
    if WHISPER_CT2_AVAILABLE and WhisperModel is not None:
        return True
    
    # Tentative d'importation avec recherche dans différents chemins
    try:
        # 1. Tentative d'importation directe
        from faster_whisper import WhisperModel as FasterWhisperModel
        WhisperModel = FasterWhisperModel
        WHISPER_CT2_AVAILABLE = True
        print("Module Whisper CT2 importé avec succès")
        return True
    except ImportError as e:
        print(f"Première tentative d'importation Whisper CT2 échouée: {e}")
        
        # 2. Tentative avec sys.path modifié
        import sys
        import site
        import os
        
        # Ajouter les chemins potentiels où Whisper CT2 pourrait être installé
        potential_paths = []
        
        # Chemins des packages utilisateur
        site_packages = site.getusersitepackages()
        if isinstance(site_packages, str):
            potential_paths.append(site_packages)
        elif isinstance(site_packages, list):
            potential_paths.extend(site_packages)
            
        # Chemins des packages système
        site_paths = site.getsitepackages()
        potential_paths.extend(site_paths)
        
        # Chercher dans les sous-répertoires potentiels
        for path in list(potential_paths):
            if os.path.exists(path):
                for subdir in os.listdir(path):
                    if "faster_whisper" in subdir.lower() or "ctranslate2" in subdir.lower():
                        subpath = os.path.join(path, subdir)
                        if os.path.isdir(subpath):
                            potential_paths.append(subpath)
        
        # Ajouter temporairement ces chemins à sys.path
        original_path = sys.path.copy()
        for path in potential_paths:
            if path not in sys.path:
                sys.path.insert(0, path)
        
        try:
            # Nouvelle tentative d'importation
            from faster_whisper import WhisperModel as FasterWhisperModel
            WhisperModel = FasterWhisperModel
            WHISPER_CT2_AVAILABLE = True
            print(f"Module Whisper CT2 importé avec succès après ajustement du chemin Python")
            return True
        except ImportError as e2:
            print(f"Deuxième tentative d'importation Whisper CT2 échouée: {e2}")
            print("Vérifiez que les packages sont bien installés avec: pip install ctranslate2 faster-whisper")
            print("Chemins Python actuels:", sys.path)
            WHISPER_CT2_AVAILABLE = False
            return False
        finally:
            # Restaurer le chemin Python original
            sys.path = original_path
    
    return WHISPER_CT2_AVAILABLE


# Supprimer l'avertissement de pydub concernant ffmpeg
import warnings
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv")

# Import numpy pour les autres fonctionnalités
import numpy as np

# Paramètres par défaut pour la reconnaissance vocale
DEFAULT_STT_SETTINGS = {
    "pause_threshold": 1.5,  # Valeur plus élevée pour attendre plus longtemps entre les phrases
    "energy_threshold": 200,  # Seuil d'énergie pour détecter la parole
    "non_speaking_duration": 0.8,  # Durée de silence plus longue pour considérer la fin d'une phrase
    "phrase_timeout": 5.0,  # Timeout plus long pour capturer des phrases complètes
    "speechrecognition_silence_threshold": 0.04,  # Seuil d'énergie pour détecter le silence (SpeechRecognition)
    "whisper_silence_threshold": 0.04,  # Seuil d'énergie pour détecter le silence (Whisper)
    "whisper_silence_chunks": 15,  # Nombre de chunks silencieux pour terminer l'enregistrement (Whisper)
    "vosk_silence_threshold": 0.04,  # Seuil d'énergie pour détecter le silence (Vosk)
    "vosk_silence_chunks": 15,  # Nombre de chunks silencieux pour terminer l'enregistrement (Vosk)
    "whisper_ct2_silence_threshold": 0.04,  # Seuil d'énergie pour détecter le silence (Whisper CT2)
    "whisper_ct2_silence_chunks": 4  # Nombre de chunks silencieux pour terminer l'enregistrement (Whisper CT2)
}

# Variables globales pour les paramètres de reconnaissance vocale
stt_settings = DEFAULT_STT_SETTINGS.copy()

def load_stt_settings():
    """Charge les paramètres de reconnaissance vocale depuis la base de données"""
    global stt_settings
    
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import load_stt_settings
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import load_stt_settings
        
        # Charger les paramètres depuis la base de données
        loaded_settings = load_stt_settings(DEFAULT_STT_SETTINGS)
        
        # Convertir les valeurs chargées au type attendu
        for key, value in loaded_settings.items():
            if key in DEFAULT_STT_SETTINGS:
                expected_type = type(DEFAULT_STT_SETTINGS[key])
                if expected_type == float:
                    loaded_settings[key] = float(value)
                elif expected_type == int:
                    loaded_settings[key] = int(value)
                elif expected_type == bool:
                    if isinstance(value, str):
                        loaded_settings[key] = value.lower() in ('true', 'yes', '1', 'oui')
                    else:
                        loaded_settings[key] = bool(value)
        
        # Mettre à jour les paramètres globaux
        stt_settings.update(loaded_settings)
        
        print(f"Paramètres STT chargés: {stt_settings}")
        return True
    except Exception as e:
        print(f"Erreur lors du chargement des paramètres STT: {e}")
        return False

def save_stt_settings():
    """Sauvegarde les paramètres de reconnaissance vocale dans la base de données"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import save_stt_settings
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import save_stt_settings
        
        # Sauvegarder les paramètres dans la base de données
        success = save_stt_settings(stt_settings)
        
        if success:
            print("Paramètres STT sauvegardés avec succès")
        else:
            print("Échec de la sauvegarde des paramètres STT")
        
        return success
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des paramètres STT: {e}")
        return False

def update_stt_setting(key, value):
    """
    Met à jour un paramètre de reconnaissance vocale
    
    Args:
        key: Nom du paramètre
        value: Nouvelle valeur
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    global stt_settings
    
    try:
        # Convertir la valeur au type approprié
        if key in DEFAULT_STT_SETTINGS:
            # Déterminer le type attendu
            expected_type = type(DEFAULT_STT_SETTINGS[key])
            
            # Convertir la valeur au type attendu
            if expected_type == float:
                value = float(value)
            elif expected_type == int:
                value = int(value)
            elif expected_type == bool:
                if isinstance(value, str):
                    value = value.lower() in ('true', 'yes', '1', 'oui')
                else:
                    value = bool(value)
        
        # Mettre à jour le paramètre
        stt_settings[key] = value
        
        # Sauvegarder les paramètres
        save_stt_settings()
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du paramètre STT '{key}': {e}")
        return False

def get_stt_settings():
    """
    Récupère les paramètres de reconnaissance vocale actuels
    
    Returns:
        dict: Dictionnaire des paramètres
    """
    return stt_settings.copy()

# Charger les paramètres au démarrage
load_stt_settings()


# File d'attente pour le traitement audio en arrière-plan
audio_queue = queue.Queue()

# Liste des threads actifs pour pouvoir les arrêter proprement
active_threads = []




# Constantes pour Whisper API
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"
WHISPER_SAMPLE_RATE = 16000
WHISPER_CHUNK_SIZE = 512  # Réduit pour un traitement plus rapide
WHISPER_SILENCE_THRESHOLD = 0.04  # Seuil d'énergie pour détecter le silence
WHISPER_SILENCE_CHUNKS = 15  # Réduit pour une détection plus rapide de fin de phrase
WHISPER_MIN_SPEAKING_CHUNKS = 3  # Réduit pour capturer des commandes plus courtes
WHISPER_MIN_AUDIO_ENERGY = 0.04  # Seuil d'énergie minimum pour l'audio
WHISPER_MIN_AUDIO_DURATION = 0.2  # Réduit pour capturer des commandes plus courtes
WHISPER_MAX_AUDIO_DURATION = 5.0  # Réduit pour un traitement plus rapide
WHISPER_COST_PER_MINUTE = 0.006  # $0.006 par minute d'audio
WHISPER_PARALLEL_REQUESTS = True  # Activer le traitement parallèle
WHISPER_CACHE_SIZE = 10  # Nombre d'entrées de cache pour éviter de retraiter des audios similaires

# Constantes pour Vosk
VOSK_SAMPLE_RATE = 16000
VOSK_CHUNK_SIZE = 4096  # Taille optimale pour Vosk
VOSK_SILENCE_THRESHOLD = 0.04  # Seuil d'énergie pour détecter le silence
VOSK_SILENCE_CHUNKS = 15
VOSK_MIN_SPEAKING_CHUNKS = 3
VOSK_MIN_AUDIO_ENERGY = 0.04  # Seuil d'énergie minimum pour l'audio
VOSK_MIN_AUDIO_DURATION = 0.2
VOSK_MAX_AUDIO_DURATION = 10.0
VOSK_MODEL_PATH = os.path.join(os.path.expanduser("~"), ".cache", "vosk", "vosk-model-fr-0.22")

# Constantes pour Whisper CT2
WHISPER_CT2_SAMPLE_RATE = 16000
WHISPER_CT2_CHUNK_SIZE = 2048  # Réduit pour une détection plus rapide
WHISPER_CT2_SILENCE_THRESHOLD = 0.04  # Seuil d'énergie pour détecter le silence
WHISPER_CT2_SILENCE_CHUNKS = 4  # Réduit pour terminer l'enregistrement beaucoup plus rapidement
WHISPER_CT2_MIN_SPEAKING_CHUNKS = 2  # Réduit pour détecter des commandes plus courtes
WHISPER_CT2_MIN_AUDIO_ENERGY = 0.04  # Seuil d'énergie minimum pour l'audio
WHISPER_CT2_MIN_AUDIO_DURATION = 0.1  # Réduit pour accepter des commandes plus courtes
WHISPER_CT2_MAX_AUDIO_DURATION = 3.0  # Réduit pour les commandes courtes
WHISPER_CT2_DICTATION_MAX_DURATION = 30.0  # Séparé pour le mode dictée
WHISPER_CT2_MODEL_SIZE = "large"  # Options: tiny, base, small, medium, large
WHISPER_CT2_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "whisper-ct2")
WHISPER_CT2_COMPUTE_TYPE = "float16"  # Options: float32, float16, int8
WHISPER_CT2_LANGUAGE = "fr"  # Langue française
WHISPER_CT2_DEFAULT_DEVICE = "auto"  # Utiliser auto (GPU si disponible) par défaut
WHISPER_CT2_USE_CUDA = True  # Par défaut, essayer d'utiliser CUDA
WHISPER_CT2_FORCE_CPU = False  # Option pour forcer l'utilisation du CPU si nécessaire

# Constantes pour Whisper French
WHISPER_FRENCH_SAMPLE_RATE = 16000
WHISPER_FRENCH_CHUNK_SIZE = 2048  # Taille de chunk optimisée pour le modèle français
WHISPER_FRENCH_SILENCE_THRESHOLD = 0.04  # Seuil d'énergie pour détecter le silence
WHISPER_FRENCH_SILENCE_CHUNKS = 4  # Nombre de chunks silencieux pour terminer l'enregistrement
WHISPER_FRENCH_MIN_SPEAKING_CHUNKS = 2  # Nombre minimum de chunks pour considérer une commande valide
WHISPER_FRENCH_MIN_AUDIO_ENERGY = 0.04  # Seuil d'énergie minimum pour l'audio
WHISPER_FRENCH_MIN_AUDIO_DURATION = 0.1  # Durée minimale pour un audio valide
WHISPER_FRENCH_MAX_AUDIO_DURATION = 3.0  # Durée maximale pour les commandes courtes
WHISPER_FRENCH_DICTATION_MAX_DURATION = 30.0  # Durée maximale en mode dictée
WHISPER_FRENCH_MODEL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "whisper-french")
WHISPER_FRENCH_MODEL_ID = "bofenghuang/whisper-large-v3-french-distil-dec16"
WHISPER_FRENCH_COMPUTE_TYPE = "float16"  # Options: float32, float16, int8
WHISPER_FRENCH_DEFAULT_DEVICE = "auto"  # Utiliser auto (GPU si disponible) par défaut
WHISPER_FRENCH_USE_CUDA = True  # Par défaut, essayer d'utiliser CUDA
WHISPER_FRENCH_FORCE_CPU = False  # Option pour forcer l'utilisation du CPU


# Variable globale pour stocker le modèle Vosk
vosk_model = None
vosk_thread = None
vosk_running = False

# Sherpa NCNN a été retiré

# Variable globale pour stocker le modèle Whisper CT2
whisper_ct2_model = None
whisper_ct2_thread = None
whisper_ct2_running = False

# Variables globales pour stocker le modèle Whisper French
whisper_french_model = None
whisper_french_thread = None
whisper_french_running = False

import ctypes

def is_cuda_available():
    """Vérifie si CUDA est disponible et fonctionnel"""
    try:
        # 0. Vérifier d'abord les packages pip NVIDIA
        try:
            # Tester si les DLLs sont accessibles directement (après configuration des chemins)
            dll_found = False
            for dll_name in ["cudart64_12.dll", "cudnn64_9.dll"]:
                try:
                    ctypes.CDLL(dll_name)
                    print(f"DLL {dll_name} accessible directement (packages pip)")
                    dll_found = True
                except Exception as e:
                    print(f"DLL {dll_name} non accessible: {e}")
            
            if dll_found:
                print("CUDA disponible via packages pip")
                return True
        except Exception as e:
            print(f"Erreur lors de la vérification des DLLs pip: {e}")
        
        # 1. Vérifier avec nvidia-smi d'abord (méthode la plus fiable)
        try:
            import subprocess
            process = subprocess.Popen(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                print("GPU NVIDIA détecté via nvidia-smi")
                # Extraire les informations du GPU
                output = stdout.decode('utf-8', errors='ignore')
                print(f"Détails du GPU:\n{output.split('|')[0]}")
                return True
        except Exception as e:
            print(f"nvidia-smi non disponible: {e}")
            
        # 2. Essayer ensuite le correcteur de chemin CUDA pour résoudre les problèmes de DLL
        try:
            print("Tentative de correction des chemins CUDA...")
            # Importer l'utilitaire cuda_path_fixer
            try:
                from whisp_assistant.cuda_path_fixer import fix_cuda_paths, verify_cudnn_availability, get_cuda_installation_info
            except ImportError:
                from cuda_path_fixer import fix_cuda_paths, verify_cudnn_availability, get_cuda_installation_info
            
            # Obtenir des informations détaillées sur CUDA
            cuda_info = get_cuda_installation_info()
            if cuda_info["cuda_found"]:
                print(f"CUDA {cuda_info['cuda_version']} trouvé dans {cuda_info['cuda_path']}")
                
                # Si CUDA est disponible, considérer que le GPU est disponible
                if cuda_info["cuda_found"]:
                    return True
                    
            # Essayer de corriger les chemins CUDA
            success, message = fix_cuda_paths()
            print(message)
            
            # Vérifier si cuDNN est disponible après la correction
            if verify_cudnn_availability():
                print("cuDNN est maintenant disponible grâce à la correction des chemins")
                return True
        except Exception as e:
            print(f"Erreur lors de la tentative de correction des chemins CUDA: {e}")
            # Continuer avec les autres méthodes de détection
        
        # 2. Tester avec GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                print(f"GPU détecté via GPUtil: {gpus[0].name}")
                # Si GPUtil trouve un GPU, on vérifie quand même les DLLs
                return True
        except (ImportError, Exception) as e:
            print(f"Impossible de vérifier GPU via GPUtil: {e}")
            pass
        
        # 3. Vérifier via torch
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                print(f"CUDA disponible selon torch: {cuda_available}")
                if torch.cuda.device_count() > 0:
                    print(f"GPU détecté: {torch.cuda.get_device_name(0)}")
                return True
        except (ImportError, AttributeError) as e:
            print(f"Impossible de vérifier CUDA via torch: {e}")
            pass
            
        # 4. Vérifier manuellement les DLLs cuDNN et CUDA
        import ctypes
        import os
        
        # Lister les chemins du PATH pour le débogage
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        print(f"Nombre de répertoires dans PATH: {len(path_dirs)}")
        
        # Chercher d'abord la DLL cudnn_ops
        cudnn_ops_found = False
        for version in ["9", "8", "8.9", "8.6", "8.4", "8.2", "8.0", "7"]:
            try:
                dll_path = f"cudnn_ops64_{version}.dll"
                print(f"Tentative de chargement de {dll_path}...")
                ctypes.CDLL(dll_path)
                print(f"{dll_path} chargé avec succès")
                cudnn_ops_found = True
                break
            except OSError as e:
                print(f"Impossible de charger {dll_path}: {e}")
        
        # Chercher ensuite la DLL cudnn principale
        cudnn_found = False
        for version in ["9", "8", "8.9", "8.6", "8.4", "8.2", "8.0", "7"]:
            try:
                dll_path = f"cudnn64_{version}.dll"
                print(f"Tentative de chargement de {dll_path}...")
                ctypes.CDLL(dll_path)
                print(f"{dll_path} chargé avec succès")
                cudnn_found = True
                break
            except OSError:
                continue
        
        # Chercher la DLL cudart
        cudart_found = False
        for version in ["12", "118", "117", "116", "115", "114", "113", "112", "111", "110", "102", "101", "100"]:
            try:
                dll_path = f"cudart64_{version}.dll"
                print(f"Tentative de chargement de {dll_path}...")
                ctypes.CDLL(dll_path)
                print(f"{dll_path} chargé avec succès")
                cudart_found = True
                break
            except OSError:
                continue
        
        # Si au moins une des DLLs principales est trouvée, considérer que CUDA est disponible
        if cudnn_found or cudnn_ops_found or cudart_found:
            print("DLLs CUDA détectées, mais certaines peuvent manquer")
            return cudart_found  # Retourner True seulement si cudart est trouvé (composant de base)
            
        print("Aucune DLL CUDA principale détectée")
        return False
    except Exception as e:
        print(f"Erreur lors de la vérification de CUDA: {e}")
        return False

def setup_whisper_french_model():
    """Charge le modèle Whisper French optimisé pour le français"""
    global whisper_french_model, WHISPER_FRENCH_USE_CUDA
    
    # Charger le modèle Whisper French s'il n'est pas déjà chargé
    if whisper_french_model is None:
        print("Chargement du modèle Whisper French...")
        
        # Vérifier si Whisper CT2 est disponible ou tenter de l'importer à nouveau
        if not WHISPER_CT2_AVAILABLE and not import_whisper_ct2():
            error_msg = "La bibliothèque faster-whisper n'est pas disponible, impossible de charger le modèle French"
            print(error_msg)
            print("Installation requise: pip install ctranslate2 faster-whisper huggingface_hub")
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
                log_to_web("Pour installer: pip install ctranslate2 faster-whisper huggingface_hub", "info")
            return False
        
        try:
            # Créer le répertoire du modèle si nécessaire
            os.makedirs(WHISPER_FRENCH_MODEL_DIR, exist_ok=True)
            
            # Afficher un message pour l'utilisateur
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(f"Chargement du modèle Whisper French optimisé... Cela peut prendre un moment lors de la première utilisation.", "info")
            
            # Vérifier si le modèle est déjà téléchargé
            model_dir = os.path.join(WHISPER_FRENCH_MODEL_DIR, "ctranslate2")
            if not os.path.exists(model_dir):
                print(f"Modèle French non trouvé localement, téléchargement depuis Hugging Face...")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("Téléchargement du modèle depuis Hugging Face (peut prendre plusieurs minutes)...", "info")
                
                try:
                    # Importer huggingface_hub pour télécharger le modèle
                    try:
                        from huggingface_hub import snapshot_download
                    except ImportError:
                        print("Installation de huggingface_hub...")
                        import subprocess
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
                        from huggingface_hub import snapshot_download
                    
                    # Télécharger le modèle
                    snapshot_download(
                        repo_id=WHISPER_FRENCH_MODEL_ID,
                        local_dir=WHISPER_FRENCH_MODEL_DIR,
                        allow_patterns='ctranslate2/*'
                    )
                    print(f"Modèle téléchargé avec succès dans {WHISPER_FRENCH_MODEL_DIR}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web("Modèle téléchargé avec succès!", "info")
                except Exception as e:
                    error_msg = f"Erreur lors du téléchargement du modèle: {e}"
                    print(error_msg)
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(error_msg, "error")
                    return False
            
            # Vérifier et corriger les chemins CUDA si nécessaire
            try:
                # Importer l'utilitaire cuda_path_fixer
                try:
                    from whisp_assistant.cuda_path_fixer import fix_cuda_paths, get_cuda_installation_info
                except ImportError:
                    from cuda_path_fixer import fix_cuda_paths, get_cuda_installation_info
                
                # Essayer de corriger les chemins CUDA avant de vérifier la disponibilité
                success, message = fix_cuda_paths()
                if success:
                    print(f"Correction des chemins CUDA réussie: {message}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"Correction des chemins CUDA réussie: {message}", "info")
                else:
                    print(f"Problème avec CUDA: {message}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"Problème avec CUDA: {message}", "warning")
            except Exception as e:
                print(f"Erreur lors de la vérification/correction des chemins CUDA: {e}")
            
            # Vérifier si CUDA est disponible après nos tentatives de correction
            WHISPER_FRENCH_USE_CUDA = is_cuda_available()
            
            # Déterminer le périphérique à utiliser
            device = "auto"  # Par défaut, utiliser auto pour le meilleur périphérique
            
            # Respecter l'option de forçage du CPU si elle est activée
            if WHISPER_FRENCH_FORCE_CPU:
                device = "cpu"
                print("Forçage de l'utilisation du CPU activé pour Whisper French")
            elif not WHISPER_FRENCH_USE_CUDA:
                device = "cpu"
                print("CUDA non disponible, utilisation du CPU pour Whisper French")
            else:
                print(f"CUDA disponible, utilisation du périphérique: {device} pour Whisper French")
                
            print(f"Utilisation du périphérique pour Whisper French: {device}")
            
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                status = "disponible et utilisé" if WHISPER_FRENCH_USE_CUDA and device != "cpu" else \
                         "disponible mais non utilisé" if WHISPER_FRENCH_USE_CUDA and device == "cpu" else \
                         "non disponible"
                log_to_web(f"Utilisation du périphérique pour Whisper French: {device} (CUDA {status})", "info")
            
            # Charger le modèle
            try:
                # Adapter le compute_type en fonction du périphérique
                compute_type = WHISPER_FRENCH_COMPUTE_TYPE if device != "cpu" else "float32"
                print(f"Utilisation du compute_type: {compute_type} pour le device: {device}")
                
                # Charger le modèle
                model_path = os.path.join(WHISPER_FRENCH_MODEL_DIR, "ctranslate2")
                whisper_french_model = WhisperModel(
                    model_size_or_path=model_path,
                    device=device,
                    compute_type=compute_type,
                    cpu_threads=8 if device == "cpu" else 4
                )
                
                print(f"Modèle Whisper French chargé avec succès sur {device}")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(f"Modèle Whisper French chargé avec succès sur {device}", "info")
                return True
            except Exception as e:
                error_msg = f"Erreur lors du chargement du modèle Whisper French sur {device}: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                
                # Si l'erreur est liée à CUDA, essayer avec CPU
                if device != "cpu" and ("cuda" in str(e).lower() or "cudnn" in str(e).lower()):
                    print("Erreur liée à CUDA détectée, nouvelle tentative avec CPU uniquement")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web("Erreur liée à CUDA détectée, nouvelle tentative avec CPU uniquement", "warning")
                    
                    try:
                        # Nouvelle tentative avec CPU seulement et float32
                        model_path = os.path.join(WHISPER_FRENCH_MODEL_DIR, "ctranslate2")
                        whisper_french_model = WhisperModel(
                            model_size_or_path=model_path,
                            device="cpu",
                            compute_type="float32",
                            cpu_threads=8
                        )
                        
                        print(f"Modèle Whisper French chargé avec succès sur CPU (fallback)")
                        if 'web_interface' in sys.modules:
                            from web_interface import log_to_web
                            log_to_web(f"Modèle Whisper French chargé avec succès sur CPU (fallback)", "info")
                        
                        # Mise à jour de l'état CUDA
                        WHISPER_FRENCH_USE_CUDA = False
                        return True
                    except Exception as e2:
                        error_msg = f"Échec également avec CPU: {e2}"
                        print(error_msg)
                        if 'web_interface' in sys.modules:
                            from web_interface import log_to_web
                            log_to_web(error_msg, "error")
                        whisper_french_model = None
                        return False
                else:
                    whisper_french_model = None
                    return False
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de Whisper French: {e}"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            whisper_french_model = None
            return False
    else:
        print("Modèle Whisper French déjà chargé")
        return True

def setup_whisper_ct2_model():
    """Charge le modèle Whisper CT2"""
    global whisper_ct2_model, WHISPER_CT2_USE_CUDA
    
    # Charger le modèle Whisper CT2 si ce n'est pas déjà fait
    if whisper_ct2_model is None:
        print("Chargement du modèle Whisper CT2...")
        
        # Vérifier si Whisper CT2 est disponible ou tenter de l'importer à nouveau
        if not WHISPER_CT2_AVAILABLE and not import_whisper_ct2():
            error_msg = "Whisper CT2 n'est pas disponible, impossible de charger le modèle"
            print(error_msg)
            print("Installation requise: pip install ctranslate2 faster-whisper")
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
                log_to_web("Pour installer: pip install ctranslate2 faster-whisper", "info")
            return False
        
        try:
            # Créer le répertoire du modèle si nécessaire
            os.makedirs(WHISPER_CT2_MODEL_DIR, exist_ok=True)
            
            # Afficher un message pour l'utilisateur
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(f"Chargement du modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE})... Cela peut prendre un moment lors de la première utilisation.", "info")
            
            # Vérifier et corriger les chemins CUDA si nécessaire
            try:
                # Importer l'utilitaire cuda_path_fixer
                try:
                    from whisp_assistant.cuda_path_fixer import fix_cuda_paths, get_cuda_installation_info
                except ImportError:
                    from cuda_path_fixer import fix_cuda_paths, get_cuda_installation_info
                
                # Essayer de corriger les chemins CUDA avant de vérifier la disponibilité
                success, message = fix_cuda_paths()
                if success:
                    print(f"Correction des chemins CUDA réussie: {message}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"Correction des chemins CUDA réussie: {message}", "info")
                else:
                    print(f"Problème avec CUDA: {message}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"Problème avec CUDA: {message}", "warning")
                
                # Obtenir des informations détaillées sur l'installation CUDA
                cuda_info = get_cuda_installation_info()
                if cuda_info["cuda_found"] and cuda_info["cudnn_found"]:
                    print(f"CUDA {cuda_info['cuda_version']} et cuDNN {cuda_info['cudnn_version']} détectés")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"CUDA {cuda_info['cuda_version']} et cuDNN {cuda_info['cudnn_version']} détectés", "info")
                
                # Afficher les DLLs manquantes pour aider au diagnostic
                if cuda_info["missing_dlls"]:
                    missing_dlls_str = ", ".join(cuda_info["missing_dlls"][:5])  # Limiter l'affichage
                    print(f"DLLs manquantes: {missing_dlls_str}")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"DLLs manquantes: {missing_dlls_str}", "warning")
            except Exception as e:
                print(f"Erreur lors de la vérification/correction des chemins CUDA: {e}")
            
            # Vérifier si CUDA est disponible après nos tentatives de correction
            WHISPER_CT2_USE_CUDA = is_cuda_available()
            
            # Déterminer le périphérique à utiliser (auto, cuda, cpu)
            device = "auto"  # Par défaut, utiliser auto pour que la bibliothèque choisisse le meilleur périphérique
            
            # Respecter l'option de forçage du CPU si elle est activée
            if WHISPER_CT2_FORCE_CPU:
                device = "cpu"
                print("Forçage de l'utilisation du CPU activé")
            elif not WHISPER_CT2_USE_CUDA:
                device = "cpu"
                print("CUDA non disponible, utilisation du CPU")
            else:
                print(f"CUDA disponible, utilisation du périphérique: {device}")
                
            print(f"Utilisation du périphérique pour Whisper CT2: {device}")
            
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                status = "disponible et utilisé" if WHISPER_CT2_USE_CUDA and device != "cpu" else \
                         "disponible mais non utilisé" if WHISPER_CT2_USE_CUDA and device == "cpu" else \
                         "non disponible"
                log_to_web(f"Utilisation du périphérique pour Whisper CT2: {device} (CUDA {status})", "info")
            
            # Charger le modèle
            try:
                # Le modèle sera téléchargé automatiquement s'il n'existe pas déjà
                # Adapter le compute_type en fonction du périphérique
                compute_type = WHISPER_CT2_COMPUTE_TYPE if device != "cpu" else "float32"
                print(f"Utilisation du compute_type: {compute_type} pour le device: {device}")
                
                whisper_ct2_model = WhisperModel(
                    model_size_or_path=WHISPER_CT2_MODEL_SIZE,
                    device=device,  # Utiliser le périphérique déterminé
                    compute_type=compute_type,  # Adapter selon le périphérique
                    download_root=WHISPER_CT2_MODEL_DIR,
                    local_files_only=False,  # Permet le téléchargement si nécessaire
                    cpu_threads=8 if device == "cpu" else 4  # Plus de threads si CPU
                )
                
                print(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur {device}")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur {device}", "info")
                return True
            except Exception as e:
                error_msg = f"Erreur lors du chargement du modèle Whisper CT2 sur {device}: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                
                # Si l'erreur est liée à CUDA et que nous n'utilisions pas déjà le CPU, analyser l'erreur
                if device != "cpu" and ("cuda" in str(e).lower() or "cudnn" in str(e).lower()):
                    error_msg = str(e).lower()
                    
                    # Vérifier s'il s'agit spécifiquement d'une erreur cudnn_ops64_9.dll manquante
                    if "cudnn_ops64_9.dll" in error_msg or "cudnn64_" in error_msg:
                        print("Erreur liée à cuDNN détectée, tentative avec CUDA sans cuDNN...")
                        
                        if 'web_interface' in sys.modules:
                            from web_interface import log_to_web
                            log_to_web("Erreur liée à cuDNN détectée, tentative avec CUDA sans cuDNN...", "warning")
                        
                        try:
                            # Essayer avec CUDA mais float32 au lieu de float16
                            device = "cuda"  # Forcer CUDA explicitement
                            whisper_ct2_model = WhisperModel(
                                model_size_or_path=WHISPER_CT2_MODEL_SIZE,
                                device=device,
                                compute_type="float32",  # Utiliser float32 pour éviter les problèmes cuDNN
                                download_root=WHISPER_CT2_MODEL_DIR,
                                local_files_only=False,
                                cpu_threads=4
                            )
                            
                            print(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur {device} avec float32")
                            if 'web_interface' in sys.modules:
                                from web_interface import log_to_web
                                log_to_web(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur {device} avec float32", "info")
                            
                            return True
                        except Exception as cuda_error:
                            print(f"Échec avec CUDA sans cuDNN: {cuda_error}")
                            # Réessayer avec CPU en cas d'échec
                    
                    print("Erreur liée à CUDA détectée, nouvelle tentative avec CPU uniquement")
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web("Erreur liée à CUDA détectée, nouvelle tentative avec CPU uniquement", "warning")
                    
                    try:
                        # Nouvelle tentative avec CPU seulement et float32
                        whisper_ct2_model = WhisperModel(
                            model_size_or_path=WHISPER_CT2_MODEL_SIZE,
                            device="cpu",  # Forcer CPU
                            compute_type="float32",  # Utiliser float32 pour CPU
                            download_root=WHISPER_CT2_MODEL_DIR,
                            local_files_only=False,
                            cpu_threads=8  # Plus de threads pour compenser le CPU
                        )
                        
                        print(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur CPU (fallback)")
                        if 'web_interface' in sys.modules:
                            from web_interface import log_to_web
                            log_to_web(f"Modèle Whisper CT2 ({WHISPER_CT2_MODEL_SIZE}) chargé avec succès sur CPU (fallback)", "info")
                        
                        # Mise à jour de l'état CUDA
                        WHISPER_CT2_USE_CUDA = False
                        return True
                    except Exception as e2:
                        error_msg = f"Échec également avec CPU: {e2}"
                        print(error_msg)
                        if 'web_interface' in sys.modules:
                            from web_interface import log_to_web
                            log_to_web(error_msg, "error")
                        whisper_ct2_model = None
                        return False
                else:
                    whisper_ct2_model = None
                    return False
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de Whisper CT2: {e}"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            whisper_ct2_model = None
            return False
    else:
        print("Modèle Whisper CT2 déjà chargé")
        return True


def setup_vosk_model():
    """Charge le modèle Vosk"""
    global vosk_model
    
    # Charger le modèle Vosk si ce n'est pas déjà fait
    if vosk_model is None:
        print("Chargement du modèle Vosk...")
        
        # Vérifier si Vosk est disponible ou tenter de l'importer à nouveau
        if not VOSK_AVAILABLE and not import_vosk():
            error_msg = "Vosk n'est pas disponible, impossible de charger le modèle"
            print(error_msg)
            print("Installation requise: pip install vosk")
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
                log_to_web("Pour installer: pip install vosk", "info")
            return False
        try:
            # Vérifier si le modèle est déjà téléchargé
            if not os.path.exists(VOSK_MODEL_PATH):
                print(f"Modèle Vosk non trouvé à {VOSK_MODEL_PATH}")
                print("Tentative de téléchargement automatique du modèle français...")
                
                # Créer le répertoire si nécessaire
                os.makedirs(os.path.dirname(VOSK_MODEL_PATH), exist_ok=True)
                
                # Téléchargement automatique
                import urllib.request
                import zipfile
                
                model_url = "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"
                zip_path = os.path.join(os.path.dirname(VOSK_MODEL_PATH), "vosk-model-fr-0.22.zip")
                
                try:
                    print(f"Téléchargement depuis {model_url}...")
                    # Afficher un message pour l'utilisateur
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(f"Téléchargement du modèle Vosk en cours... Cela peut prendre quelques minutes.", "info")
                    
                    urllib.request.urlretrieve(model_url, zip_path)
                    
                    print(f"Extraction vers {os.path.dirname(VOSK_MODEL_PATH)}...")
                    if 'web_interface' in sys.modules:
                        log_to_web("Extraction du modèle Vosk...", "info")
                    
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(os.path.dirname(VOSK_MODEL_PATH))
                    
                    print("Modèle téléchargé et extrait avec succès")
                    if 'web_interface' in sys.modules:
                        log_to_web("Modèle Vosk téléchargé et installé avec succès!", "info")
                    
                    os.remove(zip_path)
                except Exception as e:
                    error_msg = f"Erreur lors du téléchargement automatique: {e}"
                    print(error_msg)
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(error_msg, "error")
                    return False
            
            # Charger le modèle
            try:
                vosk_model = Model(VOSK_MODEL_PATH)
                print(f"Modèle Vosk chargé depuis {VOSK_MODEL_PATH}")
                return True
            except Exception as e:
                error_msg = f"Erreur lors du chargement du modèle Vosk: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                vosk_model = None
                return False
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation de Vosk: {e}"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            vosk_model = None
            return False
    else:
        print("Modèle Vosk déjà chargé")
        return True

def setup_whisper_french_recognition():
    """Configure et initialise le système de reconnaissance vocale avec Whisper French"""
    global whisper_french_model
    
    print("Configuration du système de reconnaissance Whisper French...")
    
    # Initialisation du recognizer (pour compatibilité)
    recognizer = sr.Recognizer()
    
    try:
        # Vérifier si Whisper CT2 est disponible (car on utilise la même bibliothèque)
        if not WHISPER_CT2_AVAILABLE:
            error_msg = "La bibliothèque faster-whisper n'est pas disponible, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
        
        # Vérifier si le modèle est déjà chargé
        if whisper_french_model is None:
            print("Modèle Whisper French non chargé, tentative de chargement...")
            if not setup_whisper_french_model():
                error_msg = "Échec du chargement du modèle Whisper French, utilisation de SpeechRecognition comme solution de repli"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                set_stt_engine("speechrecognition")
                return setup_speechrecognition()
            
        # Initialisation du microphone avec le taux d'échantillonnage approprié
        try:
            microphone = sr.Microphone(sample_rate=WHISPER_FRENCH_SAMPLE_RATE)
            print(f"Microphone configuré avec sample_rate={WHISPER_FRENCH_SAMPLE_RATE}")
        except Exception as mic_error:
            print(f"Erreur lors de l'initialisation du microphone avec sample_rate={WHISPER_FRENCH_SAMPLE_RATE}: {mic_error}")
            try:
                # Essayer sans spécifier le taux d'échantillonnage
                microphone = sr.Microphone()
                print("Utilisation du microphone par défaut sans sample_rate spécifié")
            except Exception as e:
                error_msg = f"Erreur critique lors de l'initialisation du microphone: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                set_stt_engine("speechrecognition")
                return setup_speechrecognition()
        
        # Placeholder pour la fonction d'arrêt (sera définie plus tard)
        stop_listening = None
        
        print("Système de reconnaissance Whisper French prêt!")
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web("Système de reconnaissance Whisper French prêt!", "info")
        return recognizer, microphone, stop_listening
    except Exception as e:
        error_msg = f"Erreur lors de l'initialisation de Whisper French: {e}"
        print(error_msg)
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(error_msg, "error")
        set_stt_engine("speechrecognition")
        return setup_speechrecognition()

def setup_whisper_ct2_recognition():
    """Configure et initialise le système de reconnaissance vocale avec Whisper CT2"""
    global whisper_ct2_model
    
    print("Configuration du système de reconnaissance Whisper CT2...")
    
    # Initialisation du recognizer (pour compatibilité)
    recognizer = sr.Recognizer()
    
    try:
        # Vérifier si Whisper CT2 est disponible
        if not WHISPER_CT2_AVAILABLE:
            error_msg = "Whisper CT2 n'est pas disponible, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
        
        # Vérifier si le modèle est déjà chargé
        if whisper_ct2_model is None:
            print("Modèle Whisper CT2 non chargé, tentative de chargement...")
            if not setup_whisper_ct2_model():
                error_msg = "Échec du chargement du modèle Whisper CT2, utilisation de SpeechRecognition comme solution de repli"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                set_stt_engine("speechrecognition")
                return setup_speechrecognition()
            
        # Initialisation du microphone avec le taux d'échantillonnage approprié
        try:
            microphone = sr.Microphone(sample_rate=WHISPER_CT2_SAMPLE_RATE)
            print(f"Microphone configuré avec sample_rate={WHISPER_CT2_SAMPLE_RATE}")
        except Exception as mic_error:
            print(f"Erreur lors de l'initialisation du microphone avec sample_rate={WHISPER_CT2_SAMPLE_RATE}: {mic_error}")
            try:
                # Essayer sans spécifier le taux d'échantillonnage
                microphone = sr.Microphone()
                print("Utilisation du microphone par défaut sans sample_rate spécifié")
            except Exception as e:
                error_msg = f"Erreur critique lors de l'initialisation du microphone: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                set_stt_engine("speechrecognition")
                return setup_speechrecognition()
        
        # Charger le modèle Whisper CT2
        if not setup_whisper_ct2_model():
            error_msg = "Échec du chargement du modèle Whisper CT2, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
        
        # Placeholder pour la fonction d'arrêt (sera définie plus tard)
        stop_listening = None
        
        print("Système de reconnaissance Whisper CT2 prêt!")
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web("Système de reconnaissance Whisper CT2 prêt!", "info")
        return recognizer, microphone, stop_listening
    except Exception as e:
        error_msg = f"Erreur lors de l'initialisation de Whisper CT2: {e}"
        print(error_msg)
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(error_msg, "error")
        set_stt_engine("speechrecognition")
        return setup_speechrecognition()


def setup_vosk_recognition():
    """Configure et initialise le système de reconnaissance vocale avec Vosk"""
    global vosk_model
    
    print("Configuration du système de reconnaissance Vosk...")
    
    # Initialisation du recognizer (pour compatibilité)
    recognizer = sr.Recognizer()
    
    try:
        # Vérifier si Vosk est disponible
        if not VOSK_AVAILABLE:
            error_msg = "Vosk n'est pas disponible, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
            
        # Initialisation du microphone avec le taux d'échantillonnage approprié
        try:
            microphone = sr.Microphone(sample_rate=VOSK_SAMPLE_RATE)
            print(f"Microphone configuré avec sample_rate={VOSK_SAMPLE_RATE}")
        except Exception as mic_error:
            print(f"Erreur lors de l'initialisation du microphone avec sample_rate={VOSK_SAMPLE_RATE}: {mic_error}")
            try:
                # Essayer sans spécifier le taux d'échantillonnage
                microphone = sr.Microphone()
                print("Utilisation du microphone par défaut sans sample_rate spécifié")
            except Exception as e:
                error_msg = f"Erreur critique lors de l'initialisation du microphone: {e}"
                print(error_msg)
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web(error_msg, "error")
                set_stt_engine("speechrecognition")
                return setup_speechrecognition()
        
        # Charger le modèle Vosk
        if not setup_vosk_model():
            error_msg = "Échec du chargement du modèle Vosk, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
        
        # Placeholder pour la fonction d'arrêt (sera définie plus tard)
        stop_listening = None
        
        print("Système de reconnaissance Vosk prêt!")
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web("Système de reconnaissance Vosk prêt!", "info")
        return recognizer, microphone, stop_listening
    except Exception as e:
        error_msg = f"Erreur lors de l'initialisation de Vosk: {e}"
        print(error_msg)
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(error_msg, "error")
        set_stt_engine("speechrecognition")
        return setup_speechrecognition()

# Cache pour les requêtes Whisper
class WhisperCache:
    def __init__(self, max_size=WHISPER_CACHE_SIZE):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get_hash(self, audio_data):
        """Génère un hash pour les données audio"""
        # Utiliser un sous-échantillonnage pour accélérer le hachage
        if len(audio_data) > 16000:  # Si plus d'une seconde
            # Prendre des échantillons à intervalles réguliers
            step = len(audio_data) // 16000
            samples = audio_data[::step][:16000]
        else:
            samples = audio_data
        
        # Calculer le hash
        return hashlib.md5(samples).hexdigest()
    
    def get(self, audio_data):
        """Récupère un résultat du cache s'il existe"""
        audio_hash = self.get_hash(audio_data)
        if audio_hash in self.cache:
            # Déplacer l'élément à la fin (le plus récemment utilisé)
            self.cache.move_to_end(audio_hash)
            return self.cache[audio_hash]
        return None
    
    def set(self, audio_data, result):
        """Ajoute un résultat au cache"""
        audio_hash = self.get_hash(audio_data)
        
        # Si le cache est plein, supprimer l'élément le plus ancien
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        # Ajouter le nouvel élément
        self.cache[audio_hash] = result

# Initialiser le cache
whisper_cache = WhisperCache()

# Métriques de performance STT
stt_metrics = {
    "speechrecognition": {
        "requests": 0,
        "success": 0,
        "errors": 0,
        "latencies": [],
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "last_latency": 0,
        "audio_durations": [],
        "avg_audio_duration": 0,
        "last_audio_duration": 0,
        "last_request_time": None,
        "word_count": 0,
        "char_count": 0,
        "words_per_minute": 0
    },
    "whisper": {
        "requests": 0,
        "success": 0,
        "errors": 0,
        "latencies": [],
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "last_latency": 0,
        "audio_durations": [],
        "avg_audio_duration": 0,
        "last_audio_duration": 0,
        "last_request_time": None,
        "word_count": 0,
        "char_count": 0,
        "words_per_minute": 0,
        "cost": 0.0  # Coût cumulé des requêtes en USD
    },
    "vosk": {
        "requests": 0,
        "success": 0,
        "errors": 0,
        "latencies": [],
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "last_latency": 0,
        "audio_durations": [],
        "avg_audio_duration": 0,
        "last_audio_duration": 0,
        "last_request_time": None,
        "word_count": 0,
        "char_count": 0,
        "words_per_minute": 0
    },
    "whisper_ct2": {
        "requests": 0,
        "success": 0,
        "errors": 0,
        "latencies": [],
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "last_latency": 0,
        "audio_durations": [],
        "avg_audio_duration": 0,
        "last_audio_duration": 0,
        "last_request_time": None,
        "word_count": 0,
        "char_count": 0,
        "words_per_minute": 0
    },
    "whisper_french": {
        "requests": 0,
        "success": 0,
        "errors": 0,
        "latencies": [],
        "avg_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "last_latency": 0,
        "audio_durations": [],
        "avg_audio_duration": 0,
        "last_audio_duration": 0,
        "last_request_time": None,
        "word_count": 0,
        "char_count": 0,
        "words_per_minute": 0
    }
}

# Charger les métriques depuis la base de données au démarrage
try:
    # Importer le module de base de données
    try:
        from whisp_assistant.database_manager import get_stt_metrics as get_db_metrics
    except ImportError:
        try:
            from database_manager import get_stt_metrics as get_db_metrics
            
            # Récupérer les métriques depuis la base de données
            db_metrics = get_db_metrics()
            
            # Mettre à jour les métriques en mémoire
            for engine, metrics in db_metrics.items():
                if engine in stt_metrics:
                    for key, value in metrics.items():
                        if key in stt_metrics[engine] and key not in ["latencies", "audio_durations"]:
                            stt_metrics[engine][key] = value
            
            print("Métriques STT chargées depuis la base de données")
        except Exception as e:
            print(f"Erreur lors du chargement des métriques depuis la base de données: {e}")
except Exception as e:
    print(f"Erreur lors de l'importation du module de base de données: {e}")

def get_stt_metrics(from_db=False):
    """
    Retourne les métriques de performance STT
    
    Args:
        from_db: Si True, récupère les métriques depuis la base de données
        
    Returns:
        dict: Métriques de performance
    """
    global stt_metrics
    
    if from_db:
        try:
            # Importer le module de base de données
            try:
                # Essayer d'abord l'import en tant que package
                from whisp_assistant.database_manager import get_stt_metrics as get_db_metrics
            except ImportError:
                # Sinon, utiliser l'import relatif
                from database_manager import get_stt_metrics as get_db_metrics
            
            # Récupérer les métriques depuis la base de données
            db_metrics = get_db_metrics()
            
            # Fusionner avec les métriques en mémoire
            merged_metrics = db_metrics.copy()
            for engine, metrics in stt_metrics.items():
                if engine not in merged_metrics:
                    merged_metrics[engine] = metrics
                else:
                    # Mettre à jour les métriques existantes
                    for key, value in metrics.items():
                        if key not in merged_metrics[engine]:
                            merged_metrics[engine][key] = value
                        elif key in ["requests", "success", "errors", "word_count", "char_count"]:
                            # Pour les compteurs, prendre la valeur la plus élevée
                            merged_metrics[engine][key] = max(merged_metrics[engine][key], value)
            
            # Mettre à jour les métriques en mémoire avec les valeurs de la base de données
            # pour assurer la cohérence
            for engine, metrics in merged_metrics.items():
                if engine in stt_metrics:
                    for key, value in metrics.items():
                        if key in ["requests", "success", "errors", "word_count", "char_count", 
                                  "avg_latency", "min_latency", "max_latency", "avg_audio_duration"]:
                            stt_metrics[engine][key] = value
            
            return merged_metrics
        except Exception as e:
            print(f"Erreur lors de la récupération des métriques depuis la base de données: {e}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, retourner les métriques en mémoire
            return stt_metrics
    
    return stt_metrics

def reset_stt_metrics():
    """Réinitialise les métriques de performance STT"""
    global stt_metrics
    for engine in stt_metrics:
        stt_metrics[engine] = {
            "requests": 0,
            "success": 0,
            "errors": 0,
            "latencies": [],
            "avg_latency": 0,
            "min_latency": 0,
            "max_latency": 0,
            "last_latency": 0,
            "audio_durations": [],
            "avg_audio_duration": 0,
            "last_audio_duration": 0,
            "last_request_time": None,
            "word_count": 0,
            "char_count": 0,
            "words_per_minute": 0
        }
        # Ajouter le coût pour Whisper
        if engine == "whisper":
            stt_metrics[engine]["cost"] = 0.0
    
    # Réinitialiser également dans la base de données
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import reset_stt_metrics_db
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import reset_stt_metrics_db
        
        # Réinitialiser les métriques dans la base de données
        success = reset_stt_metrics_db()
        if success:
            print("Métriques STT réinitialisées dans la base de données")
        else:
            print("Échec de la réinitialisation des métriques STT dans la base de données")
    except Exception as e:
        print(f"Erreur lors de la réinitialisation des métriques dans la base de données: {e}")
        import traceback
        traceback.print_exc()
    
    # Réinitialiser également dans la base de données
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import reset_stt_metrics_db
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import reset_stt_metrics_db
        
        # Réinitialiser les métriques dans la base de données
        success = reset_stt_metrics_db()
        if success:
            print("Métriques STT réinitialisées dans la base de données")
        else:
            print("Échec de la réinitialisation des métriques STT dans la base de données")
    except Exception as e:
        print(f"Erreur lors de la réinitialisation des métriques dans la base de données: {e}")
        import traceback
        traceback.print_exc()

def update_stt_metrics(engine, success=True, latency=0, audio_duration=0, text=""):
    """Met à jour les métriques de performance STT"""
    # Vérifier que le moteur existe dans les métriques
    if engine not in stt_metrics:
        print(f"Erreur: Moteur '{engine}' non trouvé dans les métriques STT")
        return
    
    # S'assurer que les métriques pour Whisper CT2 sont correctement initialisées
    if engine == "whisper_ct2" and "whisper_ct2" not in stt_metrics:
        stt_metrics["whisper_ct2"] = {
            "requests": 0,
            "success": 0,
            "errors": 0,
            "latencies": [],
            "avg_latency": 0,
            "min_latency": 0,
            "max_latency": 0,
            "last_latency": 0,
            "audio_durations": [],
            "avg_audio_duration": 0,
            "last_audio_duration": 0,
            "last_request_time": None,
            "word_count": 0,
            "char_count": 0,
            "words_per_minute": 0
        }
    
    # Obtenir les métriques pour le moteur spécifié
    metrics = stt_metrics[engine]
    
    # Incrémenter les compteurs
    metrics["requests"] += 1
    if success:
        metrics["success"] += 1
    else:
        metrics["errors"] += 1
    
    # Enregistrer la latence
    if latency > 0:
        metrics["latencies"].append(latency)
        metrics["last_latency"] = latency
        
        # Calculer les statistiques de latence
        if metrics["latencies"]:
            metrics["avg_latency"] = statistics.mean(metrics["latencies"][-100:])  # Moyenne des 100 dernières requêtes
            metrics["min_latency"] = min(metrics["latencies"][-100:])
            metrics["max_latency"] = max(metrics["latencies"][-100:])
    
    # Enregistrer la durée audio
    if audio_duration > 0:
        metrics["audio_durations"].append(audio_duration)
        metrics["last_audio_duration"] = audio_duration
        
        # Calculer la durée audio moyenne
        if metrics["audio_durations"]:
            metrics["avg_audio_duration"] = statistics.mean(metrics["audio_durations"][-100:])
    
    # Enregistrer l'heure de la dernière requête
    metrics["last_request_time"] = datetime.now().strftime("%H:%M:%S")
    
    # Analyser le texte reconnu
    if text:
        word_count = len(text.split())
        char_count = len(text)
        metrics["word_count"] += word_count
        metrics["char_count"] += char_count
        
        # Calculer les mots par minute si nous avons une durée audio
        if audio_duration > 0:
            words_per_minute = (word_count / (audio_duration / 60)) if audio_duration > 0 else 0
            metrics["words_per_minute"] = words_per_minute
    
    # Sauvegarder les métriques dans la base de données
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import save_stt_metric, save_stt_metrics_history
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import save_stt_metric, save_stt_metrics_history
        
        # Sauvegarder les métriques principales dans la base de données
        # Nous ne sauvegardons pas les listes complètes pour des raisons de performance
        metrics_to_save = {
            "requests": metrics["requests"],
            "success": metrics["success"],
            "errors": metrics["errors"],
            "avg_latency": metrics["avg_latency"],
            "min_latency": metrics["min_latency"] if "min_latency" in metrics else 0,
            "max_latency": metrics["max_latency"] if "max_latency" in metrics else 0,
            "last_latency": metrics["last_latency"],
            "avg_audio_duration": metrics["avg_audio_duration"],
            "last_audio_duration": metrics["last_audio_duration"],
            "word_count": metrics["word_count"],
            "char_count": metrics["char_count"],
            "words_per_minute": metrics["words_per_minute"] if "words_per_minute" in metrics else 0
        }
        
        # Ajouter le coût pour Whisper
        if engine == "whisper" and "cost" in metrics:
            metrics_to_save["cost"] = metrics["cost"]
        
        # Sauvegarder chaque métrique
        for key, value in metrics_to_save.items():
            save_stt_metric(engine, key, str(value))
            
        # Sauvegarder un point d'historique toutes les 10 requêtes
        if metrics["requests"] % 10 == 0:
            save_stt_metrics_history(
                engine=engine,
                requests=metrics["requests"],
                success=metrics["success"],
                errors=metrics["errors"],
                avg_latency=metrics["avg_latency"],
                avg_audio_duration=metrics["avg_audio_duration"],
                word_count=metrics["word_count"],
                char_count=metrics["char_count"]
            )
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des métriques dans la base de données: {e}")
        import traceback
        traceback.print_exc()
    
    # Sauvegarder les métriques dans la base de données
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import save_stt_metric, save_stt_metrics_history
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import save_stt_metric, save_stt_metrics_history
        
        # Sauvegarder les métriques principales dans la base de données
        # Nous ne sauvegardons pas les listes complètes pour des raisons de performance
        metrics_to_save = {
            "requests": metrics["requests"],
            "success": metrics["success"],
            "errors": metrics["errors"],
            "avg_latency": metrics["avg_latency"],
            "min_latency": metrics["min_latency"] if "min_latency" in metrics else 0,
            "max_latency": metrics["max_latency"] if "max_latency" in metrics else 0,
            "last_latency": metrics["last_latency"],
            "avg_audio_duration": metrics["avg_audio_duration"],
            "last_audio_duration": metrics["last_audio_duration"],
            "word_count": metrics["word_count"],
            "char_count": metrics["char_count"],
            "words_per_minute": metrics["words_per_minute"] if "words_per_minute" in metrics else 0
        }
        
        # Ajouter le coût pour Whisper
        if engine == "whisper" and "cost" in metrics:
            metrics_to_save["cost"] = metrics["cost"]
        
        # Sauvegarder chaque métrique
        for key, value in metrics_to_save.items():
            save_stt_metric(engine, key, str(value))
            
        # Sauvegarder un point d'historique toutes les 10 requêtes
        if metrics["requests"] % 10 == 0:
            save_stt_metrics_history(
                engine=engine,
                requests=metrics["requests"],
                success=metrics["success"],
                errors=metrics["errors"],
                avg_latency=metrics["avg_latency"],
                avg_audio_duration=metrics["avg_audio_duration"],
                word_count=metrics["word_count"],
                char_count=metrics["char_count"]
            )
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des métriques dans la base de données: {e}")
        import traceback
        traceback.print_exc()
    
    # Notifier l'interface web des nouvelles métriques
    try:
        if 'web_interface' in sys.modules:
            from web_interface import web_message_queue
            import json
            # Envoyer les métriques mises à jour via SSE
            web_message_queue.put(json.dumps({"type": "metrics", "data": stt_metrics}))
            # Ajouter un log pour le débogage des métriques Whisper CT2
            if engine == "whisper_ct2":
                print(f"Métriques Whisper CT2 envoyées à l'interface web - Requêtes: {metrics['requests']}, Succès: {metrics['success']}, Latence: {metrics['last_latency']:.0f}ms")
    except Exception as e:
        print(f"Erreur lors de la notification des métriques à l'interface web: {e}")

def setup_recognition():
    """Configure et initialise le système de reconnaissance vocale"""
    # Vérifier que speech_recognition est correctement importé
    if not import_speech_recognition():
        raise ImportError("Problème avec le module speech_recognition")
    
    # Vérifier le moteur STT à utiliser
    stt_engine = get_stt_engine()
    
    # Vérifier la disponibilité des moteurs spécialisés à la demande avec tentatives robustes
    if stt_engine == "vosk":
        print("Vérification de la disponibilité de Vosk...")
        if not VOSK_AVAILABLE:
            print("Vosk non détecté, tentative d'importation...")
            if not import_vosk():
                print("Vosk n'est pas disponible même après tentative d'importation.")
                print("Utilisation de SpeechRecognition à la place")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("Vosk n'est pas disponible, utilisation de SpeechRecognition.", "warning")
                    log_to_web("Pour utiliser Vosk: pip install vosk", "info")
                set_stt_engine("speechrecognition")
                stt_engine = "speechrecognition"
            else:
                print("Vosk importé avec succès!")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("Vosk importé avec succès", "info")
        else:
            print("Vosk est disponible")
    
    if stt_engine == "whisper_ct2" or stt_engine == "whisper_french":
        print(f"Vérification de la disponibilité de {stt_engine}...")
        if not WHISPER_CT2_AVAILABLE:
            print("Bibliothèque faster-whisper non détectée, tentative d'importation...")
            if not import_whisper_ct2():
                print("La bibliothèque faster-whisper n'est pas disponible même après tentative d'importation.")
                print("Utilisation de SpeechRecognition à la place")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("La bibliothèque faster-whisper n'est pas disponible, utilisation de SpeechRecognition.", "warning")
                    log_to_web("Pour utiliser Whisper CT2/French: pip install ctranslate2 faster-whisper huggingface_hub", "info")
                set_stt_engine("speechrecognition")
                stt_engine = "speechrecognition"
            else:
                print("Bibliothèque faster-whisper importée avec succès!")
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("Bibliothèque faster-whisper importée avec succès", "info")
        else:
            print("Bibliothèque faster-whisper disponible")
    
    # Vérifier si la clé API OpenAI est disponible pour Whisper
    if stt_engine == "whisper":
        if not get_openai_api_key():
            print("Clé API OpenAI non configurée, utilisation de SpeechRecognition à la place")
            set_stt_engine("speechrecognition")
            stt_engine = "speechrecognition"
        else:
            # Importer requests à la demande pour Whisper API
            if not import_requests():
                print("Module requests non disponible, utilisation de SpeechRecognition à la place")
                set_stt_engine("speechrecognition")
                stt_engine = "speechrecognition"
            else:
                try:
                    return setup_whisper_recognition()
                except Exception as e:
                    print(f"Erreur lors de l'initialisation de Whisper: {e}")
                    print("Utilisation de SpeechRecognition comme solution de repli")
                    set_stt_engine("speechrecognition")
                    return setup_speechrecognition()
    
    # Importer numpy à la demande pour les autres moteurs
    if not import_numpy() and stt_engine != "speechrecognition":
        print("Module numpy non disponible, utilisation de SpeechRecognition à la place")
        set_stt_engine("speechrecognition")
        stt_engine = "speechrecognition"
    
    if stt_engine == "vosk" and VOSK_AVAILABLE:
        try:
            return setup_vosk_recognition()
        except Exception as e:
            print(f"Erreur lors de l'initialisation de Vosk: {e}")
            print("Utilisation de SpeechRecognition comme solution de repli")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
    elif stt_engine == "whisper_ct2" and WHISPER_CT2_AVAILABLE:
        try:
            return setup_whisper_ct2_recognition()
        except Exception as e:
            print(f"Erreur lors de l'initialisation de Whisper CT2: {e}")
            print("Utilisation de SpeechRecognition comme solution de repli")
            set_stt_engine("speechrecognition")
            return setup_speechrecognition()
    else:
        return setup_speechrecognition()

def setup_speechrecognition():
    """Configure et initialise le système de reconnaissance vocale avec SpeechRecognition et fallback intelligent"""
    # Test de disponibilité des alternatives audio
    AUDIO_BACKEND_AVAILABLE = False
    try:
        import sounddevice
        AUDIO_BACKEND_AVAILABLE = True
        print("[OK] sounddevice detecte - sera utilise comme alternative")
    except ImportError:
        print("[AVERTISSEMENT] sounddevice non disponible")

    # Initialisation du recognizer
    recognizer = sr.Recognizer()

    # Paramètres de sensibilité ajustés pour une meilleure continuité en dictée
    recognizer.pause_threshold = stt_settings["pause_threshold"]
    recognizer.energy_threshold = stt_settings["energy_threshold"]
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.non_speaking_duration = stt_settings["non_speaking_duration"]

    # Tentative de création du microphone avec fallback
    microphone = None

    # Essayer sounddevice d'abord (meilleure compatibilité ARM64)
    if AUDIO_BACKEND_AVAILABLE:
        try:
            import sounddevice as sd
            import numpy as np

            class SoundDeviceMicrophone:
                def __init__(self):
                    self.sample_rate = 16000
                    self.channels = 1
                    self.dtype = np.int16

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass

            microphone = SoundDeviceMicrophone()
            print("[OK] Utilisation de sounddevice (recommande pour ARM64)")
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur avec sounddevice: {e}")
            AUDIO_BACKEND_AVAILABLE = False

    # Fallback classique avec PyAudio
    if microphone is None:
        try:
            microphone = sr.Microphone()
            print("[OK] Utilisation de PyAudio classique")
        except Exception as e:
            print(f"[ERREUR CRITIQUE] Impossible d'initialiser le microphone")
            print(f"Erreur: {e}")
            print("\nSolutions recommandees:")
            print("   1. Installer sounddevice (recommande pour Windows ARM64):")
            print("      pip install sounddevice")
            print("   2. Essayer l'installation de PyAudio avec wheel:")
            print("      pip install pip-wheel")
            print("      pip install --only-binary :all: pyaudio")
            print("   3. Utiliser un autre moteur STT (Whisper/Vosk) qui n'a pas besoin de PyAudio")
            return None, None, None

    # Ajustement pour le bruit ambiant
    try:
        with microphone as source:
            print("Calibrage du microphone pour le bruit ambiant...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("Calibrage terminé, assistant prêt!")
    except Exception as e:
        print(f"[AVERTISSEMENT] Erreur lors du calibrage: {e}")
        print("L'assistant fonctionnera mais la reconnaissance vocale pourrait etre moins precise.")

    # Afficher les recommandations si necessaire
    if not AUDIO_BACKEND_AVAILABLE:
        print("\nRecommandation pour Windows ARM64:")
        print("   pip install sounddevice numpy")
        print("   sounddevice est compatible avec toutes les architectures")

    # Placeholder pour la fonction d'arrêt (sera définie plus tard)
    stop_listening = None

    return recognizer, microphone, stop_listening


@catch_errors(category=ErrorCategory.SPEECH_RECOGNITION, severity=ErrorSeverity.MEDIUM)
def process_audio(recognizer, audio, command_processor):
    """Traite l'audio capturé et le convertit en commande"""
    start_time = time.time()
    audio_duration = len(audio.frame_data) / (audio.sample_rate * audio.sample_width)
    
    try:
        # Importer l'exception UnknownValueError pour la gérer explicitement
        from speech_recognition.exceptions import UnknownValueError
        
        try:
            # Utilisation de Google Speech Recognition avec un niveau de confiance plus élevé en mode dictée
            if get_dictation_mode():
                # En mode dictée, on utilise un niveau de confiance plus bas pour capter plus de paroles
                texte = recognizer.recognize_google(audio, language="fr-FR", show_all=False)
                
                # Vérification spécifique pour les commandes de fin de dictée
                texte_lower = texte.lower().strip()
                phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                                "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
                
                if texte_lower in phrases_arret:
                    # Si c'est exactement une commande de fin, on la traite prioritairement
                    print(f"Commande de fin détectée: {texte}")
                    # Ne pas ajouter la commande de fin au texte dicté
                    return command_processor.process_command(texte)
            else:
                # Hors mode dictée, utiliser des paramètres optimisés pour la reconnaissance de commandes
                texte = recognizer.recognize_google(
                    audio, 
                    language="fr-FR",
                    # Paramètres supplémentaires pour améliorer la précision
                    show_all=False
                )
                
                # Vérifier si le texte est trop court (probablement incomplet)
                if len(texte.strip().split()) < 2 and len(texte.strip()) < 5:
                    # Stocker ce fragment pour une possible fusion avec le prochain
                    print(f"Fragment détecté: {texte} (en attente de suite...)")
                    
                    # Exception pour les réponses de confirmation (oui/non)
                    from exit_commands import traiter_reponse_confirmation, confirmation_en_cours
                    if confirmation_en_cours and texte.lower().strip() in ["oui", "non", "yes", "no"]:
                        print(f"Fragment de confirmation détecté: '{texte}' - Traitement prioritaire")
                        return command_processor.process_command(texte)
                    
                    # Ne pas traiter les autres fragments trop courts
                    return None
        except UnknownValueError:
            # Gérer l'exception UnknownValueError ici pour éviter qu'elle ne remonte
            # et soit traitée par le bloc except sr.UnknownValueError plus bas
            raise sr.UnknownValueError("Audio non reconnu")
        
        # Calculer la latence
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # en millisecondes
        
        # Enregistrer l'audio et le texte pour fine tuning
        save_audio_for_fine_tuning(audio, texte, "speechrecognition")
        
        # Mettre à jour les métriques
        update_stt_metrics(
            engine="speechrecognition",
            success=True,
            latency=latency,
            audio_duration=audio_duration,
            text=texte
        )
        
        # Affichage différent selon le mode
        if get_dictation_mode():
            print(f"Dictée: {texte}")
        else:
            print(f"Vous avez dit : {texte} (latence: {latency:.0f}ms, durée audio: {audio_duration:.2f}s)")
        
        # Exécution de la commande via le processeur de commandes
        resultat = command_processor.process_command(texte)
        print(f"Résultat : {resultat}")
        return resultat
    except sr.UnknownValueError:
        # Mettre à jour les métriques en cas d'erreur
        update_stt_metrics(
            engine="speechrecognition",
            success=False,
            audio_duration=audio_duration
        )
        
        if not get_dictation_mode():  # On n'affiche pas les erreurs en mode dictée pour ne pas polluer la console
            print("Audio non reconnu")
        
        # Ne pas journaliser cette erreur qui est un comportement normal
        # quand l'audio n'est pas reconnu
        return None
    except sr.RequestError as e:
        # Mettre à jour les métriques en cas d'erreur
        update_stt_metrics(
            engine="speechrecognition",
            success=False,
            audio_duration=audio_duration
        )
        
        error_msg = f"Service de reconnaissance vocale indisponible: {str(e)}"
        print(error_msg)
        
        # Enregistrer l'erreur avec un niveau de gravité moyen (problème de service)
        error_handler.handle_error(
            e, 
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.MEDIUM,
            notify_user=True,
            context={"audio_duration": audio_duration, "service": "Google Speech Recognition"}
        )
        
        # Notifier l'utilisateur via l'interface web si disponible
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web("Service de reconnaissance vocale indisponible. Vérifiez votre connexion internet.", "error")
        
        return "Erreur: Service de reconnaissance vocale indisponible"
    except Exception as e:
        # Mettre à jour les métriques en cas d'erreur
        update_stt_metrics(
            engine="speechrecognition",
            success=False,
            audio_duration=audio_duration
        )
        
        error_msg = f"Erreur lors de la reconnaissance vocale: {str(e)}"
        print(error_msg)
        
        # Enregistrer l'erreur avec un niveau de gravité élevé (erreur inattendue)
        error_handler.handle_error(
            e, 
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.HIGH,
            notify_user=True,
            context={"audio_duration": audio_duration, "engine": "speechrecognition"}
        )
        
        # Notifier l'utilisateur via l'interface web si disponible
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(f"Erreur lors de la reconnaissance vocale: {str(e)}", "error")
        
        return "Erreur lors de la reconnaissance vocale"

def callback(recognizer, audio, command_processor):
    """Fonction appelée lorsque de l'audio est détecté - Optimisée avec Numba"""
    # Vérifier l'énergie audio pour filtrer les faux positifs
    try:
        # Convertir les données audio en tableau numpy pour analyse
        audio_data = np.frombuffer(audio.frame_data, dtype=np.int16).astype(np.float32)

        # Utiliser Numba pour l'optimisation si disponible
        if NUMBA_AVAILABLE:
            # Optimisation audio avec Numba
            audio_data_optimized = optimize_audio_processing(audio_data)

            # Détection de parole optimisée
            threshold = float(stt_settings["speechrecognition_silence_threshold"])
            speech_detected = is_speech_active(audio_data_optimized, threshold)

            if not speech_detected:
                print(f"Audio ignoré - Pas de parole détectée (seuil: {threshold})")
                return

            # Calcul de l'énergie avec données optimisées
            energy = np.sqrt(np.mean(audio_data_optimized**2)) / 32768.0
            print(f"Audio détecté (optimisé Numba) - Énergie: {energy:.6f}")
        else:
            # Calcul standard de l'énergie du signal
            energy = np.sqrt(np.mean(audio_data**2)) / 32768.0

            # Vérifier si l'énergie est suffisante
            threshold = float(stt_settings["speechrecognition_silence_threshold"])
            if energy < threshold:
                print(f"Audio ignoré - Énergie trop faible: {energy:.6f} < {threshold}")
                return

            print(f"Audio détecté (standard) - Énergie: {energy:.6f}")

    except Exception as e:
        # En cas d'erreur dans l'analyse d'énergie, traiter l'audio quand même
        print(f"Erreur lors de l'analyse d'énergie: {e}")
    
    # Ajouter l'audio à la file d'attente pour traitement en arrière-plan
    audio_queue.put((audio, command_processor))
def setup_whisper_recognition():
    """Configure et initialise le système de reconnaissance vocale avec OpenAI Whisper API"""
    # Initialisation du recognizer (pour compatibilité)
    recognizer = sr.Recognizer()
    
    # Paramètres de sensibilité ajustés pour Whisper
    recognizer.pause_threshold = 0.6  # Plus court pour Whisper
    recognizer.energy_threshold = 120  # Plus sensible
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.1
    recognizer.dynamic_energy_ratio = 1.1  # Plus sensible
    
    # Lister les microphones disponibles pour le débogage
    print("Microphones disponibles:")
    for i, mic_name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {i}: {mic_name}")
    
    # Initialisation du microphone avec le taux d'échantillonnage approprié
    try:
        # Essayer d'utiliser le microphone par défaut
        microphone = sr.Microphone(sample_rate=WHISPER_SAMPLE_RATE)
        print(f"Microphone configuré avec sample_rate={WHISPER_SAMPLE_RATE}")
    except Exception as e:
        print(f"Erreur lors de l'initialisation du microphone: {e}")
        # Essayer avec un index spécifique (0 est souvent le microphone par défaut)
        try:
            microphone = sr.Microphone(device_index=0, sample_rate=WHISPER_SAMPLE_RATE)
            print("Utilisation du microphone avec index 0")
        except Exception as e2:
            print(f"Erreur avec l'index 0: {e2}")
            # Essayer avec d'autres indices de microphone
            for i in range(1, 5):  # Essayer les indices 1 à 4
                try:
                    microphone = sr.Microphone(device_index=i, sample_rate=WHISPER_SAMPLE_RATE)
                    print(f"Utilisation du microphone avec index {i}")
                    break
                except Exception:
                    continue
            else:
                # Dernier recours: utiliser le microphone par défaut sans spécifier le taux d'échantillonnage
                microphone = sr.Microphone()
                print("Utilisation du microphone par défaut sans sample_rate spécifié")
    
    # Vérifier que la clé API est configurée
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("Clé API OpenAI non configurée")
    else:
        # Vérifier le format de la clé API
        if not api_key.startswith('sk-'):
            print("AVERTISSEMENT: La clé API OpenAI ne commence pas par 'sk-', ce qui est inhabituel")
        print(f"Clé API OpenAI configurée: {api_key[:5]}...{api_key[-4:]} (longueur: {len(api_key)})")
    
    # Créer un répertoire temporaire pour les fichiers audio
    temp_dir = os.path.join(tempfile.gettempdir(), "whisp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Répertoire temporaire pour les fichiers audio: {temp_dir}")
    
    # Placeholder pour la fonction d'arrêt (sera définie plus tard)
    stop_listening = None
    
    print("Système de reconnaissance Whisper API prêt!")
    return recognizer, microphone, stop_listening

def start_whisper_french_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue avec Whisper French"""
    global active_threads, whisper_french_model, whisper_french_running, whisper_french_thread
    
    print("Démarrage de l'écoute Whisper French...")
    
    # S'assurer que tous les autres threads sont arrêtés
    arreter_threads_reconnaissance()
    
    # Attendre un court instant pour s'assurer que tous les threads sont arrêtés
    time.sleep(0.5)
    
    # Vérifier si le modèle Whisper French est chargé
    if whisper_french_model is None:
        print("Erreur: Le modèle Whisper French n'est pas chargé, tentative de chargement...")
        if not setup_whisper_french_model():
            error_msg = "Échec du chargement du modèle Whisper French, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return start_speechrecognition_listening(recognizer, microphone, command_processor)
        else:
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web("Modèle Whisper French chargé avec succès", "info")
            print("Modèle Whisper French chargé avec succès")
    
    # Arrêter le thread Whisper French s'il est déjà en cours d'exécution
    if whisper_french_thread is not None and whisper_french_thread.is_alive():
        print("Arrêt du thread Whisper French existant...")
        whisper_french_running = False
        whisper_french_thread.join(timeout=1.0)
    
    # Variable pour contrôler l'exécution du thread
    whisper_french_running = True
    
    # Créer un nouveau microphone pour éviter les problèmes de context manager
    try:
        # Fermer le microphone existant s'il est ouvert
        if hasattr(microphone, 'stream') and microphone.stream is not None:
            microphone.stream.close()
        
        # Créer un nouveau microphone avec le taux d'échantillonnage approprié
        new_microphone = sr.Microphone(sample_rate=WHISPER_FRENCH_SAMPLE_RATE)
    except Exception as e:
        print(f"Erreur lors de la création d'un nouveau microphone: {e}")
        new_microphone = microphone  # Utiliser l'ancien microphone en cas d'erreur
    
    # Thread de traitement audio en continu avec Whisper French
    def whisper_french_processing_thread():
        print("Thread de traitement audio Whisper French démarré")
        
        # Ouvrir le flux audio avec le nouveau microphone
        with new_microphone as source:
            try:
                # Ajuster pour le bruit ambiant
                print("Calibrage du microphone pour Whisper French...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Créer un stream audio
                audio_stream = source.stream
                
                # Variables pour le traitement en continu
                audio_buffer = []
                silence_counter = 0
                is_speaking = False
                
                while whisper_french_running and get_running():
                    # Vérifier si le moteur STT actuel est toujours Whisper French
                    if get_stt_engine() != "whisper_french":
                        print("Moteur STT changé, arrêt du thread Whisper French")
                        break
                        
                    try:
                        # Lire un chunk audio
                        audio_chunk = audio_stream.read(WHISPER_FRENCH_CHUNK_SIZE)
                        
                        # Convertir en numpy array pour analyse d'énergie
                        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        
                        # Calculer l'énergie du signal
                        energy = np.sqrt(np.mean(audio_data**2)) / 32768.0
                        
                        # Détecter si l'utilisateur parle
                        if energy > stt_settings["whisper_ct2_silence_threshold"]:  # Réutiliser le même paramètre que CT2
                            if not is_speaking:
                                print(f"Parole détectée (Whisper French) - Énergie: {energy:.6f}")
                            silence_counter = 0
                            is_speaking = True
                        else:
                            silence_counter += 1
                        
                        # Si l'utilisateur parle ou vient de parler, ajouter à la mémoire tampon
                        if is_speaking:
                            audio_buffer.append(audio_chunk)
                        
                        # Si suffisamment de silence après la parole, traiter l'audio accumulé
                        if is_speaking and silence_counter >= stt_settings["whisper_ct2_silence_chunks"]:
                            # Vérifier si l'enregistrement est assez long pour être significatif
                            audio_duration = len(audio_buffer) * WHISPER_FRENCH_CHUNK_SIZE / WHISPER_FRENCH_SAMPLE_RATE
                                
                            # Vérifier si l'audio est trop court
                            if len(audio_buffer) < WHISPER_FRENCH_MIN_SPEAKING_CHUNKS or audio_duration < WHISPER_FRENCH_MIN_AUDIO_DURATION:
                                print(f"Audio trop court ({audio_duration:.2f}s), minimum requis: {WHISPER_FRENCH_MIN_AUDIO_DURATION}s - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                                
                            # En mode dictée, on peut avoir des pauses plus longues
                            if get_dictation_mode() and silence_counter < WHISPER_FRENCH_SILENCE_CHUNKS * 2:
                                # Si l'audio n'est pas encore très long, attendre plus longtemps
                                if audio_duration < 10.0:
                                    print(f"Possible pause en dictée (durée actuelle: {audio_duration:.2f}s), attente prolongée")
                                    silence_counter = max(0, silence_counter - 2)
                                    continue
                            # Pour les commandes normales, on peut être plus agressif sur la détection de fin
                            elif not get_dictation_mode() and audio_duration > 1.5:
                                # Si on a déjà enregistré plus de 1.5s, terminer plus rapidement
                                if silence_counter >= WHISPER_FRENCH_SILENCE_CHUNKS // 2:
                                    print(f"Commande suffisamment longue ({audio_duration:.2f}s), fin anticipée")
                            
                            # Limiter la durée maximale de l'audio (différente selon le mode)
                            max_duration = WHISPER_FRENCH_DICTATION_MAX_DURATION if get_dictation_mode() else WHISPER_FRENCH_MAX_AUDIO_DURATION
                            
                            if audio_duration > max_duration:
                                print(f"Audio trop long ({audio_duration:.2f}s), tronqué à {max_duration}s")
                                # Calculer combien de chunks garder
                                chunks_to_keep = int(max_duration * WHISPER_FRENCH_SAMPLE_RATE / WHISPER_FRENCH_CHUNK_SIZE)
                                
                                # Conserver le début et la fin de l'audio pour les commandes longues
                                if chunks_to_keep > 20 and get_dictation_mode():
                                    start_chunks = int(chunks_to_keep * 0.7)
                                    end_chunks = chunks_to_keep - start_chunks
                                    audio_buffer = audio_buffer[:start_chunks] + audio_buffer[-end_chunks:]
                                else:
                                    # Pour les commandes courtes, garder le début
                                    audio_buffer = audio_buffer[:chunks_to_keep]
                                
                                audio_duration = max_duration
                            
                            # Concaténer tous les chunks audio
                            full_audio = b''.join(audio_buffer)
                            
                            # Vérifier si l'audio contient des données significatives
                            audio_values = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32)
                            audio_energy = np.sqrt(np.mean(audio_values**2)) / 32768.0
                            
                            if audio_energy < WHISPER_FRENCH_MIN_AUDIO_ENERGY:
                                print(f"Audio trop silencieux, énergie: {audio_energy:.6f} - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                            
                            print(f"Traitement audio Whisper French - Durée: {audio_duration:.2f}s, Énergie: {audio_energy:.6f}")
                            
                            # Marquer le temps de début du traitement
                            process_start_time = time.time()
                            
                            # Convertir les données audio en format approprié pour Whisper French
                            audio_samples = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32) / 32768.0
                            
                            # Traiter avec Whisper French
                            try:
                                # Transcription avec Whisper French
                                segments, info = whisper_french_model.transcribe(
                                    audio_samples, 
                                    language="fr",
                                    beam_size=5,
                                    word_timestamps=False,
                                    vad_filter=True,
                                    vad_parameters={"min_silence_duration_ms": 300},
                                    condition_on_previous_text=True,
                                    temperature=0.0,
                                    initial_prompt="Transcription en français. " + 
                                                  ("Dictée de texte." if get_dictation_mode() else "Commandes vocales courtes.")
                                )
                                
                                # Extraire le texte de tous les segments
                                texte = " ".join([segment.text for segment in segments])
                                
                                # Nettoyer le texte
                                try:
                                    from text_processing import nettoyer_commande
                                    texte = nettoyer_commande(texte)
                                except ImportError:
                                    # Si impossible d'importer, supprimer manuellement le point final
                                    if texte.endswith(".") or texte.endswith("!") or texte.endswith("?"):
                                        texte = texte[:-1].strip()
                                
                                # Calculer le temps de traitement réel
                                process_end_time = time.time()
                                process_latency = (process_end_time - process_start_time) * 1000  # en millisecondes
                                
                                # Enregistrer l'audio et le texte pour fine tuning
                                save_audio_for_fine_tuning(full_audio, texte, "whisper_french", sample_rate=WHISPER_FRENCH_SAMPLE_RATE)
                                
                                # Traiter le texte reconnu
                                if texte.strip():
                                    # Mettre à jour les métriques
                                    update_stt_metrics(
                                        engine="whisper_french",
                                        success=True,
                                        latency=process_latency,
                                        audio_duration=audio_duration,
                                        text=texte
                                    )
                                    
                                    # Vérification spécifique pour les commandes de fin de dictée
                                    if get_dictation_mode():
                                        texte_lower = texte.lower().strip()
                                        phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                                                        "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
                                        
                                        if texte_lower in phrases_arret:
                                            print(f"Commande de fin détectée: {texte}")
                                            command_processor.process_command(texte)
                                            # Réinitialiser
                                            audio_buffer = []
                                            is_speaking = False
                                            silence_counter = 0
                                            continue
                                    
                                    # Affichage différent selon le mode
                                    if get_dictation_mode():
                                        print(f"Dictée (Whisper French): {texte}")
                                    else:
                                        print(f"Vous avez dit (Whisper French): {texte} (latence: {process_latency:.0f}ms, durée audio: {audio_duration:.2f}s)")
                                    
                                    # Exécution de la commande via le processeur de commandes
                                    resultat = command_processor.process_command(texte)
                                    print(f"Résultat : {resultat}")
                                else:
                                    # Mettre à jour les métriques en cas d'échec
                                    update_stt_metrics(
                                        engine="whisper_french",
                                        success=False,
                                        audio_duration=audio_duration
                                    )
                                    print("Aucun texte reconnu par Whisper French")
                            except Exception as e:
                                # Mettre à jour les métriques en cas d'erreur
                                update_stt_metrics(
                                    engine="whisper_french",
                                    success=False,
                                    audio_duration=audio_duration
                                )
                                print(f"Erreur lors du traitement audio Whisper French: {e}")
                            
                            # Réinitialiser
                            audio_buffer = []
                            is_speaking = False
                            silence_counter = 0
                            
                    except Exception as e:
                        print(f"Erreur dans le thread Whisper French: {e}")
                        if not get_running() or not whisper_french_running:
                            break
            except Exception as e:
                print(f"Erreur lors de l'initialisation du microphone Whisper French: {e}")
    
    # Démarrer le thread Whisper French
    whisper_french_thread = threading.Thread(
        target=whisper_french_processing_thread,
        daemon=True,
        name="whisper_french_processing_thread"
    )
    whisper_french_thread.start()
    
    # Ajouter le thread à la liste des threads actifs
    active_threads.append(whisper_french_thread)
    
    # Fonction pour arrêter l'écoute
    def stop_whisper_french_listening(wait_for_stop=False):
        global whisper_french_running
        whisper_french_running = False
        
        # Si wait_for_stop est True, attendre que le thread se termine
        if wait_for_stop and whisper_french_thread is not None and whisper_french_thread.is_alive():
            whisper_french_thread.join(timeout=1.0)
    
    return stop_whisper_french_listening

def start_whisper_ct2_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue avec Whisper CT2"""
    global active_threads, whisper_ct2_model, whisper_ct2_running, whisper_ct2_thread
    
    print("Démarrage de l'écoute Whisper CT2...")
    
    # S'assurer que tous les autres threads sont arrêtés
    arreter_threads_reconnaissance()
    
    # Attendre un court instant pour s'assurer que tous les threads sont arrêtés
    time.sleep(0.5)
    
    # Vérifier si le modèle Whisper CT2 est chargé
    if whisper_ct2_model is None:
        print("Erreur: Le modèle Whisper CT2 n'est pas chargé, tentative de chargement...")
        if not setup_whisper_ct2_model():
            error_msg = "Échec du chargement du modèle Whisper CT2, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return start_speechrecognition_listening(recognizer, microphone, command_processor)
        else:
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web("Modèle Whisper CT2 chargé avec succès", "info")
            print("Modèle Whisper CT2 chargé avec succès")
    
    # Arrêter le thread Whisper CT2 s'il est déjà en cours d'exécution
    if whisper_ct2_thread is not None and whisper_ct2_thread.is_alive():
        print("Arrêt du thread Whisper CT2 existant...")
        whisper_ct2_running = False
        whisper_ct2_thread.join(timeout=1.0)
    
    # Variable pour contrôler l'exécution du thread
    whisper_ct2_running = True
    
    # Créer un nouveau microphone pour éviter les problèmes de context manager
    try:
        # Fermer le microphone existant s'il est ouvert
        if hasattr(microphone, 'stream') and microphone.stream is not None:
            microphone.stream.close()
        
        # Créer un nouveau microphone avec le taux d'échantillonnage approprié
        new_microphone = sr.Microphone(sample_rate=WHISPER_CT2_SAMPLE_RATE)
    except Exception as e:
        print(f"Erreur lors de la création d'un nouveau microphone: {e}")
        new_microphone = microphone  # Utiliser l'ancien microphone en cas d'erreur
    
    # Thread de traitement audio en continu avec Whisper CT2
    def whisper_ct2_processing_thread():
        print("Thread de traitement audio Whisper CT2 démarré")
        
        # Ouvrir le flux audio avec le nouveau microphone
        with new_microphone as source:
            try:
                # Ajuster pour le bruit ambiant
                print("Calibrage du microphone pour Whisper CT2...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Créer un stream audio
                audio_stream = source.stream
                
                # Variables pour le traitement en continu
                audio_buffer = []
                silence_counter = 0
                is_speaking = False
                
                while whisper_ct2_running and get_running():
                    # Vérifier si le moteur STT actuel est toujours Whisper CT2
                    if get_stt_engine() != "whisper_ct2":
                        print("Moteur STT changé, arrêt du thread Whisper CT2")
                        break
                        
                    try:
                        # Lire un chunk audio
                        audio_chunk = audio_stream.read(WHISPER_CT2_CHUNK_SIZE)
                        
                        # Convertir en numpy array pour analyse d'énergie
                        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        
                        # Calculer l'énergie du signal
                        energy = np.sqrt(np.mean(audio_data**2)) / 32768.0
                        
                        # Détecter si l'utilisateur parle
                        if energy > stt_settings["whisper_ct2_silence_threshold"]:
                            if not is_speaking:
                                print(f"Parole détectée (Whisper CT2) - Énergie: {energy:.6f}")
                            silence_counter = 0
                            is_speaking = True
                        else:
                            silence_counter += 1
                        
                        # Si l'utilisateur parle ou vient de parler, ajouter à la mémoire tampon
                        if is_speaking:
                            audio_buffer.append(audio_chunk)
                        
                        # Si suffisamment de silence après la parole, traiter l'audio accumulé
                        if is_speaking and silence_counter >= stt_settings["whisper_ct2_silence_chunks"]:
                            # Vérifier si l'enregistrement est assez long pour être significatif
                            audio_duration = len(audio_buffer) * WHISPER_CT2_CHUNK_SIZE / WHISPER_CT2_SAMPLE_RATE
                                
                            # Vérifier si l'audio est trop court
                            if len(audio_buffer) < WHISPER_CT2_MIN_SPEAKING_CHUNKS or audio_duration < WHISPER_CT2_MIN_AUDIO_DURATION:
                                print(f"Audio trop court ({audio_duration:.2f}s), minimum requis: {WHISPER_CT2_MIN_AUDIO_DURATION}s - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                                
                            # En mode dictée, on peut avoir des pauses plus longues
                            if get_dictation_mode() and silence_counter < WHISPER_CT2_SILENCE_CHUNKS * 2:
                                # Vérifier si l'utilisateur fait juste une pause dans sa dictée
                                # Si l'audio n'est pas encore très long, attendre plus longtemps
                                if audio_duration < 10.0:  # Pour les dictées courtes, attendre plus de silence
                                    print(f"Possible pause en dictée (durée actuelle: {audio_duration:.2f}s), attente prolongée")
                                    silence_counter = max(0, silence_counter - 2)  # Réduire le compteur de silence
                                    continue
                            # Pour les commandes normales, on peut être plus agressif sur la détection de fin
                            elif not get_dictation_mode() and audio_duration > 1.5:
                                # Si on a déjà enregistré plus de 1.5s, on peut considérer que c'est suffisant
                                # pour une commande courte et terminer plus rapidement
                                if silence_counter >= WHISPER_CT2_SILENCE_CHUNKS // 2:
                                    print(f"Commande suffisamment longue ({audio_duration:.2f}s), fin anticipée")
                                    # On ne réduit pas le compteur, on continue pour traiter l'audio
                            
                            # Vérifier si l'audio contient encore de la parole à la fin
                            # Analyser les derniers chunks pour voir s'ils contiennent encore de la parole
                            # Seulement pour le mode dictée ou les audios courts
                            if get_dictation_mode() or audio_duration < 1.0:
                                last_chunks = audio_buffer[-min(WHISPER_CT2_SILENCE_CHUNKS, len(audio_buffer)):]
                                last_chunks_energy = 0
                                if last_chunks:
                                    last_audio = b''.join(last_chunks)
                                    last_values = np.frombuffer(last_audio, dtype=np.int16).astype(np.float32)
                                    last_chunks_energy = np.sqrt(np.mean(last_values**2)) / 32768.0
                                
                                # Si les derniers chunks contiennent encore de la parole significative, attendre plus longtemps
                                if last_chunks_energy > WHISPER_CT2_SILENCE_THRESHOLD * 1.5:
                                    print(f"Parole encore détectée à la fin (énergie: {last_chunks_energy:.6f}), attente prolongée")
                                    silence_counter = max(0, silence_counter - 2)  # Réduire le compteur de silence
                                    continue
                            
                            # Limiter la durée maximale de l'audio (différente selon le mode)
                            max_duration = WHISPER_CT2_DICTATION_MAX_DURATION if get_dictation_mode() else WHISPER_CT2_MAX_AUDIO_DURATION
                            
                            if audio_duration > max_duration:
                                print(f"Audio trop long ({audio_duration:.2f}s), tronqué à {max_duration}s")
                                # Calculer combien de chunks garder
                                chunks_to_keep = int(max_duration * WHISPER_CT2_SAMPLE_RATE / WHISPER_CT2_CHUNK_SIZE)
                                
                                # Conserver le début et la fin de l'audio, qui sont généralement les plus importants
                                # Garder 70% du début et 30% de la fin pour les commandes longues
                                if chunks_to_keep > 20 and get_dictation_mode():  # Seulement pour les dictées longues
                                    start_chunks = int(chunks_to_keep * 0.7)
                                    end_chunks = chunks_to_keep - start_chunks
                                    audio_buffer = audio_buffer[:start_chunks] + audio_buffer[-end_chunks:]
                                else:
                                    # Pour les commandes courtes, garder le début qui contient généralement la commande
                                    audio_buffer = audio_buffer[:chunks_to_keep]
                                
                                audio_duration = max_duration
                            
                            # Concaténer tous les chunks audio
                            full_audio = b''.join(audio_buffer)
                            
                            # Vérifier si l'audio contient des données significatives
                            audio_values = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32)
                            audio_energy = np.sqrt(np.mean(audio_values**2)) / 32768.0
                            
                            if audio_energy < WHISPER_CT2_MIN_AUDIO_ENERGY:
                                print(f"Audio trop silencieux, énergie: {audio_energy:.6f} - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                            
                            print(f"Traitement audio Whisper CT2 - Durée: {audio_duration:.2f}s, Énergie: {audio_energy:.6f}")
                            
                            # Marquer le temps de début du traitement
                            process_start_time = time.time()
                            
                            # Convertir les données audio en format approprié pour Whisper CT2
                            audio_samples = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32) / 32768.0
                            
                            # Traiter avec Whisper CT2
                            try:
                                # Transcription avec Whisper CT2
                                segments, info = whisper_ct2_model.transcribe(
                                    audio_samples, 
                                    language=WHISPER_CT2_LANGUAGE,
                                    beam_size=5,
                                    word_timestamps=False,
                                    vad_filter=True,
                                    vad_parameters={"min_silence_duration_ms": 300},  # Réduit pour être plus réactif
                                    condition_on_previous_text=True,  # Améliore la cohérence
                                    temperature=0.0,  # Réduit la créativité pour plus de précision
                                    initial_prompt="Transcription en français. " + 
                                                  ("Dictée de texte." if get_dictation_mode() else "Commandes vocales courtes.")  # Adapte le prompt selon le mode
                                )
                                
                                # Extraire le texte de tous les segments
                                texte = " ".join([segment.text for segment in segments])
                                
                                # Nettoyer le texte (supprimer le point final et autres ponctuations qui peuvent perturber les commandes)
                                try:
                                    from text_processing import nettoyer_commande
                                    texte = nettoyer_commande(texte)
                                except ImportError:
                                    # Si impossible d'importer, supprimer manuellement le point final
                                    if texte.endswith(".") or texte.endswith("!") or texte.endswith("?"):
                                        texte = texte[:-1].strip()
                                
                                # Calculer le temps de traitement réel
                                process_end_time = time.time()
                                process_latency = (process_end_time - process_start_time) * 1000  # en millisecondes
                                
                                # Enregistrer l'audio et le texte pour fine tuning
                                save_audio_for_fine_tuning(full_audio, texte, "whisper_ct2", sample_rate=WHISPER_CT2_SAMPLE_RATE)
                                
                                # Traiter le texte reconnu
                                if texte.strip():
                                    # Mettre à jour les métriques
                                    update_stt_metrics(
                                        engine="whisper_ct2",
                                        success=True,
                                        latency=process_latency,
                                        audio_duration=audio_duration,
                                        text=texte
                                    )
                                    
                                    # Afficher les métriques mises à jour pour le débogage
                                    print(f"Métriques Whisper CT2 mises à jour - Requêtes: {stt_metrics['whisper_ct2']['requests']}, Succès: {stt_metrics['whisper_ct2']['success']}")
                                    
                                    # Vérification spécifique pour les commandes de fin de dictée
                                    if get_dictation_mode():
                                        texte_lower = texte.lower().strip()
                                        phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                                                        "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
                                        
                                        if texte_lower in phrases_arret:
                                            print(f"Commande de fin détectée: {texte}")
                                            command_processor.process_command(texte)
                                            # Réinitialiser
                                            audio_buffer = []
                                            is_speaking = False
                                            silence_counter = 0
                                            continue
                                    
                                    # Affichage différent selon le mode
                                    if get_dictation_mode():
                                        print(f"Dictée (Whisper CT2): {texte}")
                                    else:
                                        print(f"Vous avez dit (Whisper CT2): {texte} (latence: {process_latency:.0f}ms, durée audio: {audio_duration:.2f}s)")
                                    
                                    # Exécution de la commande via le processeur de commandes
                                    resultat = command_processor.process_command(texte)
                                    print(f"Résultat : {resultat}")
                                else:
                                    # Mettre à jour les métriques en cas d'échec
                                    update_stt_metrics(
                                        engine="whisper_ct2",
                                        success=False,
                                        audio_duration=audio_duration
                                    )
                                    print("Aucun texte reconnu par Whisper CT2")
                            except Exception as e:
                                # Mettre à jour les métriques en cas d'erreur
                                update_stt_metrics(
                                    engine="whisper_ct2",
                                    success=False,
                                    audio_duration=audio_duration
                                )
                                print(f"Erreur lors du traitement audio Whisper CT2: {e}")
                            
                            # Réinitialiser
                            audio_buffer = []
                            is_speaking = False
                            silence_counter = 0
                            
                    except Exception as e:
                        print(f"Erreur dans le thread Whisper CT2: {e}")
                        if not get_running() or not whisper_ct2_running:
                            break
            except Exception as e:
                print(f"Erreur lors de l'initialisation du microphone Whisper CT2: {e}")
    
    # Démarrer le thread Whisper CT2
    whisper_ct2_thread = threading.Thread(
        target=whisper_ct2_processing_thread,
        daemon=True,
        name="whisper_ct2_processing_thread"
    )
    whisper_ct2_thread.start()
    
    # Ajouter le thread à la liste des threads actifs
    active_threads.append(whisper_ct2_thread)
    
    # Fonction pour arrêter l'écoute
    def stop_whisper_ct2_listening(wait_for_stop=False):
        global whisper_ct2_running
        whisper_ct2_running = False
        
        # Si wait_for_stop est True, attendre que le thread se termine
        if wait_for_stop and whisper_ct2_thread is not None and whisper_ct2_thread.is_alive():
            whisper_ct2_thread.join(timeout=1.0)
    
    return stop_whisper_ct2_listening

def start_continuous_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue en arrière-plan avec traitement asynchrone"""
    global _recognizer, _microphone, _command_processor, _stop_listening_func
    
    # Stocker les références pour pouvoir redémarrer plus tard
    _recognizer = recognizer
    _microphone = microphone
    _command_processor = command_processor
    
    # Afficher des informations pour le débogage
    print(f"start_continuous_listening: command_processor {'défini' if command_processor else 'manquant'}")
    
    # Vérifier le moteur STT à utiliser
    stt_engine = get_stt_engine()
    print(f"Démarrage de l'écoute continue avec le moteur: {stt_engine}")
    
    # Arrêter les threads existants avant de démarrer un nouveau mode d'écoute
    print("Arrêt de tous les threads de reconnaissance vocale existants...")
    arreter_threads_reconnaissance()
    
    # Attendre un court instant pour s'assurer que tous les threads sont arrêtés
    time.sleep(1.0)  # Augmenter le délai d'attente pour s'assurer que tous les threads sont arrêtés
    print("Démarrage du nouveau moteur de reconnaissance vocale...")
    
    # Vérifier si nous sommes en mode dictée ou traduction
    if get_dictation_mode() or get_translation_mode():
        print("Mode dictée ou traduction actif, désactivation temporaire pour le changement de moteur")
    
    if stt_engine == "vosk" and not VOSK_AVAILABLE:
        print("Vosk n'est pas disponible, utilisation de SpeechRecognition à la place")
        set_stt_engine("speechrecognition")
        stt_engine = "speechrecognition"
    
    # Démarrer l'écoute avec le moteur approprié
    if stt_engine == "whisper":
        print("Démarrage de l'écoute avec OpenAI Whisper API...")
        _stop_listening_func = start_whisper_listening(recognizer, microphone, command_processor)
    elif stt_engine == "vosk" and VOSK_AVAILABLE:
        print("Démarrage de l'écoute avec Vosk...")
        _stop_listening_func = start_vosk_listening(recognizer, microphone, command_processor)
    elif stt_engine == "whisper_ct2" and WHISPER_CT2_AVAILABLE:
        print("Démarrage de l'écoute avec Whisper CT2...")
        _stop_listening_func = start_whisper_ct2_listening(recognizer, microphone, command_processor)
    elif stt_engine == "whisper_french" and WHISPER_CT2_AVAILABLE:  # Même dépendance que CT2
        print("Démarrage de l'écoute avec Whisper French...")
        _stop_listening_func = start_whisper_french_listening(recognizer, microphone, command_processor)
    else:
        print("Démarrage de l'écoute avec SpeechRecognition...")
        _stop_listening_func = start_speechrecognition_listening(recognizer, microphone, command_processor)
    
    # Journaliser le changement de moteur
    if 'web_interface' in sys.modules:
        from web_interface import log_to_web
        log_to_web(f"Écoute démarrée avec le moteur: {stt_engine}", "info")
    
    return _stop_listening_func

def start_speechrecognition_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue avec SpeechRecognition"""
    
    # Créer un nouveau microphone pour éviter les problèmes de context manager
    try:
        # Fermer le microphone existant s'il est ouvert
        if hasattr(microphone, 'stream') and microphone.stream is not None:
            microphone.stream.close()
        
        # Créer un nouveau microphone
        new_microphone = sr.Microphone()
        
        # S'assurer que numpy est importé pour l'analyse d'énergie
        if not import_numpy():
            print("Avertissement: numpy n'est pas disponible, l'analyse d'énergie sera désactivée")
    except Exception as e:
        print(f"Erreur lors de la création d'un nouveau microphone: {e}")
        new_microphone = microphone  # Utiliser l'ancien microphone en cas d'erreur
    
    # Thread de traitement audio
    def audio_processing_thread():
        print("Thread de traitement audio SpeechRecognition démarré")
        while get_running():
            try:
                # Récupérer l'audio de la file d'attente avec un timeout court
                # pour réagir rapidement à l'arrêt
                audio_data, processor = audio_queue.get(timeout=0.2)
                # Traiter l'audio
                process_audio(recognizer, audio_data, processor)
                audio_queue.task_done()
            except queue.Empty:
                # Pas d'audio à traiter, continuer la boucle
                # Vérifier si on doit s'arrêter
                if not get_running():
                    break
                continue
            except Exception as e:
                print(f"Erreur dans le thread de traitement audio: {e}")
                # Vérifier si on doit s'arrêter
                if not get_running():
                    break
    
    # Démarrer le thread de traitement audio
    processing_thread = threading.Thread(
        target=audio_processing_thread,
        daemon=True,
        name="audio_processing_thread"
    )
    processing_thread.start()
    
    # Ajouter le thread à la liste des threads actifs
    global active_threads
    active_threads.append(processing_thread)
    
    # Configurer les paramètres du recognizer avant d'appeler listen_in_background
    recognizer.pause_threshold = stt_settings["pause_threshold"]
    recognizer.non_speaking_duration = stt_settings["non_speaking_duration"]
    recognizer.energy_threshold = stt_settings["energy_threshold"]
    
    # Afficher les paramètres configurés
    print(f"SpeechRecognition configuré avec: pause_threshold={stt_settings['pause_threshold']}, "
          f"non_speaking_duration={stt_settings['non_speaking_duration']}, energy_threshold={stt_settings['energy_threshold']}")
    
    # Démarrer l'écoute en arrière-plan avec des paramètres optimisés pour la capture de phrases complètes
    try:
        stop_listening = recognizer.listen_in_background(
            new_microphone, 
            lambda r, a: callback(r, a, command_processor),
            phrase_time_limit=stt_settings["phrase_timeout"]
        )
        return stop_listening
    except Exception as e:
        print(f"Erreur lors du démarrage de l'écoute: {e}")
        # Essayer avec l'ancien microphone en cas d'erreur
        try:
            stop_listening = recognizer.listen_in_background(
                microphone, 
                lambda r, a: callback(r, a, command_processor),
                phrase_time_limit=stt_settings["phrase_timeout"]
            )
            return stop_listening
        except Exception as e2:
            print(f"Erreur critique lors du démarrage de l'écoute: {e2}")
            return lambda **kwargs: None  # Fonction vide en cas d'échec

# Fonction utilitaire pour normaliser le texte
def save_audio_for_fine_tuning(audio_data, recognized_text, stt_engine, audio_format="wav", sample_rate=16000):
    """
    Sauvegarde l'audio et le texte reconnu pour un fine tuning ultérieur
    dans un format compatible avec Hugging Face Datasets
    
    Args:
        audio_data: Données audio à sauvegarder (bytes, AudioData, numpy array ou file-like)
        recognized_text: Texte reconnu
        stt_engine: Moteur STT utilisé (speechrecognition, whisper, vosk, whisper_ct2)
        audio_format: Format d'enregistrement (wav par défaut)
        sample_rate: Taux d'échantillonnage pour les données audio brutes (16000 par défaut)
    """
    if not recognized_text or len(recognized_text.strip()) == 0:
        return False  # Ne pas enregistrer si le texte est vide
        
    try:
        # Créer le dossier records s'il n'existe pas
        records_dir = os.path.join(os.getcwd(), "records")
        os.makedirs(records_dir, exist_ok=True)
        
        # Créer un sous-dossier pour chaque moteur
        engine_dir = os.path.join(records_dir, stt_engine)
        os.makedirs(engine_dir, exist_ok=True)
        
        # Créer un sous-dossier pour les splits de Hugging Face (par défaut tout dans train)
        split = "train"  # Pourrait être paramétré ou calculé (ex: 80% train, 10% validation, 10% test)
        split_dir = os.path.join(engine_dir, split)
        os.makedirs(split_dir, exist_ok=True)
        
        # Générer un nom de fichier unique basé sur l'horodatage
        timestamp = int(time.time())
        filename_base = f"{timestamp}_{stt_engine}"
        audio_path = os.path.join(split_dir, f"{filename_base}.{audio_format}")
        text_path = os.path.join(split_dir, f"{filename_base}.txt")
        
        # Chemin relatif pour le dataset
        rel_audio_path = os.path.join(stt_engine, split, f"{filename_base}.{audio_format}")
        
        # Variables pour les métadonnées
        audio_duration = None
        audio_sample_rate = sample_rate
        audio_sample_width = 2  # 16 bits par défaut
        
        # Convertir et sauvegarder l'audio dans un format approprié
        if isinstance(audio_data, sr.AudioData):
            # Pour les objets AudioData de SpeechRecognition
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(audio_data.sample_width)
                wf.setframerate(audio_data.sample_rate)
                wf.writeframes(audio_data.frame_data)
            audio_duration = len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)
            audio_sample_rate = audio_data.sample_rate
            audio_sample_width = audio_data.sample_width
        elif isinstance(audio_data, str) and os.path.exists(audio_data):
            # Pour les chemins de fichiers
            with open(audio_data, 'rb') as src_file:
                with open(audio_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            # Tenter d'obtenir la durée audio
            try:
                with wave.open(audio_data, 'rb') as wf:
                    audio_duration = wf.getnframes() / wf.getframerate()
                    audio_sample_rate = wf.getframerate()
                    audio_sample_width = wf.getsampwidth()
            except Exception:
                pass
        elif isinstance(audio_data, bytes):
            # Pour les données audio brutes en bytes
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            audio_duration = len(audio_data) / (sample_rate * 2)
        elif isinstance(audio_data, np.ndarray):
            # Pour les tableaux numpy
            if audio_data.dtype == np.float32:
                # Convertir les flottants en int16
                audio_data = (audio_data * 32767).astype(np.int16)
            
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            audio_duration = len(audio_data) / sample_rate
        
        # Sauvegarder le texte reconnu
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(recognized_text)
        
        # Créer un fichier JSON avec les métadonnées pour le fine-tuning
        metadata = {
            "audio_file": os.path.basename(audio_path),
            "text": recognized_text,
            "engine": stt_engine,
            "timestamp": timestamp,
            "duration": audio_duration,
            "sample_rate": audio_sample_rate,
            "sample_width": audio_sample_width,
            "split": split
        }
        
        # Enregistrer les métadonnées
        json_path = os.path.join(split_dir, f"{filename_base}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Mettre à jour le fichier metadata.jsonl global (format compatible HF)
        metadata_entry = {
            "path": rel_audio_path,
            "audio": {
                "path": rel_audio_path,
                "array": None,  # Non stocké dans le JSON
                "sampling_rate": audio_sample_rate
            },
            "sentence": recognized_text,
            "transcription": recognized_text,
            "engine": stt_engine,
            "duration": audio_duration,
            "timestamp": timestamp,
            "split": split
        }
        
        metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
        
        # Ajouter l'entrée au fichier jsonl (1 JSON par ligne)
        with open(metadata_jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metadata_entry, ensure_ascii=False) + "\n")
        
        # Mettre à jour ou créer le fichier dataset_info.json si nécessaire
        dataset_info_path = os.path.join(records_dir, "dataset_info.json")
        if not os.path.exists(dataset_info_path):
            dataset_info = {
                "description": "Dataset d'enregistrements audio pour fine-tuning de modèles de reconnaissance vocale",
                "citation": "",
                "homepage": "",
                "license": "",
                "features": {
                    "path": {"dtype": "string", "id": None, "_type": "Value"},
                    "audio": {
                        "dtype": "dict",
                        "id": None,
                        "_type": "Audio",
                        "sampling_rate": 16000
                    },
                    "sentence": {"dtype": "string", "id": None, "_type": "Value"},
                    "transcription": {"dtype": "string", "id": None, "_type": "Value"},
                    "engine": {"dtype": "string", "id": None, "_type": "Value"},
                    "duration": {"dtype": "float32", "id": None, "_type": "Value"},
                    "timestamp": {"dtype": "int64", "id": None, "_type": "Value"},
                    "split": {"dtype": "string", "id": None, "_type": "Value"}
                },
                "splits": {
                    "train": {"name": "train", "num_bytes": 0, "num_examples": 0},
                    "validation": {"name": "validation", "num_bytes": 0, "num_examples": 0},
                    "test": {"name": "test", "num_bytes": 0, "num_examples": 0}
                }
            }
            with open(dataset_info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement pour fine tuning: {e}")
        return False

def normalize_text(text_input):
    # Vérifier si c'est une liste ou un tuple
    if isinstance(text_input, (list, tuple)):
        # Prendre le premier élément s'il existe
        if text_input and len(text_input) > 0:
            text_input = text_input[0]
        else:
            text_input = ""
    
    # S'assurer que c'est bien une chaîne de caractères
    if not isinstance(text_input, str):
        text_input = str(text_input)
        
    return text_input

def generate_huggingface_dataset():
    """
    Génère un dataset compatible avec Hugging Face à partir des enregistrements existants
    
    Returns:
        bool: True si le dataset a été généré avec succès
    """
    try:
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            print(f"Dossier records non trouvé: {records_dir}")
            return False
            
        # Vérifier si metadata.jsonl existe déjà
        metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
        if os.path.exists(metadata_jsonl_path):
            print(f"Le fichier metadata.jsonl existe déjà: {metadata_jsonl_path}")
            # En option, on pourrait régénérer le fichier
        
        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]
        total_processed = 0
        
        # Ouvrir le fichier metadata.jsonl en mode écriture (écrase le contenu existant)
        with open(metadata_jsonl_path, 'w', encoding='utf-8') as metadata_file:
            # Pour chaque moteur, parcourir les fichiers JSON
            for engine in engines:
                engine_dir = os.path.join(records_dir, engine)
                
                # Parcourir récursivement tous les fichiers JSON
                json_files = []
                for root, dirs, files in os.walk(engine_dir):
                    json_files.extend([os.path.join(root, f) for f in files if f.endswith('.json')])
                
                for json_path in json_files:
                    try:
                        # Charger les métadonnées existantes
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Déterminer le chemin du fichier audio
                        audio_file = metadata.get("audio_file")
                        audio_path = os.path.join(os.path.dirname(json_path), audio_file)
                        
                        # Vérifier si le fichier audio existe
                        if not os.path.exists(audio_path):
                            print(f"Fichier audio non trouvé: {audio_path}")
                            continue
                        
                        # Déterminer le split (dossier parent immédiat ou "train" par défaut)
                        parent_dir = os.path.basename(os.path.dirname(json_path))
                        split = parent_dir if parent_dir in ["train", "validation", "test"] else "train"
                        
                        # Chemin relatif pour le dataset
                        rel_path = os.path.relpath(audio_path, records_dir)
                        
                        # Créer l'entrée metadata au format Hugging Face
                        metadata_entry = {
                            "path": rel_path,
                            "audio": {
                                "path": rel_path,
                                "array": None,  # Non stocké dans le JSON
                                "sampling_rate": metadata.get("sample_rate", 16000)
                            },
                            "sentence": metadata.get("text", ""),
                            "transcription": metadata.get("text", ""),
                            "engine": metadata.get("engine", engine),
                            "duration": metadata.get("duration", 0),
                            "timestamp": metadata.get("timestamp", 0),
                            "split": split
                        }
                        
                        # Écrire dans le fichier metadata.jsonl
                        metadata_file.write(json.dumps(metadata_entry, ensure_ascii=False) + "\n")
                        total_processed += 1
                    except Exception as e:
                        print(f"Erreur lors du traitement du fichier {json_path}: {e}")
                        continue
        
        # Créer ou mettre à jour le fichier dataset_info.json
        dataset_info_path = os.path.join(records_dir, "dataset_info.json")
        dataset_info = {
            "description": "Dataset d'enregistrements audio pour fine-tuning de modèles de reconnaissance vocale",
            "citation": "",
            "homepage": "",
            "license": "",
            "features": {
                "path": {"dtype": "string", "id": None, "_type": "Value"},
                "audio": {
                    "dtype": "dict",
                    "id": None,
                    "_type": "Audio",
                    "sampling_rate": 16000
                },
                "sentence": {"dtype": "string", "id": None, "_type": "Value"},
                "transcription": {"dtype": "string", "id": None, "_type": "Value"},
                "engine": {"dtype": "string", "id": None, "_type": "Value"},
                "duration": {"dtype": "float32", "id": None, "_type": "Value"},
                "timestamp": {"dtype": "int64", "id": None, "_type": "Value"},
                "split": {"dtype": "string", "id": None, "_type": "Value"}
            },
            "splits": {
                "train": {"name": "train", "num_bytes": 0, "num_examples": 0},
                "validation": {"name": "validation", "num_bytes": 0, "num_examples": 0},
                "test": {"name": "test", "num_bytes": 0, "num_examples": 0}
            }
        }
        
        with open(dataset_info_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)
        
        print(f"Dataset Hugging Face généré avec succès: {total_processed} échantillons")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du dataset Hugging Face: {e}")
        return False

def split_dataset(train_ratio=0.8, validation_ratio=0.1, test_ratio=0.1):
    """
    Répartit les échantillons existants entre les splits train/validation/test
    
    Args:
        train_ratio: Proportion d'échantillons pour l'entraînement (0.8 par défaut)
        validation_ratio: Proportion d'échantillons pour la validation (0.1 par défaut)
        test_ratio: Proportion d'échantillons pour le test (0.1 par défaut)
        
    Returns:
        bool: True si la répartition a été effectuée avec succès
    """
    try:
        # Vérifier que la somme des ratios est égale à 1
        if abs(train_ratio + validation_ratio + test_ratio - 1.0) > 0.001:
            print(f"La somme des ratios doit être égale à 1, reçu: {train_ratio + validation_ratio + test_ratio}")
            return False
            
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            print(f"Dossier records non trouvé: {records_dir}")
            return False
        
        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]
        
        for engine in engines:
            engine_dir = os.path.join(records_dir, engine)
            
            # Créer les dossiers de splits s'ils n'existent pas
            train_dir = os.path.join(engine_dir, "train")
            validation_dir = os.path.join(engine_dir, "validation")
            test_dir = os.path.join(engine_dir, "test")
            
            os.makedirs(train_dir, exist_ok=True)
            os.makedirs(validation_dir, exist_ok=True)
            os.makedirs(test_dir, exist_ok=True)
            
            # Récupérer tous les ensembles d'échantillons (WAV, TXT, JSON)
            sample_sets = []
            
            for root, dirs, files in os.walk(engine_dir):
                # Ignorer les dossiers train/validation/test eux-mêmes
                if os.path.basename(root) in ["train", "validation", "test"]:
                    continue
                
                # Récupérer tous les fichiers JSON à la racine de engine_dir
                json_files = [f for f in files if f.endswith('.json')]
                
                for json_file in json_files:
                    json_path = os.path.join(root, json_file)
                    base_name = json_file[:-5]  # Enlever l'extension .json
                    
                    # Construire les chemins pour les fichiers WAV et TXT
                    wav_path = os.path.join(root, f"{base_name}.wav")
                    txt_path = os.path.join(root, f"{base_name}.txt")
                    
                    # Vérifier que les fichiers existent
                    if os.path.exists(wav_path) and os.path.exists(txt_path):
                        sample_sets.append((json_path, wav_path, txt_path))
            
            # Mélanger les échantillons pour une répartition aléatoire
            import random
            random.shuffle(sample_sets)
            
            # Calculer le nombre d'échantillons pour chaque split
            total_samples = len(sample_sets)
            train_count = int(total_samples * train_ratio)
            validation_count = int(total_samples * validation_ratio)
            # Le reste va dans test
            
            train_samples = sample_sets[:train_count]
            validation_samples = sample_sets[train_count:train_count + validation_count]
            test_samples = sample_sets[train_count + validation_count:]
            
            # Déplacer les échantillons dans les dossiers appropriés
            def move_samples(samples, target_dir):
                for json_path, wav_path, txt_path in samples:
                    # Extraire les noms de fichiers
                    json_file = os.path.basename(json_path)
                    wav_file = os.path.basename(wav_path)
                    txt_file = os.path.basename(txt_path)
                    
                    # Définir les chemins cibles
                    target_json = os.path.join(target_dir, json_file)
                    target_wav = os.path.join(target_dir, wav_file)
                    target_txt = os.path.join(target_dir, txt_file)
                    
                    # Déplacer les fichiers
                    import shutil
                    shutil.copy2(json_path, target_json)
                    shutil.copy2(wav_path, target_wav)
                    shutil.copy2(txt_path, target_txt)
                    
                    # Mettre à jour le fichier JSON pour refléter le nouveau split
                    try:
                        with open(target_json, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Mettre à jour le split
                        metadata["split"] = os.path.basename(target_dir)
                        
                        with open(target_json, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"Erreur lors de la mise à jour du fichier JSON {target_json}: {e}")
            
            # Déplacer les échantillons
            move_samples(train_samples, train_dir)
            move_samples(validation_samples, validation_dir)
            move_samples(test_samples, test_dir)
            
            print(f"Split effectué pour {engine}: {len(train_samples)} train, {len(validation_samples)} validation, {len(test_samples)} test")
        
        # Régénérer le dataset Hugging Face
        generate_huggingface_dataset()
        
        return True
    except Exception as e:
        print(f"Erreur lors de la répartition du dataset: {e}")
        return False

# Variables globales pour la gestion de la reconnaissance vocale
_recognizer = None
_microphone = None
_command_processor = None
_stop_listening_func = None


def arreter_threads_reconnaissance():
    """Arrête tous les threads de reconnaissance vocale"""
    global active_threads, audio_queue, vosk_running, vosk_thread, whisper_ct2_running, whisper_ct2_thread, whisper_french_running, whisper_french_thread, _stop_listening_func, _recognizer, _microphone
    
    # Arrêter la fonction d'écoute si elle existe
    if _stop_listening_func:
        try:
            _stop_listening_func(wait_for_stop=False)
            _stop_listening_func = None
        except Exception:
            pass
    
    # Arrêter Vosk si actif
    vosk_running = False
    
    # Arrêter Whisper CT2 si actif
    whisper_ct2_running = False
    
    # Arrêter Whisper French si actif
    whisper_french_running = False
    
    # Arrêter Whisper si actif (en modifiant les variables de contrôle des threads Whisper)
    for t in threading.enumerate():
        if t.name == "whisper_processing_thread":
            try:
                frame = sys._current_frames().get(t.ident)
                if frame and 'whisper_running' in frame.f_locals:
                    frame.f_locals['whisper_running'][0] = False
            except Exception:
                pass
    
    # Vider la file d'attente sans attendre
    try:
        while not audio_queue.empty():
            audio_queue.get_nowait()
            audio_queue.task_done()
    except:
        pass
    
    # Fermer le microphone s'il est ouvert
    if _microphone and hasattr(_microphone, 'stream') and _microphone.stream is not None:
        try:
            _microphone.stream.close()
        except Exception:
            pass
    
    # Vider la liste des threads sans attendre leur terminaison
    active_threads.clear()
    
    # Réinitialiser le thread Vosk
    if vosk_thread is not None:
        vosk_thread = None
def start_whisper_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue avec OpenAI Whisper API"""
    global active_threads
    
    # Variable pour contrôler l'exécution du thread
    # Utiliser une liste pour pouvoir la modifier depuis l'extérieur
    whisper_running = [True]
    
    # Créer un nouveau microphone pour éviter les problèmes de context manager
    try:
        # Fermer le microphone existant s'il est ouvert
        if hasattr(microphone, 'stream') and microphone.stream is not None:
            microphone.stream.close()
        
        # Créer un nouveau microphone avec le taux d'échantillonnage approprié
        new_microphone = sr.Microphone(sample_rate=WHISPER_SAMPLE_RATE)
    except Exception as e:
        print(f"Erreur lors de la création d'un nouveau microphone: {e}")
        new_microphone = microphone  # Utiliser l'ancien microphone en cas d'erreur
    
    # Thread de traitement audio en continu avec Whisper
    def whisper_processing_thread():
        print("Thread de traitement audio Whisper API démarré")
        
        # Ouvrir le flux audio avec le nouveau microphone
        with new_microphone as source:
            try:
                # Ajuster pour le bruit ambiant
                print("Calibrage du microphone pour Whisper...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Créer un stream audio
                audio_stream = source.stream
                
                # Variables pour le traitement en continu
                audio_buffer = []
                silence_counter = 0
                is_speaking = False
                
                # Stocker la référence à whisper_running dans une variable locale
                # pour que les autres threads puissent la modifier
                nonlocal whisper_running
                
                while whisper_running[0] and get_running():
                    # Vérifier si le moteur STT actuel est toujours Whisper
                    if get_stt_engine() != "whisper":
                        print("Moteur STT changé, arrêt du thread Whisper")
                        break
                    try:
                        # Lire un chunk audio
                        audio_chunk = audio_stream.read(WHISPER_CHUNK_SIZE)
                        
                        # Convertir en tableau d'octets pour analyse
                        audio_data = sr.AudioData(
                            audio_chunk,
                            WHISPER_SAMPLE_RATE,
                            2  # Nombre d'octets par échantillon
                        )
                        
                        # Calculer l'énergie du signal (méthode améliorée)
                        # Convertir les bytes en valeurs numériques
                        audio_values = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)
                        # Calculer l'énergie RMS
                        energy = np.sqrt(np.mean(audio_values**2)) / 32768.0
                        
                        # Détecter si l'utilisateur parle (avec moins de logs)
                        if energy > stt_settings["whisper_silence_threshold"]:
                            # Seulement afficher si c'est le début de la parole
                            if not is_speaking:
                                print(f"Parole détectée (Whisper) - Énergie: {energy:.6f}")
                            silence_counter = 0
                            is_speaking = True
                        else:
                            silence_counter += 1
                        
                        # Si l'utilisateur parle ou vient de parler, ajouter à la mémoire tampon
                        if is_speaking:
                            audio_buffer.append(audio_chunk)
                        
                        # Si suffisamment de silence après la parole, traiter l'audio
                        if is_speaking and silence_counter >= stt_settings["whisper_silence_chunks"]:
                            # Vérifier si l'enregistrement est assez long pour être significatif
                            audio_duration = len(audio_buffer) * WHISPER_CHUNK_SIZE / WHISPER_SAMPLE_RATE
                            
                            if len(audio_buffer) < WHISPER_MIN_SPEAKING_CHUNKS or audio_duration < WHISPER_MIN_AUDIO_DURATION:
                                print(f"Audio trop court ({audio_duration:.2f}s), minimum requis: {WHISPER_MIN_AUDIO_DURATION}s - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                            
                            # Limiter la durée maximale de l'audio
                            if audio_duration > WHISPER_MAX_AUDIO_DURATION:
                                print(f"Audio trop long ({audio_duration:.2f}s), tronqué à {WHISPER_MAX_AUDIO_DURATION}s")
                                # Calculer combien de chunks garder
                                chunks_to_keep = int(WHISPER_MAX_AUDIO_DURATION * WHISPER_SAMPLE_RATE / WHISPER_CHUNK_SIZE)
                                audio_buffer = audio_buffer[-chunks_to_keep:]
                                audio_duration = WHISPER_MAX_AUDIO_DURATION
                            
                            # Concaténer tous les chunks audio
                            full_audio = b''.join(audio_buffer)
                            
                            # Vérifier si l'audio contient des données significatives
                            audio_values = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32)
                            audio_energy = np.sqrt(np.mean(audio_values**2)) / 32768.0
                            
                            if audio_energy < WHISPER_MIN_AUDIO_ENERGY:
                                print(f"Audio trop silencieux, énergie: {audio_energy:.6f} - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                            
                            print(f"Traitement audio Whisper - Durée: {audio_duration:.2f}s, Énergie: {audio_energy:.6f}")
                            
                            # Vérifier d'abord si un résultat similaire existe dans le cache
                            cached_result = whisper_cache.get(full_audio)
                            if cached_result:
                                print("Résultat trouvé dans le cache, traitement évité")
                                # Traiter directement le résultat mis en cache
                                if command_processor.process_command(cached_result) is not None:
                                    print(f"Commande exécutée depuis le cache: {cached_result}")
                                
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                continue
                            
                            # Prétraiter l'audio pour améliorer la qualité (optimisé)
                            try:
                                # Normaliser l'audio (augmenter le volume)
                                audio_values = np.frombuffer(full_audio, dtype=np.int16).astype(np.float32)
                                
                                # Appliquer un gain plus élevé pour améliorer la détection
                                gain_factor = 1.5
                                
                                # Normalisation du volume avec gain (optimisée)
                                if np.abs(audio_values).max() > 0:
                                    # Appliquer le gain tout en évitant l'écrêtage
                                    max_value = np.abs(audio_values).max()
                                    safe_gain = min(gain_factor, 32767 / max_value)
                                    
                                    # Utiliser une opération vectorisée plus rapide
                                    normalized_audio = np.clip(audio_values * safe_gain, -32767, 32767)
                                    processed_audio = normalized_audio.astype(np.int16).tobytes()
                                else:
                                    processed_audio = full_audio
                                
                                # Réduire la verbosité pour améliorer les performances
                                if audio_duration > 1.0:  # Seulement pour les audios plus longs
                                    print(f"Audio prétraité avec succès (gain: {safe_gain:.2f})")
                            except Exception as e:
                                print(f"Erreur lors du prétraitement audio: {e}")
                                processed_audio = full_audio
                            
                            # Créer un fichier WAV temporaire dans un répertoire accessible
                            temp_dir = os.path.join(tempfile.gettempdir(), "whisp_audio")
                            os.makedirs(temp_dir, exist_ok=True)
                            temp_filename = os.path.join(temp_dir, f"whisp_audio_{int(time.time())}.wav")
                            
                            # Écrire les données audio dans le fichier WAV
                            with wave.open(temp_filename, 'wb') as wf:
                                wf.setnchannels(1)  # Mono
                                wf.setsampwidth(2)  # 16 bits
                                wf.setframerate(WHISPER_SAMPLE_RATE)
                                wf.writeframes(processed_audio)
                                
                            print(f"Fichier audio temporaire créé: {temp_filename}")
                            
                            # Traiter avec Whisper API
                            try:
                                process_whisper_audio(temp_filename, command_processor)
                            finally:
                                # Supprimer le fichier temporaire
                                try:
                                    os.unlink(temp_filename)
                                except:
                                    pass
                            
                            # Réinitialiser
                            audio_buffer = []
                            is_speaking = False
                            silence_counter = 0
                        
                    except Exception as e:
                        print(f"Erreur dans le thread Whisper: {e}")
                        if not get_running() or not whisper_running[0]:
                            break
            except Exception as e:
                print(f"Erreur lors de l'initialisation du microphone Whisper: {e}")
    
    # Démarrer le thread Whisper
    whisper_thread = threading.Thread(
        target=whisper_processing_thread,
        daemon=True,
        name="whisper_processing_thread"
    )
    whisper_thread.start()
    
    # Ajouter le thread à la liste des threads actifs
    active_threads.append(whisper_thread)
    
    # Fonction pour arrêter l'écoute
    def stop_whisper_listening():
        whisper_running[0] = False
    
    return stop_whisper_listening

def process_whisper_audio(audio_file_path, command_processor):
    """Traite l'audio avec l'API Whisper d'OpenAI"""
    api_key = get_openai_api_key()
    if not api_key:
        print("Erreur: Clé API OpenAI non configurée")
        return
    
    start_time = time.time()
    
    # Obtenir la durée de l'audio et vérifier sa qualité (optimisé)
    try:
        with wave.open(audio_file_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            audio_duration = frames / float(rate)
            
            # Vérification rapide de la durée
            if audio_duration < WHISPER_MIN_AUDIO_DURATION:
                print(f"Audio trop court: {audio_duration:.2f}s < {WHISPER_MIN_AUDIO_DURATION}s")
                return
            
            # Lecture optimisée pour vérifier l'énergie
            wf.setpos(0)
            # Lire seulement un petit échantillon pour accélérer la vérification
            sample_size = min(frames, int(rate * 0.2))  # Réduit à 0.2s
            sample_frames = wf.readframes(sample_size)
            audio_values = np.frombuffer(sample_frames, dtype=np.int16).astype(np.float32)
            sample_energy = np.sqrt(np.mean(audio_values**2)) / 32768.0
            
            if sample_energy < WHISPER_MIN_AUDIO_ENERGY:
                print(f"Énergie audio insuffisante: {sample_energy:.6f}")
                return
            
            # Lire tout le contenu du fichier pour le cache
            wf.setpos(0)
            full_audio = wf.readframes(frames)
            
            # Vérifier le cache
            cached_result = whisper_cache.get(full_audio)
            if cached_result:
                print("Résultat trouvé dans le cache, utilisation directe")
                # Simuler le temps de traitement pour les métriques
                time.sleep(0.1)
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                # Mettre à jour les métriques
                update_stt_metrics(
                    engine="whisper",
                    success=True,
                    latency=latency,
                    audio_duration=audio_duration,
                    text=cached_result
                )
                
                print(f"Vous avez dit (Whisper/cache): {cached_result} (latence: {latency:.0f}ms)")
                command_processor.process_command(cached_result)
                return
            
    except Exception as e:
        print(f"Erreur lors de la lecture audio: {e}")
        return
    
    # Fonction pour envoyer la requête API dans un thread séparé
    def send_whisper_request():
        try:
            # Préparer les en-têtes avec la clé API
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Vérifier que le fichier existe
            if not os.path.exists(audio_file_path):
                print(f"Erreur: Fichier audio {audio_file_path} introuvable")
                return None
                
            # Vérifier la taille du fichier (rapide)
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                print("Erreur: Fichier audio vide")
                return None
                
            # Préparer les données pour la requête
            with open(audio_file_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_file_path), audio_file, "audio/wav")
                }
                
                data = {
                    "model": WHISPER_MODEL,
                    "language": "fr",
                    "response_format": "json",
                    "temperature": 0.0
                }
                
                # Envoyer la requête avec un timeout réduit
                print(f"Envoi requête API Whisper ({file_size} octets)")
                response = requests.post(
                    WHISPER_API_URL,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=15  # Timeout réduit
                )
                
                return response
        except Exception as e:
            print(f"Erreur requête Whisper: {e}")
            return None
    
    # Utiliser un thread séparé ou un pool d'exécuteurs pour la requête API
    if WHISPER_PARALLEL_REQUESTS:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(send_whisper_request)
            try:
                response = future.result(timeout=20)
            except concurrent.futures.TimeoutError:
                print("Timeout lors de la requête Whisper API")
                return
    else:
        response = send_whisper_request()
    
    # Traiter la réponse
    try:
        # Vérifier si la requête a réussi
        if response and response.status_code == 200:
            result = response.json()
            texte = result.get("text", "").strip()
            
            # Nettoyer le texte (supprimer le point final et autres ponctuations qui peuvent perturber les commandes)
            try:
                from text_processing import nettoyer_commande
                texte = nettoyer_commande(texte)
            except ImportError:
                # Si impossible d'importer, supprimer manuellement le point final
                if texte.endswith(".") or texte.endswith("!") or texte.endswith("?"):
                    texte = texte[:-1].strip()
            
            # Calculer la latence
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # en millisecondes
            
            # Calculer le coût approximatif
            cost = (audio_duration / 60.0) * WHISPER_COST_PER_MINUTE
            
            # Enregistrer l'audio et le texte pour fine tuning
            save_audio_for_fine_tuning(audio_file_path, texte, "whisper")
            
            # Mettre à jour les métriques
            update_stt_metrics(
                engine="whisper",
                success=True,
                latency=latency,
                audio_duration=audio_duration,
                text=texte
            )
            
            # Ajouter le coût à la métrique
            stt_metrics["whisper"]["cost"] += cost
            
            # Traitement rapide pour les commandes de fin de dictée
            if get_dictation_mode():
                texte_lower = texte.lower().strip()
                if any(phrase in texte_lower for phrase in ["fin de dictée", "terminer dictée", "arrêter dictée"]):
                    print(f"Commande de fin détectée: {texte}")
                    return command_processor.process_command(texte)
            
            # Affichage optimisé
            print(f"Vous avez dit (Whisper): {texte} (latence: {latency:.0f}ms, durée audio: {audio_duration:.2f}s, coût: ${cost:.6f})")
            
            # Vérifications rapides
            if not texte or any(fragment in texte.lower() for fragment in ["transcris cet audio", "l'audio contient"]):
                print("Réponse invalide ignorée")
                return
                
            # Prétraitement du texte optimisé
            texte = ' '.join(texte.strip().split())  # Normaliser les espaces
            
            # Corrections rapides (optimisées)
            for char_pair in [(" ,", ","), (" .", "."), (" :", ":"), (" ?", "?"), (" !", "!"), (" ;", ";")]:
                texte = texte.replace(*char_pair)
            
            for apostrophe in ["l'", "d'", "n'", "qu'", "s'", "j'"]:
                texte = texte.replace(apostrophe.replace("'", " '"), apostrophe)
            
            # Corrections de commandes (optimisées)
            corrections = {
                "rechercher": "recherche", "recherches": "recherche", "recherché": "recherche",
                "nouvelle longlet": "nouvel onglet", "nouveau longlet": "nouvel onglet",
                "nouvelle onglet": "nouvel onglet", "nouveau onglet": "nouvel onglet",
                "merci d'avoir": "recherche", "merci d avoir": "recherche",
                "regardé cette vidéo": "sur youtube", "regarder cette vidéo": "sur youtube"
            }
            
            # Appliquer les corrections de manière optimisée
            texte_lower = texte.lower()
            correction_appliquee = False
            
            for erreur, correction in corrections.items():
                if erreur in texte_lower:
                    texte_lower = texte_lower.replace(erreur, correction)
                    correction_appliquee = True
            
            if correction_appliquee:
                texte = texte_lower
            
            # Vérification rapide pour les commandes courtes
            if len(texte.split()) < 2 and len(texte) < 10:
                commandes_courtes = ["stop", "pause", "play", "ok", "oui", "non", "suivant", "précédent",
                                    "arrête", "continue", "valide", "annule", "ferme", "ouvre", "active"]
                
                if texte.lower() not in commandes_courtes and not any(mot in texte.lower() for mot in 
                                                                    ["recherche", "cherche", "trouve", "nouvel", "nouveau"]):
                    print(f"Réponse trop courte ignorée: '{texte}'")
                    return
            
            # Ajouter au cache pour les futures requêtes
            with wave.open(audio_file_path, 'rb') as wf:
                full_audio = wf.readframes(wf.getnframes())
                whisper_cache.set(full_audio, texte)
            
            # Exécution de la commande
            resultat = command_processor.process_command(texte)
            print(f"Résultat : {resultat}")
        else:
            # Mettre à jour les métriques en cas d'erreur
            update_stt_metrics(
                engine="whisper",
                success=False,
                audio_duration=audio_duration
            )
            
            error_message = f"Erreur API Whisper: {response.status_code} - {response.text}" if response else "Pas de réponse de l'API Whisper"
            print(error_message)
            
            # Afficher plus de détails pour le débogage
            print(f"Détails de la requête: URL={WHISPER_API_URL}, Modèle={WHISPER_MODEL}, Durée audio={audio_duration:.2f}s")
            
            # Vérifier si c'est une erreur d'authentification
            if response and response.status_code == 401:
                print("Erreur d'authentification - Vérifiez votre clé API OpenAI")
                # Vérifier si la clé API est correctement formatée
                api_key_prefix = api_key[:4] + "..." if len(api_key) > 4 else ""
                print(f"Préfixe de la clé API: {api_key_prefix}")
                print("La clé API doit commencer par 'sk-' et avoir une longueur d'environ 51 caractères")
            elif response and response.status_code == 400:
                print("Erreur de requête - Vérifiez le format de l'audio")
                # Essayer de diagnostiquer le problème avec le fichier audio
                try:
                    with wave.open(audio_file_path, 'rb') as wf:
                        print(f"Détails du fichier audio: canaux={wf.getnchannels()}, "
                              f"largeur={wf.getsampwidth()}, "
                              f"taux={wf.getframerate()}, "
                              f"frames={wf.getnframes()}")
                except Exception as e:
                    print(f"Impossible d'analyser le fichier audio: {e}")
            elif response and response.status_code == 429:
                print("Limite de requêtes atteinte - Attendez avant de réessayer")
            elif response and response.status_code >= 500:
                print("Erreur serveur OpenAI - Réessayez plus tard")
    except Exception as e:
        # Mettre à jour les métriques en cas d'erreur
        update_stt_metrics(
            engine="whisper",
            success=False,
            audio_duration=audio_duration
        )
        print(f"Erreur lors du traitement audio Whisper: {e}")

def start_vosk_listening(recognizer, microphone, command_processor):
    """Démarre l'écoute continue avec Vosk"""
    global active_threads, vosk_model, vosk_running, vosk_thread
    
    print("Démarrage de l'écoute Vosk...")
    
    # S'assurer que tous les autres threads sont arrêtés
    arreter_threads_reconnaissance()
    
    # Attendre un court instant pour s'assurer que tous les threads sont arrêtés
    time.sleep(0.5)
    
    # Vérifier si le modèle Vosk est chargé
    if vosk_model is None:
        print("Erreur: Le modèle Vosk n'est pas chargé, tentative de chargement...")
        if not setup_vosk_model():
            error_msg = "Échec du chargement du modèle Vosk, utilisation de SpeechRecognition comme solution de repli"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            set_stt_engine("speechrecognition")
            return start_speechrecognition_listening(recognizer, microphone, command_processor)
        else:
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web("Modèle Vosk chargé avec succès", "info")
            print("Modèle Vosk chargé avec succès")
    
    # Arrêter le thread Vosk s'il est déjà en cours d'exécution
    if vosk_thread is not None and vosk_thread.is_alive():
        print("Arrêt du thread Vosk existant...")
        vosk_running = False
        vosk_thread.join(timeout=1.0)
    
    # Variable pour contrôler l'exécution du thread
    vosk_running = True
    
    # Créer un nouveau microphone pour éviter les problèmes de context manager
    # Essayer d'abord l'alternative sounddevice (pour Windows ARM64)
    new_microphone = create_microphone_alternative(sample_rate=VOSK_SAMPLE_RATE)

    if new_microphone is None:
        # Fallback sur PyAudio si sounddevice n'est pas disponible
        try:
            # Fermer le microphone existant s'il est ouvert
            if hasattr(microphone, 'stream') and microphone.stream is not None:
                microphone.stream.close()

            # Créer un nouveau microphone avec le taux d'échantillonnage approprié
            new_microphone = sr.Microphone(sample_rate=VOSK_SAMPLE_RATE)
            print("Utilisation de PyAudio pour Vosk")
        except Exception as e:
            print(f"Erreur lors de la création d'un nouveau microphone PyAudio: {e}")
            print("Impossible de créer un microphone - Vosk ne fonctionnera pas")
            new_microphone = None

    if new_microphone is None:
        error_msg = "Impossible de créer un microphone audio (ni sounddevice ni PyAudio disponibles)"
        print(error_msg)
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(error_msg, "error")
        return
    
    # Thread de traitement audio en continu avec Vosk
    def vosk_processing_thread():
        print("Thread de traitement audio Vosk démarré")
        
        # Ouvrir le flux audio avec le nouveau microphone
        with new_microphone as source:
            try:
                # Ajuster pour le bruit ambiant (seulement si on utilise un vrai sr.Microphone)
                print("Calibrage du microphone pour Vosk...")
                try:
                    # Cette étape fonctionne seulement avec PyAudio/sr.Microphone
                    if hasattr(source, 'stream') and hasattr(source.stream, 'read'):
                        recognizer.adjust_for_ambient_noise(source, duration=1)
                    else:
                        print("Microphone alternatif détecté, saut du calibrage du bruit ambiant")
                except Exception as e:
                    print(f"Calibrage du bruit ambiant non possible: {e}")
                    print("Continuation sans calibrage...")

                # Créer un stream audio
                # Gérer les deux cas: sr.Microphone (PyAudio) et AlternativeMicrophone (sounddevice)
                if hasattr(source, '__class__') and 'AlternativeMicrophone' in str(source.__class__):
                    # Cas sounddevice: le flux est déjà dans source.stream
                    audio_stream = source.stream
                    print("Utilisation du flux audio sounddevice")
                else:
                    # Cas PyAudio standard
                    audio_stream = source.stream
                    print("Utilisation du flux audio PyAudio")

                # Créer un recognizer Vosk
                try:
                    vosk_rec = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)
                    print("KaldiRecognizer créé avec succès")
                except Exception as e:
                    error_msg = f"Erreur lors de la création du KaldiRecognizer: {e}"
                    print(error_msg)
                    if 'web_interface' in sys.modules:
                        from web_interface import log_to_web
                        log_to_web(error_msg, "error")
                    return
                
                # Variables pour le traitement en continu
                audio_buffer = []
                silence_counter = 0
                is_speaking = False
                
                while vosk_running and get_running():
                    # Vérifier si le moteur STT actuel est toujours Vosk
                    if get_stt_engine() != "vosk":
                        print("Moteur STT changé, arrêt du thread Vosk")
                        break
                        
                    try:
                        # Lire un chunk audio
                        audio_chunk = audio_stream.read(VOSK_CHUNK_SIZE)

                        # Debug: montrer que la boucle continue (une fois par seconde environ)
                        if hasattr(start_vosk_listening, '_debug_counter'):
                            start_vosk_listening._debug_counter += 1
                        else:
                            start_vosk_listening._debug_counter = 1

                        if start_vosk_listening._debug_counter % 100 == 0:  # Tous les ~100 chunks
                            print(f"Vosk: Boucle d'écoute active (chunk #{start_vosk_listening._debug_counter})")
                            # Debug audio info
                            print(f"Vosk Debug: Taille chunk={len(audio_chunk)} bytes, Type={type(audio_chunk)}")

                        # Convertir en numpy array pour analyse d'énergie
                        audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32)

                        # Normaliser correctement les données audio (int16 → float32 [-1.0, 1.0])
                        audio_data = audio_data / 32768.0

                        # Debug: vérifier les données audio une fois par seconde
                        if start_vosk_listening._debug_counter % 100 == 0:
                            print(f"Vosk Debug: Audio shape={audio_data.shape}, Min={audio_data.min():.4f}, Max={audio_data.max():.4f}")

                        # Calculer l'énergie du signal (maintenant sur données normalisées)
                        energy = np.sqrt(np.mean(audio_data**2))
                        threshold = stt_settings["vosk_silence_threshold"]

                        # Debug: afficher l'énergie périodiquement (tous les 50 chunks)
                        if start_vosk_listening._debug_counter % 50 == 0:
                            print(f"Vosk Debug: Énergie={energy:.6f}, Seuil={threshold:.6f}, Speaking={is_speaking}")

                        # Détecter si l'utilisateur parle
                        if energy > threshold:
                            if not is_speaking:
                                print(f"Parole détectée (Vosk) - Énergie: {energy:.6f} > Seuil: {threshold:.6f}")
                            silence_counter = 0
                            is_speaking = True
                        else:
                            if is_speaking and start_vosk_listening._debug_counter % 50 == 0:
                                print(f"Silence détecté - Énergie: {energy:.6f} <= Seuil: {threshold:.6f}")
                            silence_counter += 1
                        
                        # Si l'utilisateur parle ou vient de parler, ajouter à la mémoire tampon
                        if is_speaking:
                            audio_buffer.append(audio_chunk)
                            
                            # Traiter le chunk avec Vosk en temps réel
                            if vosk_rec.AcceptWaveform(audio_chunk):
                                # Récupérer le résultat partiel
                                result_json = vosk_rec.Result()
                                result = json.loads(result_json)
                                
                                if "text" in result and result["text"].strip():
                                    texte = result["text"].strip()
                                    
                                    # Calculer la durée audio
                                    audio_duration = len(audio_buffer) * VOSK_CHUNK_SIZE / VOSK_SAMPLE_RATE
                                    
                                    # Traiter le texte reconnu
                                    print(f"Vosk: Traitement du texte reconnu: '{texte}'")
                                    process_vosk_result(texte, audio_duration, command_processor)

                                    # Réinitialiser pour continuer l'écoute
                                    print("Vosk: Réinitialisation pour continuer l'écoute...")
                                    audio_buffer = []
                                    is_speaking = False
                                    silence_counter = 0
                                    try:
                                        vosk_rec = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)
                                        print("Vosk: Nouveau recognizer créé, écoute continue...")
                                    except Exception as e:
                                        print(f"Vosk: Erreur lors de la création du nouveau recognizer: {e}")
                                        break
                        
                        # Si suffisamment de silence après la parole, traiter l'audio accumulé
                        if is_speaking and silence_counter >= stt_settings["vosk_silence_chunks"]:
                            # Vérifier si l'enregistrement est assez long pour être significatif
                            audio_duration = len(audio_buffer) * VOSK_CHUNK_SIZE / VOSK_SAMPLE_RATE
                            
                            if len(audio_buffer) < VOSK_MIN_SPEAKING_CHUNKS or audio_duration < VOSK_MIN_AUDIO_DURATION:
                                print(f"Audio trop court ({audio_duration:.2f}s), minimum requis: {VOSK_MIN_AUDIO_DURATION}s - Ignoré")
                                # Réinitialiser
                                audio_buffer = []
                                is_speaking = False
                                silence_counter = 0
                                vosk_rec = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)
                                continue
                            
                            # Marquer le temps de début du traitement
                            process_start_time = time.time()
                            
                            # Récupérer le résultat final
                            result_json = vosk_rec.FinalResult()
                            result = json.loads(result_json)
                            
                            if "text" in result and result["text"].strip():
                                texte = result["text"].strip()
                                
                                # Nettoyer le texte (supprimer le point final et autres ponctuations qui peuvent perturber les commandes)
                                try:
                                    from text_processing import nettoyer_commande
                                    texte = nettoyer_commande(texte)
                                except ImportError:
                                    # Si impossible d'importer, supprimer manuellement le point final
                                    if texte.endswith(".") or texte.endswith("!") or texte.endswith("?"):
                                        texte = texte[:-1].strip()
                                
                                # Calculer le temps de traitement réel
                                process_end_time = time.time()
                                process_latency = (process_end_time - process_start_time) * 1000  # en millisecondes
                                
                                # Concaténer tous les chunks audio
                                full_audio = b''.join(audio_buffer)
                                
                                # Enregistrer l'audio et le texte pour fine tuning
                                save_audio_for_fine_tuning(full_audio, texte, "vosk", sample_rate=VOSK_SAMPLE_RATE)
                                
                                # Traiter le texte reconnu avec la latence réelle
                                print(f"Vosk: Traitement du texte final: '{texte}'")
                                process_vosk_result(texte, audio_duration, command_processor)

                            # Réinitialiser pour continuer l'écoute
                            print("Vosk: Réinitialisation finale pour continuer l'écoute...")
                            audio_buffer = []
                            is_speaking = False
                            silence_counter = 0
                            try:
                                vosk_rec = KaldiRecognizer(vosk_model, VOSK_SAMPLE_RATE)
                                print("Vosk: Nouveau recognizer final créé, écoute continue...")
                            except Exception as e:
                                print(f"Vosk: Erreur lors de la création du recognizer final: {e}")
                                break
                            
                    except Exception as e:
                        print(f"Erreur dans le thread Vosk: {e}")
                        if not get_running() or not vosk_running:
                            break
            except Exception as e:
                print(f"Erreur lors de l'initialisation du microphone Vosk: {e}")
    
    # Démarrer le thread Vosk
    vosk_thread = threading.Thread(
        target=vosk_processing_thread,
        daemon=True,
        name="vosk_processing_thread"
    )
    vosk_thread.start()
    
    # Ajouter le thread à la liste des threads actifs
    active_threads.append(vosk_thread)
    
    # Fonction pour arrêter l'écoute
    def stop_vosk_listening():
        global vosk_running
        vosk_running = False
    
    return stop_vosk_listening

def process_vosk_result(texte, audio_duration, command_processor):
    """Traite le résultat de la reconnaissance Vosk"""
    # Enregistrer le temps de début pour calculer la latence réelle
    start_time = time.time()
    
    # Vérifier si le texte est vide
    if not texte or len(texte.strip()) == 0:
        return
    
    # Nettoyer le texte (supprimer le point final et autres ponctuations qui peuvent perturber les commandes)
    try:
        from text_processing import nettoyer_commande
        texte = nettoyer_commande(texte)
    except ImportError:
        # Si impossible d'importer, supprimer manuellement le point final
        if texte.endswith(".") or texte.endswith("!") or texte.endswith("?"):
            texte = texte[:-1].strip()
    
    # Simuler un temps de traitement plus réaliste pour Vosk
    # La latence réelle inclut le temps de traitement audio qui a déjà eu lieu
    # On ajoute donc un temps proportionnel à la durée audio
    processing_time = audio_duration * 50  # ~50ms par seconde d'audio
    
    # Calculer la latence (temps de traitement + temps simulé)
    end_time = time.time()
    latency = (end_time - start_time) * 1000 + processing_time  # en millisecondes
    
    # Mettre à jour les métriques avec des valeurs plus réalistes
    update_stt_metrics(
        engine="vosk",
        success=True,
        latency=max(latency, 100),  # Assurer une latence minimale de 100ms pour éviter les 0ms
        audio_duration=audio_duration,
        text=texte
    )
    
    # Note: Pour Vosk, nous n'avons pas d'accès direct aux données audio à cet endroit
    # L'enregistrement pour le fine tuning sera fait dans le thread de traitement
    
    # Vérification spécifique pour les commandes de fin de dictée
    if get_dictation_mode():
        texte_lower = texte.lower().strip()
        phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                        "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
        
        if texte_lower in phrases_arret:
            print(f"Commande de fin détectée: {texte}")
            return command_processor.process_command(texte)
    
    # Affichage différent selon le mode
    if get_dictation_mode():
        print(f"Dictée (Vosk): {texte}")
    else:
        print(f"Vous avez dit (Vosk): {texte} (latence: {latency:.0f}ms, durée audio: {audio_duration:.2f}s)")
    
    # Exécution de la commande via le processeur de commandes
    resultat = command_processor.process_command(texte)
    print(f"Résultat : {resultat}")

@catch_errors(category=ErrorCategory.SPEECH_RECOGNITION, severity=ErrorSeverity.HIGH, notify_user=True)
def redemarrer_reconnaissance_vocale(command_processor=None):
    """Redémarre la reconnaissance vocale avec le moteur actuellement configuré"""
    global _recognizer, _microphone, _command_processor, vosk_model, whisper_ct2_model, whisper_french_model, _stop_listening_func
    
    # Si un processeur de commandes est fourni, le sauvegarder
    if command_processor is not None:
        _command_processor = command_processor
    
    # Vérifier que nous avons les références nécessaires
    if not _command_processor:
        # Tenter de récupérer le processeur de commandes
        try:
            # Essayer d'abord de l'obtenir depuis main
            try:
                import main
                if hasattr(main, 'command_processor'):
                    _command_processor = main.command_processor
                    print("Processeur de commandes récupéré depuis main.py")
                else:
                    # Créer une nouvelle instance
                    from command_processor import CommandProcessor
                    _command_processor = CommandProcessor()
                    print("Nouvelle instance du processeur de commandes créée")
            except (ImportError, AttributeError) as e:
                print(f"Impossible d'importer depuis main: {e}")
                # Créer une nouvelle instance
                from command_processor import CommandProcessor
                _command_processor = CommandProcessor()
                print("Nouvelle instance du processeur de commandes créée (fallback)")
        except Exception as e:
            error_msg = f"Impossible de récupérer ou créer un processeur de commandes: {str(e)}"
            print(error_msg)
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web(error_msg, "error")
            
            error_handler.handle_error(
                error_msg,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.HIGH,
                context={"action": "redémarrage", "missing": "command_processor"}
            )
            return False
    
    # Si le recognizer ou le microphone sont manquants, les recréer
    if not _recognizer or not _microphone:
        print("Recréation du recognizer et/ou du microphone manquants")
        try:
            _recognizer = sr.Recognizer() if not _recognizer else _recognizer
            if not _microphone:
                # Utiliser le microphone alternative par défaut (compatible ARM64)
                _microphone = create_microphone_alternative()
                if _microphone is None:
                    # Fallback sur PyAudio si sounddevice n'est pas disponible
                    print("sounddevice non disponible, fallback sur PyAudio")
                    _microphone = sr.Microphone()
        except Exception as e:
            error_msg = f"Erreur lors de la recréation du recognizer/microphone: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.HIGH,
                context={"action": "recréation des composants"}
            )
            return False
    
    # Arrêter proprement les threads existants
    print("Arrêt complet de tous les threads avant redémarrage...")
    try:
        arreter_threads_reconnaissance()
    except Exception as e:
        error_msg = f"Erreur lors de l'arrêt des threads: {str(e)}"
        print(error_msg)
        error_handler.handle_error(
            e,
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.MEDIUM,
            context={"action": "arrêt des threads"}
        )
        # Continuer malgré l'erreur
    
    # Attendre un court instant pour s'assurer que tous les threads sont arrêtés
    time.sleep(0.5)
    print("Préparation du redémarrage de la reconnaissance vocale...")
    
    # Créer un nouveau recognizer pour éviter les problèmes
    try:
        new_recognizer = sr.Recognizer()
        new_recognizer.pause_threshold = stt_settings["pause_threshold"]
        new_recognizer.energy_threshold = stt_settings["energy_threshold"]
        new_recognizer.dynamic_energy_threshold = True
        new_recognizer.dynamic_energy_adjustment_damping = 0.15
        new_recognizer.dynamic_energy_ratio = 1.5
        new_recognizer.non_speaking_duration = stt_settings["non_speaking_duration"]
    except Exception as e:
        error_msg = f"Erreur lors de la création du nouveau recognizer: {str(e)}"
        print(error_msg)
        error_handler.handle_error(
            e,
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.HIGH,
            context={"action": "création du recognizer"}
        )
        return False
    
    # Créer un nouveau microphone
    try:
        stt_engine = get_stt_engine()
        print(f"Redémarrage avec le moteur STT: {stt_engine}")

        # NeMo n'est plus supporté, cette condition ne sera jamais vraie
        if stt_engine == "nemo":
            print("NVIDIA NeMo n'est plus supporté, utilisation du microphone par défaut")
            new_microphone = sr.Microphone()
        elif stt_engine == "whisper":
            new_microphone = sr.Microphone(sample_rate=WHISPER_SAMPLE_RATE)
        elif stt_engine == "vosk" and VOSK_AVAILABLE:
            # Utiliser le microphone alternative avec sounddevice pour Vosk (compatible ARM64)
            print("Utilisation du microphone sounddevice pour Vosk")
            new_microphone = create_microphone_alternative(sample_rate=VOSK_SAMPLE_RATE)
            if new_microphone is None:
                # Fallback sur PyAudio si sounddevice n'est pas disponible
                print("sounddevice non disponible, fallback sur PyAudio pour Vosk")
                new_microphone = sr.Microphone(sample_rate=VOSK_SAMPLE_RATE)
        else:
            new_microphone = sr.Microphone()
    except Exception as e:
        error_msg = f"Erreur lors de la création d'un nouveau microphone: {str(e)}"
        print(error_msg)
        error_handler.handle_error(
            e,
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.HIGH,
            context={"action": "création du microphone", "engine": get_stt_engine()}
        )
        
        # Essayer de réutiliser l'ancien microphone
        print("Tentative de réutilisation de l'ancien microphone")
        new_microphone = _microphone
    
    # Mettre à jour les références globales
    _recognizer = new_recognizer
    _microphone = new_microphone
    
    # Si on utilise Vosk, s'assurer que le modèle est chargé
    if get_stt_engine() == "vosk" and VOSK_AVAILABLE:
        # Forcer le rechargement du modèle Vosk
        try:
            print("Préchargement du modèle Vosk avant redémarrage...")
            if not setup_vosk_model():
                error_msg = "Échec du chargement du modèle Vosk, utilisation de SpeechRecognition comme solution de repli"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.SPEECH_RECOGNITION,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "chargement du modèle Vosk"}
                )
                set_stt_engine("speechrecognition")
        except Exception as e:
            error_msg = f"Erreur lors du préchargement du modèle Vosk: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.MEDIUM,
                context={"action": "préchargement du modèle Vosk"}
            )
            print("Utilisation de SpeechRecognition comme solution de repli")
            set_stt_engine("speechrecognition")
    
    # Si on utilise Whisper CT2 ou Whisper French, s'assurer que le modèle est chargé
    current_engine = get_stt_engine()
    if current_engine == "whisper_ct2" and WHISPER_CT2_AVAILABLE:
        # Forcer le rechargement du modèle Whisper CT2
        try:
            print("Préchargement du modèle Whisper CT2 avant redémarrage...")
            if not setup_whisper_ct2_model():
                error_msg = "Échec du chargement du modèle Whisper CT2, utilisation de SpeechRecognition comme solution de repli"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.SPEECH_RECOGNITION,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "chargement du modèle Whisper CT2"}
                )
                set_stt_engine("speechrecognition")
        except Exception as e:
            error_msg = f"Erreur lors du préchargement du modèle Whisper CT2: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.MEDIUM,
                context={"action": "préchargement du modèle Whisper CT2"}
            )
            print("Utilisation de SpeechRecognition comme solution de repli")
            set_stt_engine("speechrecognition")
    elif current_engine == "whisper_french" and WHISPER_CT2_AVAILABLE:
        # Forcer le rechargement du modèle Whisper French
        try:
            print("Préchargement du modèle Whisper French avant redémarrage...")
            if not setup_whisper_french_model():
                error_msg = "Échec du chargement du modèle Whisper French, utilisation de SpeechRecognition comme solution de repli"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.SPEECH_RECOGNITION,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "chargement du modèle Whisper French"}
                )
                set_stt_engine("speechrecognition")
        except Exception as e:
            error_msg = f"Erreur lors du préchargement du modèle Whisper French: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.MEDIUM,
                context={"action": "préchargement du modèle Whisper French"}
            )
            print("Utilisation de SpeechRecognition comme solution de repli")
            set_stt_engine("speechrecognition")
    
    # Redémarrer la reconnaissance vocale
    try:
        print("Redémarrage de la reconnaissance vocale...")
        print(f"État actuel: command_processor={'disponible' if _command_processor else 'manquant'}, "
              f"recognizer={'disponible' if _recognizer else 'manquant'}, "
              f"microphone={'disponible' if _microphone else 'manquant'}")
        
        # Vérifier le moteur actuel
        current_engine = get_stt_engine()
        print(f"Moteur STT actuel avant redémarrage: {current_engine}")
        
        # Démarrer l'écoute avec le moteur approprié
        try:
            if current_engine == "vosk" and VOSK_AVAILABLE:
                print("Démarrage direct de l'écoute avec Vosk...")
                _stop_listening_func = start_vosk_listening(new_recognizer, new_microphone, _command_processor)
            elif current_engine == "whisper":
                print("Démarrage direct de l'écoute avec Whisper...")
                _stop_listening_func = start_whisper_listening(new_recognizer, new_microphone, _command_processor)
            elif current_engine == "whisper_ct2" and WHISPER_CT2_AVAILABLE:
                print("Démarrage direct de l'écoute avec Whisper CT2...")
                # S'assurer que le modèle est chargé avant de démarrer l'écoute
                if whisper_ct2_model is None:
                    print("Chargement du modèle Whisper CT2 avant démarrage...")
                    setup_whisper_ct2_model()
                _stop_listening_func = start_whisper_ct2_listening(new_recognizer, new_microphone, _command_processor)
            elif current_engine == "whisper_french" and WHISPER_CT2_AVAILABLE:
                print("Démarrage direct de l'écoute avec Whisper French...")
                # S'assurer que le modèle est chargé avant de démarrer l'écoute
                if whisper_french_model is None:
                    print("Chargement du modèle Whisper French avant démarrage...")
                    setup_whisper_french_model()
                _stop_listening_func = start_whisper_french_listening(new_recognizer, new_microphone, _command_processor)
            else:
                print("Démarrage de l'écoute via start_continuous_listening...")
                _stop_listening_func = start_continuous_listening(new_recognizer, new_microphone, _command_processor)
        except Exception as e:
            error_msg = f"Erreur lors du démarrage de l'écoute avec {current_engine}: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.SPEECH_RECOGNITION,
                severity=ErrorSeverity.HIGH,
                context={"action": "démarrage de l'écoute", "engine": current_engine}
            )
            
            print("Tentative de repli sur SpeechRecognition...")
            set_stt_engine("speechrecognition")
            _stop_listening_func = start_speechrecognition_listening(new_recognizer, new_microphone, _command_processor)
        
        # Vérifier que le moteur a bien été changé
        current_engine = get_stt_engine()
        success_msg = f"Reconnaissance vocale redémarrée avec le moteur: {current_engine}"
        print(success_msg)
        
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(success_msg, "info")
        
        return True
    except Exception as e:
        error_msg = f"Erreur critique lors du redémarrage de la reconnaissance vocale: {str(e)}"
        print(error_msg)
        
        error_handler.handle_error(
            e,
            category=ErrorCategory.SPEECH_RECOGNITION,
            severity=ErrorSeverity.CRITICAL,
            context={"action": "redémarrage de la reconnaissance vocale"}
        )
        
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(f"Erreur lors du redémarrage de la reconnaissance vocale: {str(e)}", "error")
        
        # Tentative de récupération d'urgence
        try:
            print("Tentative de récupération d'urgence...")
            set_stt_engine("speechrecognition")
            _recognizer = sr.Recognizer()
            _microphone = sr.Microphone()
            _stop_listening_func = start_speechrecognition_listening(_recognizer, _microphone, _command_processor)
            
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web("Récupération d'urgence effectuée avec SpeechRecognition", "warning")
            
            return True
        except:
            if 'web_interface' in sys.modules:
                from web_interface import log_to_web
                log_to_web("Échec de la récupération d'urgence. Redémarrez l'application.", "error")
            
            return False
