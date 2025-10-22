"""
Module pour la synthèse vocale (Text-to-Speech) utilisant pyttsx3 et gTTS
"""

import threading
import queue
import time
import os
import tempfile
import re
import sys
from os_detection import get_os_type, is_windows, is_mac, is_linux
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

# Importations conditionnelles selon l'OS - chargées à la demande
pyttsx3 = None
gTTS = None
pygame = None
pygame_initialized = False

# Fonction pour importer les modules à la demande
def import_tts_modules():
    global pyttsx3, gTTS, pygame, pygame_initialized
    
    # Importer pyttsx3 si nécessaire
    if pyttsx3 is None:
        try:
            import pyttsx3 as pyttsx3_module
            pyttsx3 = pyttsx3_module
            print("Module pyttsx3 importé avec succès")
        except ImportError:
            print("Module pyttsx3 non disponible")
    
    # Importer gTTS et pygame si nécessaires
    if gTTS is None or pygame is None:
        try:
            from gtts import gTTS as gtts_module
            gTTS = gtts_module
            print("Module gTTS importé avec succès")
            
            import pygame as pygame_module
            pygame = pygame_module
            try:
                pygame.mixer.init()
                pygame_initialized = True
                print("Module pygame initialisé avec succès")
            except Exception as pygame_error:
                print(f"Erreur lors de l'initialisation de pygame: {pygame_error}")
                pygame_initialized = False
        except ImportError as e:
            print(f"Erreur d'importation des modules TTS: {e}")

# Fonction pour vérifier et réinitialiser pygame si nécessaire
def ensure_pygame_initialized():
    global pygame_initialized, pygame
    
    # Importer pygame à la demande s'il n'est pas déjà importé
    if pygame is None:
        try:
            import pygame as pygame_module
            pygame = pygame_module
        except ImportError:
            print("Module pygame non disponible")
            return False
    
    if not pygame_initialized:
        try:
            # Fermer proprement pygame avant de le réinitialiser
            try:
                pygame.mixer.quit()
                pygame.quit()
            except:
                pass
                
            # Réinitialiser pygame avec gestion d'erreur
            pygame.init()
            pygame.mixer.init(frequency=44100, buffer=1024)
            pygame_initialized = True
            print("Pygame réinitialisé avec succès")
            return True
        except Exception as e:
            print(f"Échec de la réinitialisation de pygame: {e}")
            pygame_initialized = False
            return False
    
    # Vérifier si le mixer est initialisé
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, buffer=1024)
            print("Mixer pygame réinitialisé")
        return True
    except Exception as e:
        try:
            # Tentative de réinitialisation complète
            pygame.mixer.quit()
            time.sleep(0.1)  # Petit délai pour laisser les ressources se libérer
            pygame.mixer.init(frequency=44100, buffer=1024)
            print("Mixer pygame réinitialisé après erreur")
            return True
        except Exception as e:
            print(f"Échec de la réinitialisation du mixer pygame: {e}")
            pygame_initialized = False
            return False
    
# Liste des modèles Coqui disponibles
COQUI_MODELS = [
    {"id": "vits-fr", "name": "tts_models/fr/css10/vits", "description": "VITS français (haute qualité)"},
    {"id": "glow-tts-fr", "name": "tts_models/fr/css10/glow-tts", "description": "GlowTTS français (rapide et stable)", "model_name": "glow_tts"},
    {"id": "tacotron2-fr", "name": "tts_models/fr/mai/tacotron2-DDC", "description": "Tacotron2 français (classique)"},
    {"id": "glow-tts-en", "name": "tts_models/en/ljspeech/glow-tts", "description": "GlowTTS anglais (solution de repli)", "model_name": "glow_tts"}
]

# Modèle par défaut
DEFAULT_COQUI_MODEL_ID = "vits-fr"

# Import du module warnings pour la gestion des avertissements
import warnings

# Variables pour Coqui TTS
coqui_available = False
coqui_model = None
coqui_vocoder = None
coqui_model_name = ""
coqui_model_id = DEFAULT_COQUI_MODEL_ID
TTS_API = None  # Renommé pour éviter le conflit avec la déclaration global

# Fonction pour importer Coqui TTS à la demande
def import_coqui_tts():
    global coqui_available, coqui_model, TTS_API, coqui_model_id
    
    if TTS_API is not None:
        return coqui_available
    
    try:
        # Configurer l'environnement avant d'importer torch et numpy
        import os
        import sys
        
        # Désactiver les messages de débogage
        os.environ['PYTORCH_JIT_LOG_LEVEL'] = 'WARNING'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # Correction pour le problème de distutils.ccompiler
        # Patch pour éviter l'erreur d'importation de compiler_class
        import importlib.util
        if importlib.util.find_spec("setuptools"):
            import setuptools._distutils.ccompiler
            sys.modules["distutils.ccompiler"] = setuptools._distutils.ccompiler
        
        # Importer TTS avec gestion des avertissements
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            from TTS.api import TTS as CoquiTTS
            TTS_API = CoquiTTS
        
        coqui_available = True
        print("Module CoquiTTS importé avec succès")
        return True
    except ImportError as e:
        coqui_available = False
        print(f"Module CoquiTTS non disponible: {e}")
        print("Utilisez 'pip install TTS' pour installer CoquiTTS.")
        return False
    except Exception as e:
        coqui_available = False
        print(f"Erreur lors de l'initialisation des modules pour CoquiTTS: {e}")
        return False

# Fonctions pour gérer les modèles Coqui
def get_coqui_models():
    """Retourne la liste des modèles Coqui disponibles"""
    return COQUI_MODELS

def get_current_coqui_model():
    """Retourne l'ID du modèle Coqui actuellement utilisé"""
    global coqui_model_id
    return coqui_model_id

def get_coqui_model_description(model_id):
    """Retourne la description d'un modèle Coqui à partir de son ID"""
    for model in COQUI_MODELS:
        if model["id"] == model_id:
            return model["description"]
    return "modèle inconnu"

# Fonction pour charger le modèle CoquiTTS (définie en dehors des blocs try/except)
def load_coqui_model(model_id=None):
    global coqui_model, coqui_vocoder, coqui_available, coqui_model_name, coqui_model_id
    
    # Importer Coqui TTS à la demande
    if not import_coqui_tts():
        print("CoquiTTS n'est pas disponible sur ce système")
        return None, None
    
    # Si un ID de modèle est spécifié, le rechercher dans la liste
    selected_model = None
    if model_id:
        for model in COQUI_MODELS:
            if model["id"] == model_id:
                selected_model = model
                break
        
        if not selected_model:
            print(f"Modèle {model_id} non trouvé, utilisation du modèle par défaut")
            model_id = DEFAULT_COQUI_MODEL_ID
            for model in COQUI_MODELS:
                if model["id"] == model_id:
                    selected_model = model
                    break
    
    # Si aucun modèle n'est spécifié ou trouvé, utiliser le modèle actuel ou le modèle par défaut
    if not selected_model:
        if coqui_model is not None and coqui_model_id:
            # Le modèle est déjà chargé, le retourner
            return coqui_model, coqui_vocoder
        else:
            # Utiliser le modèle par défaut
            model_id = DEFAULT_COQUI_MODEL_ID
            for model in COQUI_MODELS:
                if model["id"] == model_id:
                    selected_model = model
                    break
    
    # Si le modèle est déjà chargé et qu'on demande le même modèle, le retourner
    if coqui_model is not None and coqui_model_id == model_id:
        print(f"Modèle {model_id} déjà chargé")
        return coqui_model, coqui_vocoder
    
    # Charger le nouveau modèle
    if selected_model:
        try:
            model_name = selected_model["name"]
            description = selected_model["description"]
            
            print(f"Chargement du modèle {description}...")
            
            # Désactiver les avertissements pendant le chargement du modèle
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                # Vérifier si un nom de modèle spécifique est fourni
                if "model_name" in selected_model:
                    coqui_model = TTS_API(model_name=model_name, model_type=selected_model["model_name"], progress_bar=False)
                else:
                    coqui_model = TTS_API(model_name=model_name, progress_bar=False)
            
            print(f"Modèle {description} chargé avec succès")
            coqui_model_name = description
            coqui_model_id = selected_model["id"]
            
            # Tester le modèle avec une phrase courte
            test_file = os.path.join(tempfile.gettempdir(), f'tts_test_{time.time()}.wav')
            test_phrase = "Test de synthèse vocale."
            
            # Vérifier si le modèle est multilingue
            if hasattr(coqui_model, 'is_multi_lingual') and coqui_model.is_multi_lingual:
                coqui_model.tts_to_file(text=test_phrase, file_path=test_file, language="fr")
            else:
                coqui_model.tts_to_file(text=test_phrase, file_path=test_file)
            
            if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                print(f"Test du modèle réussi (taille: {os.path.getsize(test_file)} octets)")
                try:
                    os.remove(test_file)
                except:
                    pass
                # Modèle chargé et testé avec succès
                return coqui_model, coqui_vocoder
            else:
                raise Exception("Test du modèle échoué: fichier vide")
                
        except Exception as e:
            print(f"Erreur avec {description}: {e}")
            # Essayer de charger un modèle de secours
            return load_coqui_model_fallback()
    else:
        # Aucun modèle trouvé, essayer le chargement de secours
        return load_coqui_model_fallback()

def load_coqui_model_fallback():
    """Fonction de secours pour charger un modèle Coqui si le modèle demandé échoue"""
    global coqui_model, coqui_vocoder, coqui_available, coqui_model_name, coqui_model_id
    
    print("Tentative de chargement d'un modèle de secours...")
    
    # Essayer chaque modèle dans l'ordre
    for model_info in COQUI_MODELS:
        try:
            model_name = model_info["name"]
            description = model_info["description"]
            
            print(f"Essai du modèle {description}...")
            
            # Désactiver les avertissements pendant le chargement du modèle
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                # Vérifier si un nom de modèle spécifique est fourni
                if "model_name" in model_info:
                    coqui_model = TTS_API(model_name=model_name, model_type=model_info["model_name"], progress_bar=False)
                else:
                    coqui_model = TTS_API(model_name=model_name, progress_bar=False)
            
            print(f"Modèle {description} chargé avec succès")
            coqui_model_name = description
            coqui_model_id = model_info["id"]
            
            # Tester le modèle avec une phrase courte
            test_file = os.path.join(tempfile.gettempdir(), f'tts_test_{time.time()}.wav')
            test_phrase = "Test de synthèse vocale."
            
            # Vérifier si le modèle est multilingue
            if hasattr(coqui_model, 'is_multi_lingual') and coqui_model.is_multi_lingual:
                coqui_model.tts_to_file(text=test_phrase, file_path=test_file, language="fr")
            else:
                coqui_model.tts_to_file(text=test_phrase, file_path=test_file)
            
            if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                print(f"Test du modèle réussi (taille: {os.path.getsize(test_file)} octets)")
                try:
                    os.remove(test_file)
                except:
                    pass
                # Modèle chargé et testé avec succès
                return coqui_model, coqui_vocoder
            else:
                raise Exception("Test du modèle échoué: fichier vide")
                
        except Exception as e:
            print(f"Erreur avec {model_info['description']}: {e}")
            # Continuer avec le modèle suivant
            continue
    
    # Vérifier si un modèle a été chargé avec succès
    if coqui_model is None:
        print("Échec du chargement de tous les modèles CoquiTTS")
        coqui_available = False
        return None, None

    # Ne pas utiliser de vocodeur séparé
    coqui_vocoder = None

    return coqui_model, coqui_vocoder

# Importations spécifiques à macOS
if is_mac():
    try:
        import subprocess
    except ImportError:
        pass

# File d'attente pour les messages à lire
tts_queue = queue.Queue()
# Flag pour indiquer si le thread TTS est en cours d'exécution
tts_thread_running = False
# Instance du moteur TTS
tts_engine = None
# Flag pour indiquer si le TTS est en cours de lecture
tts_is_speaking = False
# Moteur TTS actuel ('pyttsx3', 'gtts', 'macos_say', 'espeak' ou 'coqui')
tts_engine_type = 'pyttsx3'  # Valeur par défaut

# Variables pour le système de feedback vocal rapide
feedback_court_message = ""
feedback_court_pret = False
feedback_court_audio_file = None

# Déterminer le moteur TTS par défaut selon l'OS
if is_mac():
    tts_engine_type = 'macos_say'
elif is_linux():
    # Vérifier si espeak est disponible
    try:
        subprocess.run(["espeak", "--version"], capture_output=True)
        tts_engine_type = 'espeak'
    except:
        if gTTS:
            tts_engine_type = 'gtts'
elif is_windows():
    if pyttsx3:
        tts_engine_type = 'pyttsx3'
    elif gTTS:
        tts_engine_type = 'gtts'

def initialiser_tts():
    """Initialise le thread de lecture TTS"""
    global tts_thread_running, tts_engine_type
    
    # Importer les modules TTS à la demande
    import_tts_modules()
    
    # Charger le moteur TTS depuis la base de données
    try:
        from config import get_preference
        saved_engine = get_preference("tts_engine")
        if saved_engine and saved_engine in ["pyttsx3", "gtts", "coqui", "macos_say", "espeak"]:
            tts_engine_type = saved_engine
            print(f"Moteur TTS chargé depuis la base de données: {tts_engine_type}")
    except Exception as e:
        print(f"Erreur lors du chargement du moteur TTS depuis la base de données: {e}")
    
    if not tts_thread_running:
        tts_thread = threading.Thread(target=processus_tts, daemon=True)
        tts_thread_running = True
        tts_thread.start()
        print("Thread TTS initialisé")

def initialiser_moteur_tts():
    """Initialise le moteur TTS"""
    global tts_engine, tts_rate
    
    if tts_engine_type == 'pyttsx3':
        if pyttsx3 is None:
            print("Module pyttsx3 non disponible")
            return False
            
        if tts_engine is None:
            try:
                tts_engine = pyttsx3.init()
                
                # Configuration du moteur avec la vitesse définie
                tts_engine.setProperty('rate', tts_rate['pyttsx3'])  # Vitesse de parole
                
                # Essayer de définir une voix française si disponible
                voices = tts_engine.getProperty('voices')
                for voice in voices:
                    if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                        tts_engine.setProperty('voice', voice.id)
                        print(f"Voix française sélectionnée: {voice.name}")
                        break
                
                return True
            except Exception as e:
                print(f"Erreur lors de l'initialisation du moteur TTS pyttsx3: {str(e)}")
                return False
        
        return True
    
    elif tts_engine_type == 'gtts':
        if gTTS is None:
            print("Module gTTS non disponible")
            return False
        return True
    
    elif tts_engine_type == 'macos_say':
        if not is_mac():
            print("Commande 'say' disponible uniquement sur macOS")
            return False
        return True
    
    elif tts_engine_type == 'espeak':
        if not is_linux():
            print("Commande 'espeak' principalement disponible sur Linux")
            return False
        
        # Vérifier si espeak est installé
        try:
            subprocess.run(["espeak", "--version"], capture_output=True)
            return True
        except:
            print("Commande 'espeak' non disponible. Installez-la avec 'sudo apt-get install espeak'")
            return False
    
    return False

def processus_tts():
    """Processus en arrière-plan pour lire les messages de la file d'attente"""
    global tts_thread_running
    
    # Initialiser le moteur TTS
    if not initialiser_moteur_tts():
        tts_thread_running = False
        return
    
    while tts_thread_running:
        try:
            # Attendre un message dans la file d'attente avec timeout
            texte = tts_queue.get(timeout=1)
            if texte:
                lire_texte(texte)
            tts_queue.task_done()
        except queue.Empty:
            # Pas de message dans la file d'attente, continuer
            pass
        except Exception as e:
            print(f"Erreur dans le processus TTS: {str(e)}")
            time.sleep(1)  # Éviter une boucle d'erreur trop rapide

def lire_texte_pyttsx3(texte):
    """Lit le texte à haute voix en utilisant pyttsx3"""
    global tts_engine, tts_is_speaking
    
    try:
        # Forcer la réinitialisation du moteur pour chaque nouvelle lecture
        # Cela résout les problèmes de blocage après une interruption
        if tts_engine is not None:
            try:
                tts_engine.stop()
                del tts_engine
            except:
                pass
            tts_engine = None
            
        # Initialiser un nouveau moteur
        if not initialiser_moteur_tts():
            print("Impossible d'initialiser le moteur TTS")
            # Essayer de basculer vers gTTS si disponible
            if gTTS is not None:
                print("Basculement vers gTTS suite à l'échec de pyttsx3")
                lire_texte_gtts(texte)
            return
        
        # Prétraitement du texte pour une meilleure lecture
        texte_propre = texte.replace('\n', ' ').strip()
        
        # Découper le texte en phrases pour une meilleure gestion
        # Utiliser une expression régulière pour détecter les fins de phrases
        import re
        phrases = re.split(r'(?<=[.!?])\s+', texte_propre)
        phrases = [p.strip() for p in phrases if p.strip()]
        
        # Si aucune phrase n'a été détectée, utiliser le texte complet
        if not phrases:
            phrases = [texte_propre]
        
        tts_is_speaking = True
        erreurs_consecutives = 0
        
        for phrase in phrases:
            if phrase and tts_is_speaking:
                # Limiter la longueur des phrases pour éviter les problèmes
                if len(phrase) > 500:
                    sous_phrases = [phrase[i:i+500] for i in range(0, len(phrase), 500)]
                else:
                    sous_phrases = [phrase]
                
                for sous_phrase in sous_phrases:
                    if not tts_is_speaking:
                        break
                        
                    print(f"Lecture TTS (pyttsx3): {sous_phrase[:50]}...")
                    try:
                        # Vérifier que le moteur est toujours valide
                        if tts_engine is None:
                            if not initialiser_moteur_tts():
                                raise Exception("Échec de l'initialisation du moteur")
                        
                        tts_engine.say(sous_phrase)
                        tts_engine.runAndWait()
                        # Réinitialiser le compteur d'erreurs après une lecture réussie
                        erreurs_consecutives = 0
                        
                    except Exception as e:
                        erreurs_consecutives += 1
                        print(f"Erreur pendant la lecture, réinitialisation du moteur: {e}")
                        
                        # Réinitialiser le moteur en cas d'erreur
                        try:
                            del tts_engine
                        except:
                            pass
                        tts_engine = None
                        
                        # Limiter le nombre de tentatives pour éviter une boucle infinie
                        if erreurs_consecutives < 3:
                            if initialiser_moteur_tts():
                                try:
                                    # Réessayer de lire la phrase
                                    tts_engine.say(sous_phrase)
                                    tts_engine.runAndWait()
                                    erreurs_consecutives = 0
                                except:
                                    pass
                        else:
                            print("Trop d'erreurs consécutives, abandon de la lecture pyttsx3")
                            # Basculer vers gTTS si disponible après trop d'erreurs
                            if gTTS is not None:
                                print("Basculement vers gTTS après échecs répétés")
                                lire_texte_gtts(texte)
                            break
            
            # Si l'arrêt a été demandé, sortir de la boucle
            if not tts_is_speaking:
                break
                
        tts_is_speaking = False
                
    except Exception as e:
        print(f"Erreur lors de la lecture TTS (pyttsx3): {str(e)}")
        tts_is_speaking = False
        # Essayer de basculer vers gTTS en cas d'erreur critique
        if gTTS is not None:
            print("Basculement vers gTTS suite à une erreur critique")
            lire_texte_gtts(texte)

# Cache pour les fichiers audio
gtts_cache = {}
coqui_cache = {}
tts_cache_size = 50  # Nombre maximum d'entrées dans le cache

# Créer le répertoire de cache
cache_dir = os.path.join(tempfile.gettempdir(), 'whisp_tts_cache')
os.makedirs(cache_dir, exist_ok=True)

def lire_texte_gtts(texte):
    """Lit le texte à haute voix en utilisant Google Text-to-Speech (gTTS)"""
    global tts_is_speaking, tts_rate, gtts_cache
    
    # Mesurer le temps de début
    temps_debut = time.time()
    
    try:
        # Nettoyer le texte (remplacer les sauts de ligne par des espaces)
        texte_propre = texte.replace('\n', ' ').strip()
        
        if not texte_propre:
            return
            
        tts_is_speaking = True
        
        # Vérifier si pygame est correctement initialisé
        if not ensure_pygame_initialized():
            print("Impossible d'initialiser pygame, tentative de réinitialisation...")
            try:
                pygame.quit()
                time.sleep(0.2)  # Attendre que les ressources soient libérées
                pygame.init()
                pygame.mixer.init(frequency=44100, buffer=1024)
                pygame_initialized = True
            except Exception as e:
                print(f"Échec de la réinitialisation de pygame: {e}")
                tts_is_speaking = False
                return
        
        # Créer un répertoire temporaire unique pour l'utilisateur actuel
        user_temp = os.path.join(tempfile.gettempdir(), f'whisp_tts_{os.getpid()}')
        try:
            os.makedirs(user_temp, exist_ok=True)
        except PermissionError:
            # En cas d'erreur de permission, utiliser un dossier dans le répertoire courant
            user_temp = os.path.join(os.getcwd(), 'temp_tts')
            os.makedirs(user_temp, exist_ok=True)
        
        # Facteur d'accélération à partir des paramètres
        acceleration_factor = tts_rate['gtts']
        
        # Limiter la longueur du texte pour éviter les problèmes
        if len(texte_propre) > 3000:
            texte_propre = texte_propre[:3000] + "..."
            print("Texte tronqué à 3000 caractères pour éviter les problèmes de performance")
        
        print(f"Lecture TTS (gTTS) démarrée: {texte_propre[:50]}...")
        
        # Vérifier si le texte est dans le cache
        cache_key = f"{texte_propre}_{acceleration_factor}"
        cache_hash = str(hash(cache_key))[:10]  # Utiliser seulement les 10 premiers caractères du hash
        temps_cache_verification = time.time()
        cache_hit = False
        
        # Vérifier le cache avec gestion d'erreur
        try:
            if cache_key in gtts_cache and os.path.exists(gtts_cache[cache_key]):
                print(f"Utilisation du fichier audio en cache (vérification: {(temps_cache_verification - temps_debut)*1000:.2f}ms)")
                audio_file = gtts_cache[cache_key]
                cache_hit = True
            else:
                # Vérifier si un fichier de cache existe déjà pour ce hash
                cache_dir = os.path.join(tempfile.gettempdir(), 'whisp_tts_cache')
                os.makedirs(cache_dir, exist_ok=True)
                potential_cache_file = os.path.join(cache_dir, f'tts_cache_{cache_hash}.mp3')
                
                if os.path.exists(potential_cache_file) and os.path.getsize(potential_cache_file) > 0:
                    print(f"Fichier de cache trouvé par hash: {potential_cache_file}")
                    gtts_cache[cache_key] = potential_cache_file
                    audio_file = potential_cache_file
                    cache_hit = True
                else:
                    cache_hit = False
        except Exception as cache_error:
            print(f"Erreur lors de la vérification du cache: {cache_error}")
            cache_hit = False
        
        if not cache_hit:
            # Créer un fichier temporaire pour l'audio avec un nom unique
            temp_file = os.path.join(user_temp, f'tts_temp_{os.getpid()}_{time.time()}.mp3')
            
            temps_avant_generation = time.time()
            print(f"Génération de l'audio avec gTTS (préparation: {(temps_avant_generation - temps_debut)*1000:.2f}ms)...")
            
            # Générer l'audio avec gTTS avec gestion d'erreur et timeout
            try:
                # Générer l'audio avec gTTS - forcer slow=False pour une vitesse de base plus rapide
                tts = gTTS(text=texte_propre, lang='fr', slow=False)
                
                # Utiliser un timeout pour éviter les blocages
                import threading
                save_success = [False]
                save_error = [None]
                
                def save_with_timeout():
                    try:
                        tts.save(temp_file)
                        save_success[0] = True
                    except Exception as e:
                        save_error[0] = e
                
                save_thread = threading.Thread(target=save_with_timeout)
                save_thread.daemon = True
                save_thread.start()
                save_thread.join(timeout=10.0)  # Timeout de 10 secondes
                
                if not save_success[0]:
                    if save_error[0]:
                        raise save_error[0]
                    else:
                        raise TimeoutError("Timeout lors de la génération de l'audio gTTS")
                
                if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                    raise Exception("Fichier audio généré vide ou inexistant")
                
            except Exception as gtts_error:
                print(f"Erreur lors de la génération audio avec gTTS: {gtts_error}")
                tts_is_speaking = False
                return
            
            temps_apres_generation = time.time()
            print(f"Audio généré en {(temps_apres_generation - temps_avant_generation)*1000:.2f}ms")
            
            # Essayer d'utiliser ffmpeg pour accélérer l'audio si disponible
            accelerated_file = os.path.join(user_temp, f'tts_accel_{os.getpid()}_{time.time()}.mp3')
            
            try:
                # Vérifier si ffmpeg est disponible
                import subprocess
                ffmpeg_check = subprocess.run(["ffmpeg", "-version"], 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL, 
                                             timeout=0.5)
                
                if ffmpeg_check.returncode == 0:
                    # Utiliser ffmpeg pour accélérer l'audio avec un timeout court
                    subprocess.run([
                        "ffmpeg", "-y", "-i", temp_file, 
                        "-filter:a", f"atempo={acceleration_factor}", 
                        "-vn", accelerated_file
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0)
                    
                    # Si ffmpeg a réussi, utiliser le fichier accéléré
                    temps_apres_ffmpeg = time.time()
                    if os.path.exists(accelerated_file) and os.path.getsize(accelerated_file) > 0:
                        audio_file = accelerated_file
                        print(f"Audio accéléré avec ffmpeg en {(temps_apres_ffmpeg - temps_apres_generation)*1000:.2f}ms")
                        # Supprimer le fichier temporaire original
                        try:
                            os.remove(temp_file)
                        except:
                            pass
                    else:
                        audio_file = temp_file
                        print("Échec de l'accélération avec ffmpeg, utilisation du fichier original")
                else:
                    audio_file = temp_file
                    print("ffmpeg non disponible, utilisation du fichier audio original")
            except Exception as e:
                # Si ffmpeg échoue, utiliser le fichier original
                print(f"Impossible d'accélérer l'audio avec ffmpeg: {e}")
                audio_file = temp_file
            
            # Ajouter au cache avec gestion d'erreur
            try:
                # Gérer la taille du cache
                if len(gtts_cache) >= tts_cache_size:
                    # Supprimer l'entrée la plus ancienne
                    oldest_key = next(iter(gtts_cache))
                    oldest_file = gtts_cache.pop(oldest_key)
                    try:
                        if os.path.exists(oldest_file):
                            os.remove(oldest_file)
                    except:
                        pass
                
                # Créer un fichier permanent pour le cache
                cache_dir = os.path.join(tempfile.gettempdir(), 'whisp_tts_cache')
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, f'tts_cache_{cache_hash}.mp3')
                
                # Copier le fichier dans le cache
                import shutil
                shutil.copy2(audio_file, cache_file)
                
                # Mettre à jour le cache
                gtts_cache[cache_key] = cache_file
            except Exception as cache_error:
                print(f"Erreur lors de la mise en cache: {cache_error}")
                # Continuer avec le fichier temporaire si le cache échoue
                cache_file = audio_file
            
            temps_avant_lecture = time.time()
            print(f"Préparation totale: {(temps_avant_lecture - temps_debut)*1000:.2f}ms")
        else:
            audio_file = gtts_cache[cache_key]
        
        # Charger et lire l'audio avec gestion d'erreur robuste
        try:
            temps_avant_chargement = time.time()
            
            # Vérifier que le fichier existe et a une taille non nulle
            if not os.path.exists(audio_file) or os.path.getsize(audio_file) == 0:
                raise FileNotFoundError(f"Fichier audio invalide: {audio_file}")
            
            # Réinitialiser le mixer avant de charger un nouveau fichier
            try:
                pygame.mixer.music.unload()
            except:
                pass
            
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            
            # Vérifier que la lecture a bien démarré
            time.sleep(0.1)
            if not pygame.mixer.music.get_busy():
                raise Exception("La lecture n'a pas démarré correctement")
                
            temps_apres_lecture = time.time()
            
            if cache_hit:
                print(f"Audio en cache chargé et lecture démarrée en {(temps_apres_lecture - temps_avant_chargement)*1000:.2f}ms")
            else:
                print(f"Audio généré chargé et lecture démarrée en {(temps_apres_lecture - temps_avant_chargement)*1000:.2f}ms")
            
            print(f"Temps total avant lecture: {(temps_apres_lecture - temps_debut)*1000:.2f}ms")
            
            # Attendre la fin de la lecture avec un tick rate optimal pour une meilleure réactivité
            try:
                print("En attente de la fin de la lecture...")
                clock = pygame.time.Clock()
                while pygame.mixer.music.get_busy() and tts_is_speaking:
                    clock.tick(60)  # 60 FPS est suffisant et moins gourmand en ressources
                print("Fin de la boucle d'attente de lecture")
            except Exception as wait_error:
                print(f"Erreur pendant l'attente de fin de lecture: {wait_error}")
            
            temps_fin_lecture = time.time()
            duree_lecture = temps_fin_lecture - temps_apres_lecture
            print(f"Lecture terminée en {duree_lecture*1000:.2f}ms")
            print(f"Temps total (préparation + lecture): {(temps_fin_lecture - temps_debut)*1000:.2f}ms")
        except Exception as e:
            print(f"Erreur pendant la lecture audio: {e}")
            # Essayer une méthode alternative de lecture
            try:
                print("Tentative de lecture alternative...")
                # Réinitialiser pygame complètement
                pygame.mixer.quit()
                pygame.mixer.init(frequency=44100, buffer=2048)
                
                # Nouvelle tentative de lecture
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                
                # Attente simplifiée
                while pygame.mixer.music.get_busy() and tts_is_speaking:
                    time.sleep(0.1)
            except Exception as alt_error:
                print(f"Échec de la méthode alternative: {alt_error}")
            
        # Si l'arrêt a été demandé, arrêter la lecture
        if not tts_is_speaking:
            # Arrêter la lecture en cours
            try:
                pygame.mixer.music.stop()
            except:
                pass
        
        tts_is_speaking = False
        
        # Nettoyer le répertoire temporaire (mais pas le cache)
        try:
            for file in os.listdir(user_temp):
                try:
                    os.remove(os.path.join(user_temp, file))
                except:
                    pass
            try:
                os.rmdir(user_temp)
            except:
                pass
        except:
            pass
        
    except Exception as e:
        print(f"Erreur lors de la lecture TTS (gTTS): {str(e)}")
        tts_is_speaking = False

def lire_texte_macos_say(texte):
    """Lit le texte à haute voix en utilisant la commande 'say' de macOS"""
    global tts_is_speaking, tts_rate
    
    try:
        # Découper le texte en phrases pour une meilleure gestion
        phrases = [p.strip() for p in texte.replace('\n', '. ').split('.') if p.strip()]
        
        tts_is_speaking = True
        
        for phrase in phrases:
            if phrase and tts_is_speaking:
                print(f"Lecture TTS (macOS say): {phrase}")
                
                try:
                    # Utiliser la commande 'say' avec voix française et vitesse personnalisée
                    # -r spécifie la vitesse en mots par minute
                    subprocess.run(["say", "-v", "Thomas", "-r", str(tts_rate['macos_say']), phrase], check=False)
                except Exception as e:
                    print(f"Erreur pendant la lecture macOS say: {e}")
                    # Essayer sans spécifier la voix mais avec la vitesse
                    try:
                        subprocess.run(["say", "-r", str(tts_rate['macos_say']), phrase], check=False)
                    except:
                        # Dernier recours: sans options
                        try:
                            subprocess.run(["say", phrase], check=False)
                        except:
                            pass
                    
            # Si l'arrêt a été demandé, sortir de la boucle
            if not tts_is_speaking:
                # Arrêter tous les processus 'say' en cours
                try:
                    subprocess.run(["killall", "say"], check=False)
                except:
                    pass
                break
        
        tts_is_speaking = False
        
    except Exception as e:
        print(f"Erreur lors de la lecture TTS (macOS say): {str(e)}")
        tts_is_speaking = False

def lire_texte_espeak(texte):
    """Lit le texte à haute voix en utilisant espeak (Linux)"""
    global tts_is_speaking, tts_rate
    
    try:
        # Découper le texte en phrases pour une meilleure gestion
        phrases = [p.strip() for p in texte.replace('\n', '. ').split('.') if p.strip()]
        
        tts_is_speaking = True
        
        for phrase in phrases:
            if phrase and tts_is_speaking:
                print(f"Lecture TTS (espeak): {phrase}")
                
                try:
                    # Utiliser espeak avec voix française et vitesse personnalisée
                    # -s spécifie la vitesse en mots par minute
                    subprocess.run(["espeak", "-v", "fr", "-s", str(tts_rate['espeak']), phrase], check=False)
                except Exception as e:
                    print(f"Erreur pendant la lecture espeak: {e}")
                    # Essayer sans spécifier la voix mais avec la vitesse
                    try:
                        subprocess.run(["espeak", "-s", str(tts_rate['espeak']), phrase], check=False)
                    except:
                        # Dernier recours: sans options
                        try:
                            subprocess.run(["espeak", phrase], check=False)
                        except:
                            pass
                    
            # Si l'arrêt a été demandé, sortir de la boucle
            if not tts_is_speaking:
                # Arrêter tous les processus espeak en cours
                try:
                    subprocess.run(["killall", "espeak"], check=False)
                except:
                    pass
                break
        
        tts_is_speaking = False
        
    except Exception as e:
        print(f"Erreur lors de la lecture TTS (espeak): {str(e)}")
        tts_is_speaking = False

def lire_texte_coqui(texte):
    """Lit le texte à haute voix en utilisant Coqui TTS"""
    global tts_is_speaking, tts_rate, coqui_model, coqui_available, coqui_cache, coqui_model_name
    
    # Vérifier si CoquiTTS est disponible
    if not coqui_available:
        print("CoquiTTS n'est pas disponible, utilisation de gTTS à la place")
        lire_texte_gtts(texte)
        return
    
    # Mesurer le temps de début
    temps_debut = time.time()
    
    try:
        # Nettoyer le texte (remplacer les sauts de ligne par des espaces)
        texte_propre = texte.replace('\n', ' ').strip()
        
        if not texte_propre:
            return
            
        tts_is_speaking = True
        
        # Vérifier si pygame est correctement initialisé
        if not ensure_pygame_initialized():
            print("Impossible d'initialiser pygame pour CoquiTTS, tentative de réinitialisation...")
            try:
                pygame.quit()
                time.sleep(0.2)
                pygame.init()
                pygame.mixer.init(frequency=44100, buffer=2048)
                pygame_initialized = True
            except Exception as e:
                print(f"Échec de la réinitialisation de pygame: {e}")
                # Basculer vers gTTS en cas d'échec
                print("Basculement vers gTTS suite à l'échec d'initialisation de pygame")
                lire_texte_gtts(texte_propre)
                return
        
        # Limiter la longueur du texte pour éviter les problèmes de performance
        if len(texte_propre) > 2000:
            print(f"Texte trop long pour CoquiTTS ({len(texte_propre)} caractères), troncature à 2000 caractères")
            texte_propre = texte_propre[:2000] + "..."
        
        # Créer un répertoire temporaire unique pour l'utilisateur actuel
        user_temp = os.path.join(tempfile.gettempdir(), f'whisp_tts_{os.getpid()}')
        try:
            os.makedirs(user_temp, exist_ok=True)
        except PermissionError:
            # En cas d'erreur de permission, utiliser un dossier dans le répertoire courant
            user_temp = os.path.join(os.getcwd(), 'temp_tts')
            os.makedirs(user_temp, exist_ok=True)
        
        # Vérifier si le texte est dans le cache
        cache_key = f"coqui_{hash(texte_propre)}"
        cache_hit = False
    
        try:
            if cache_key in coqui_cache and os.path.exists(coqui_cache[cache_key]):
                print(f"Utilisation du fichier audio en cache pour CoquiTTS")
                temp_file = coqui_cache[cache_key]
                print(f"Fichier en cache: {temp_file}")
                cache_hit = True
            else:
                # Vérifier si un fichier de cache existe déjà pour ce hash
                cache_dir = os.path.join(tempfile.gettempdir(), 'whisp_tts_cache')
                os.makedirs(cache_dir, exist_ok=True)
                potential_cache_file = os.path.join(cache_dir, f'tts_cache_coqui_{hash(texte_propre)}.wav')
                
                if os.path.exists(potential_cache_file) and os.path.getsize(potential_cache_file) > 0:
                    print(f"Fichier de cache trouvé par hash: {potential_cache_file}")
                    coqui_cache[cache_key] = potential_cache_file
                    temp_file = potential_cache_file
                    cache_hit = True
                else:
                    cache_hit = False
        except Exception as cache_error:
            print(f"Erreur lors de la vérification du cache: {cache_error}")
            cache_hit = False
        
        if not cache_hit:
            # Créer un fichier temporaire pour l'audio
            temp_file = os.path.join(user_temp, f'tts_coqui_{os.getpid()}_{time.time()}.wav')
            
            print(f"Génération TTS pour: {texte_propre[:50]}...")
            
            # Charger le modèle si nécessaire avec gestion d'erreur
            if coqui_model is None:
                try:
                    # Utiliser un timeout pour le chargement du modèle
                    import threading
                    load_success = [False]
                    load_error = [None]
                    
                    def load_with_timeout():
                        try:
                            global coqui_model, coqui_vocoder
                            coqui_model, coqui_vocoder = load_coqui_model()
                            load_success[0] = True
                        except Exception as e:
                            load_error[0] = e
                    
                    load_thread = threading.Thread(target=load_with_timeout)
                    load_thread.daemon = True
                    load_thread.start()
                    load_thread.join(timeout=30.0)  # Timeout de 30 secondes pour le chargement
                    
                    if not load_success[0]:
                        if load_error[0]:
                            raise load_error[0]
                        else:
                            raise TimeoutError("Timeout lors du chargement du modèle TTS")
                    
                    if coqui_model is None:
                        raise Exception("Le modèle n'a pas été chargé correctement")
                        
                except Exception as e:
                    print(f"Erreur lors du chargement du modèle CoquiTTS: {e}")
                    print("Basculement vers gTTS suite à l'échec de chargement du modèle")
                    lire_texte_gtts(texte_propre)
                    return
            
            # Diviser le texte en phrases pour une meilleure gestion
            import re
            phrases = re.split(r'(?<=[.!?])\s+', texte_propre)
            phrases = [p.strip() for p in phrases if p.strip()]
            
            # Si aucune phrase n'a été extraite, utiliser le texte original
            if not phrases:
                phrases = [texte_propre]
            
            # Pour les phrases trop longues, les diviser davantage
            phrases_finales = []
            for phrase in phrases:
                if len(phrase) > 150:
                    # Diviser par virgules ou autres séparateurs
                    sous_phrases = re.split(r'(?<=[:;,])\s+', phrase)
                    sous_phrases = [sp.strip() for sp in sous_phrases if sp.strip()]
                    phrases_finales.extend(sous_phrases)
                else:
                    phrases_finales.append(phrase)
            
            print(f"Texte divisé en {len(phrases_finales)} segments pour Tacotron")
            
            # Générer l'audio pour chaque phrase avec gestion d'erreur
            audio_files = []
            erreurs_generation = 0
            
            for i, phrase in enumerate(phrases_finales):
                if not tts_is_speaking:
                    break
                
                # Limiter le nombre d'erreurs consécutives
                if erreurs_generation >= 3:
                    print("Trop d'erreurs de génération, basculement vers gTTS")
                    break
                
                phrase_file = os.path.join(user_temp, f'tts_tacotron_part_{i}_{time.time()}.wav')
                try:
                    print(f"Génération audio pour segment {i+1}/{len(phrases_finales)}: {phrase[:30]}...")
                    
                    # Nettoyer la phrase des caractères problématiques
                    phrase_clean = re.sub(r'[^\w\s.,!?:;()\'\"-éèêëàâäôöùûüçÉÈÊËÀÂÄÔÖÙÛÜÇ]', ' ', phrase)
                    
                    # Utiliser un timeout pour la génération
                    import threading
                    gen_success = [False]
                    gen_error = [None]
                    
                    def generate_with_timeout():
                        try:
                            # Vérifier si le modèle est multilingue
                            if hasattr(coqui_model, 'is_multi_lingual') and coqui_model.is_multi_lingual:
                                coqui_model.tts_to_file(text=phrase_clean, file_path=phrase_file, language="fr")
                            else:
                                coqui_model.tts_to_file(text=phrase_clean, file_path=phrase_file)
                            gen_success[0] = True
                        except Exception as e:
                            gen_error[0] = e
                    
                    gen_thread = threading.Thread(target=generate_with_timeout)
                    gen_thread.daemon = True
                    gen_thread.start()
                    gen_thread.join(timeout=10.0)  # Timeout de 10 secondes par segment
                    
                    if not gen_success[0]:
                        if gen_error[0]:
                            raise gen_error[0]
                        else:
                            raise TimeoutError("Timeout lors de la génération audio")
                    
                    if os.path.exists(phrase_file) and os.path.getsize(phrase_file) > 0:
                        audio_files.append(phrase_file)
                        # Réinitialiser le compteur d'erreurs après un succès
                        erreurs_generation = 0
                    else:
                        raise Exception("Fichier audio vide ou inexistant")
                        
                except Exception as e:
                    erreurs_generation += 1
                    print(f"Erreur lors de la génération audio pour le segment {i+1}: {e}")
                    continue
            
            # Si aucun fichier audio n'a été généré ou trop d'erreurs, utiliser gTTS
            if not audio_files or erreurs_generation >= 3:
                print("Échec de la génération audio avec CoquiTTS, utilisation de gTTS")
                lire_texte_gtts(texte_propre)
                return
            
            # Fusionner les fichiers audio si nécessaire
            if len(audio_files) > 1:
                try:
                    import wave
                    import numpy as np
                    
                    print(f"Fusion de {len(audio_files)} fichiers audio...")
                    
                    # Lire tous les fichiers audio
                    audio_data = []
                    sample_rate = None
                    params = None
                    
                    for audio_file in audio_files:
                        try:
                            with wave.open(audio_file, 'rb') as wf:
                                if params is None:
                                    params = wf.getparams()
                                    sample_rate = wf.getframerate()
                                
                                # Lire les données audio
                                frames = wf.readframes(wf.getnframes())
                                audio_data.append(frames)
                        except Exception as read_error:
                            print(f"Erreur lors de la lecture du fichier {audio_file}: {read_error}")
                    
                    # Écrire le fichier fusionné
                    if audio_data and params:
                        with wave.open(temp_file, 'wb') as outfile:
                            outfile.setparams(params)
                            for frames in audio_data:
                                outfile.writeframes(frames)
                        
                        print(f"Fichiers audio fusionnés avec succès dans {temp_file}")
                    else:
                        raise Exception("Aucune donnée audio valide à fusionner")
                except Exception as e:
                    print(f"Erreur lors de la fusion des fichiers audio: {e}")
                    # Utiliser le premier fichier si la fusion échoue
                    if audio_files:
                        temp_file = audio_files[0]
                        print(f"Utilisation du premier fichier audio: {temp_file}")
            elif audio_files:
                # S'il n'y a qu'un seul fichier, l'utiliser directement
                temp_file = audio_files[0]
                print(f"Un seul fichier audio généré, utilisation directe: {temp_file}")
            
            # Ajouter au cache avec gestion d'erreur
            try:
                # Gérer la taille du cache
                if len(coqui_cache) >= tts_cache_size:
                    # Supprimer l'entrée la plus ancienne
                    oldest_key = next(iter(coqui_cache))
                    oldest_file = coqui_cache.pop(oldest_key)
                    try:
                        if os.path.exists(oldest_file):
                            os.remove(oldest_file)
                    except:
                        pass
                
                # Créer un fichier permanent pour le cache
                cache_dir = os.path.join(tempfile.gettempdir(), 'whisp_tts_cache')
                os.makedirs(cache_dir, exist_ok=True)
                cache_file = os.path.join(cache_dir, f'tts_cache_coqui_{hash(texte_propre)}.wav')
                
                # Copier le fichier dans le cache
                import shutil
                shutil.copy2(temp_file, cache_file)
                
                # Mettre à jour le cache
                coqui_cache[cache_key] = cache_file
            except Exception as cache_error:
                print(f"Erreur lors de la mise en cache: {cache_error}")
        
        # Vérifier que le fichier existe et a une taille non nulle
        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            print("Le fichier audio est vide ou n'existe pas")
            lire_texte_gtts(texte_propre)
            return
        
        # Lire l'audio avec pygame avec gestion d'erreur robuste
        try:
            # Réinitialiser complètement pygame pour éviter les problèmes
            pygame.mixer.quit()
            pygame.mixer.init(frequency=44100, buffer=2048)
            
            print(f"Lecture du fichier audio: {temp_file}")
            
            # Charger et lire l'audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            
            # Attendre un court instant pour vérifier que la lecture a démarré
            time.sleep(0.1)
            
            # Vérifier si la lecture a bien démarré
            if pygame.mixer.music.get_busy():
                print("Lecture audio démarrée avec succès")
                
                # Attendre la fin de la lecture avec un tick rate optimal
                clock = pygame.time.Clock()
                while pygame.mixer.music.get_busy() and tts_is_speaking:
                    clock.tick(60)  # 60 FPS est suffisant
                
                print("Lecture audio terminée")
            else:
                print("La lecture n'a pas démarré, tentative alternative...")
                raise Exception("Échec de la lecture avec pygame")
                
        except Exception as e:
            print(f"Erreur lors de la lecture audio avec pygame: {e}")
            
            # Essayer avec sounddevice comme alternative
            try:
                # Vérifier si les modules sont disponibles
                import importlib
                sf_spec = importlib.util.find_spec("soundfile")
                sd_spec = importlib.util.find_spec("sounddevice")
                
                if sf_spec and sd_spec:
                    import soundfile as sf
                    import sounddevice as sd
                    
                    print("Tentative de lecture avec sounddevice...")
                    data, samplerate = sf.read(temp_file)
                    sd.play(data, samplerate)
                    
                    # Attendre la fin de la lecture avec possibilité d'interruption
                    while sd.get_stream().active and tts_is_speaking:
                        time.sleep(0.1)
                    
                    # Arrêter explicitement si nécessaire
                    if not tts_is_speaking:
                        sd.stop()
                    
                    print("Lecture avec sounddevice terminée")
                else:
                    raise ImportError("Modules soundfile ou sounddevice non disponibles")
            except Exception as sd_error:
                print(f"Erreur avec sounddevice: {sd_error}")
                
                # Essayer avec le lecteur système en dernier recours
                try:
                    print("Tentative de lecture avec le lecteur système...")
                    if is_windows():
                        os.system(f'start "" "{temp_file}"')
                    elif is_mac():
                        os.system(f'open "{temp_file}"')
                    elif is_linux():
                        os.system(f'xdg-open "{temp_file}"')
                    
                    # Attendre un peu pour laisser le temps au lecteur de démarrer
                    time.sleep(2)
                except Exception as sys_error:
                    print(f"Erreur avec le lecteur système: {sys_error}")
        
        tts_is_speaking = False
        
        # Nettoyer les fichiers temporaires
        try:
            for file in audio_files:
                if file != temp_file and os.path.exists(file):
                    os.remove(file)
        except:
            pass
        
    except Exception as e:
        print(f"Erreur critique lors de la lecture TTS CoquiTTS: {str(e)}")
        tts_is_speaking = False
        
        # En cas d'erreur critique, basculer vers gTTS
        try:
            print("Basculement vers gTTS suite à une erreur critique avec CoquiTTS")
            lire_texte_gtts(texte)
        except:
            pass

@catch_errors(category=ErrorCategory.TTS, severity=ErrorSeverity.MEDIUM, notify_user=True)
def lire_texte(texte):
    """Lit le texte à haute voix en utilisant le moteur TTS sélectionné"""
    global tts_engine_type, coqui_available
    
    # Prétraitement du texte
    if not texte or texte.strip() == "":
        print("Texte vide, aucune lecture nécessaire")
        return
    
    # Nettoyer le texte (espaces, sauts de ligne, etc.)
    texte_propre = texte.replace('\n', ' ').strip()
    while '  ' in texte_propre:
        texte_propre = texte_propre.replace('  ', ' ')
    
    print(f"Lecture de texte avec le moteur: {tts_engine_type}")
    
    # Limiter la longueur du texte pour tous les moteurs
    if len(texte_propre) > 3000:
        texte_propre = texte_propre[:3000] + "..."
        print(f"Texte tronqué à 3000 caractères pour éviter les problèmes de performance")
    
    # Gestion spécifique pour CoquiTTS
    if tts_engine_type == 'coqui':
        # Limiter davantage pour CoquiTTS qui est plus gourmand
        if len(texte_propre) > 2000:
            texte_propre = texte_propre[:2000] + "..."
            print(f"Texte tronqué à 2000 caractères pour CoquiTTS")
        
        # Vérifier si CoquiTTS est toujours disponible
        global coqui_available
        if not coqui_available:
            print("CoquiTTS n'est plus disponible, basculement vers gTTS")
            error_handler.handle_error(
                "CoquiTTS n'est plus disponible, basculement vers gTTS",
                category=ErrorCategory.TTS,
                severity=ErrorSeverity.MEDIUM,
                notify_user=True,
                context={"engine": "coqui", "fallback": "gtts"}
            )
            tts_engine_type = 'gtts'  # Changer le moteur par défaut
            lire_texte_gtts(texte_propre)
            return
        
        # Vérifier si le modèle est chargé avec gestion d'erreur
        try:
            if coqui_model is None:
                print("Modèle CoquiTTS non chargé, tentative de chargement...")
                model, _ = load_coqui_model()
                if model is None:
                    error_msg = "Échec du chargement du modèle CoquiTTS, basculement vers gTTS"
                    print(error_msg)
                    error_handler.handle_error(
                        error_msg,
                        category=ErrorCategory.TTS,
                        severity=ErrorSeverity.MEDIUM,
                        notify_user=True,
                        context={"engine": "coqui", "action": "chargement du modèle"}
                    )
                    lire_texte_gtts(texte_propre)
                    return
            
            print(f"Démarrage de la lecture avec CoquiTTS (modèle: {coqui_model_name})...")
            lire_texte_coqui(texte_propre)
        except Exception as e:
            error_msg = f"Erreur critique avec CoquiTTS, basculement vers gTTS: {str(e)}"
            print(error_msg)
            error_handler.handle_error(
                e,
                category=ErrorCategory.TTS,
                severity=ErrorSeverity.HIGH,
                notify_user=True,
                context={"engine": "coqui", "model": coqui_model_name}
            )
            # Marquer CoquiTTS comme indisponible après une erreur critique
            coqui_available = False
            lire_texte_gtts(texte_propre)
        return
    
    # Pour les autres moteurs avec gestion d'erreur
    try:
        if tts_engine_type == 'gtts':
            if gTTS is None:
                error_msg = "Module gTTS non disponible, basculement vers pyttsx3"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.TTS,
                    severity=ErrorSeverity.MEDIUM,
                    notify_user=True,
                    context={"engine": "gtts", "fallback": "pyttsx3"}
                )
                if pyttsx3 is not None:
                    lire_texte_pyttsx3(texte_propre)
                return
            lire_texte_gtts(texte_propre)
            
        elif tts_engine_type == 'macos_say':
            if not is_mac():
                error_msg = "Commande 'say' disponible uniquement sur macOS, basculement vers gTTS"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.TTS,
                    severity=ErrorSeverity.LOW,
                    notify_user=False,
                    context={"engine": "macos_say", "os": get_os_type()}
                )
                if gTTS is not None:
                    lire_texte_gtts(texte_propre)
                return
            lire_texte_macos_say(texte_propre)
            
        elif tts_engine_type == 'espeak':
            if not is_linux():
                error_msg = "Commande 'espeak' principalement disponible sur Linux, basculement vers gTTS"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.TTS,
                    severity=ErrorSeverity.LOW,
                    notify_user=False,
                    context={"engine": "espeak", "os": get_os_type()}
                )
                if gTTS is not None:
                    lire_texte_gtts(texte_propre)
                return
            lire_texte_espeak(texte_propre)
            
        else:
            # Par défaut, utiliser pyttsx3
            if pyttsx3 is None:
                error_msg = "Module pyttsx3 non disponible, basculement vers gTTS"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.TTS,
                    severity=ErrorSeverity.MEDIUM,
                    notify_user=True,
                    context={"engine": "pyttsx3", "fallback": "gtts"}
                )
                if gTTS is not None:
                    lire_texte_gtts(texte_propre)
                return
            lire_texte_pyttsx3(texte_propre)
            
    except Exception as e:
        error_msg = f"Erreur lors de la lecture TTS avec {tts_engine_type}: {str(e)}"
        print(error_msg)
        error_handler.handle_error(
            e,
            category=ErrorCategory.TTS,
            severity=ErrorSeverity.HIGH,
            notify_user=True,
            context={"engine": tts_engine_type, "text_length": len(texte_propre)}
        )
        
        # Notifier l'utilisateur via l'interface web si disponible
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(f"Problème de synthèse vocale avec {tts_engine_type}. Tentative de récupération...", "warning")
        
        # Essayer de basculer vers un autre moteur en cas d'erreur
        try:
            if tts_engine_type != 'gtts' and gTTS is not None:
                print("Basculement vers gTTS suite à une erreur")
                lire_texte_gtts(texte_propre)
            elif tts_engine_type != 'pyttsx3' and pyttsx3 is not None:
                print("Basculement vers pyttsx3 suite à une erreur")
                lire_texte_pyttsx3(texte_propre)
            else:
                # Dernier recours: essayer tous les moteurs disponibles
                for engine in ['gtts', 'pyttsx3', 'macos_say', 'espeak']:
                    if engine != tts_engine_type:
                        try:
                            if engine == 'gtts' and gTTS is not None:
                                lire_texte_gtts(texte_propre)
                                return
                            elif engine == 'pyttsx3' and pyttsx3 is not None:
                                lire_texte_pyttsx3(texte_propre)
                                return
                            elif engine == 'macos_say' and is_mac():
                                lire_texte_macos_say(texte_propre)
                                return
                            elif engine == 'espeak' and is_linux():
                                lire_texte_espeak(texte_propre)
                                return
                        except:
                            continue
                
                # Si tous les moteurs échouent, notifier l'utilisateur
                error_msg = "Échec de tous les moteurs TTS disponibles"
                print(error_msg)
                error_handler.handle_error(
                    error_msg,
                    category=ErrorCategory.TTS,
                    severity=ErrorSeverity.CRITICAL,
                    notify_user=True,
                    context={"tried_engines": ['gtts', 'pyttsx3', 'macos_say', 'espeak']}
                )
                
                if 'web_interface' in sys.modules:
                    from web_interface import log_to_web
                    log_to_web("Impossible de lire le texte. Tous les moteurs de synthèse vocale ont échoué.", "error")
        except Exception as fallback_error:
            error_msg = f"Échec critique de la récupération TTS: {str(fallback_error)}"
            print(error_msg)
            error_handler.handle_error(
                fallback_error,
                category=ErrorCategory.TTS,
                severity=ErrorSeverity.CRITICAL,
                notify_user=True,
                context={"action": "récupération après erreur"}
            )

def preparer_feedback_court(message):
    """
    Prépare un message court pour un feedback vocal rapide
    Génère l'audio en arrière-plan pour une lecture immédiate quand nécessaire
    """
    global feedback_court_message, feedback_court_pret, feedback_court_audio_file
    
    # Mémoriser le message
    feedback_court_message = message
    feedback_court_pret = False
    
    # Créer un thread pour générer l'audio en arrière-plan
    def generer_audio_background():
        global feedback_court_pret, feedback_court_audio_file
        
        try:
            # Créer un fichier temporaire pour l'audio
            import tempfile
            import os
            temp_file = os.path.join(tempfile.gettempdir(), f'feedback_rapide_{time.time()}.mp3')
            
            # Générer l'audio avec la méthode la plus rapide disponible
            if gTTS is not None:
                # Utiliser gTTS avec mise en cache et paramètres optimisés
                tts = gTTS(text=message, lang='fr', slow=False)
                tts.save(temp_file)
                
                # Marquer comme prêt
                feedback_court_audio_file = temp_file
                feedback_court_pret = True
                print(f"Audio de feedback rapide préparé: {message}")
            else:
                # Si gTTS n'est pas disponible, nous utiliserons pyttsx3 ou une autre méthode disponible
                feedback_court_pret = True
                print(f"Audio de feedback rapide prêt à être synthétisé: {message}")
        except Exception as e:
            print(f"Erreur lors de la préparation du feedback rapide: {e}")
            feedback_court_pret = False
    
    # Lancer la génération en arrière-plan
    import threading
    prep_thread = threading.Thread(target=generer_audio_background)
    prep_thread.daemon = True
    prep_thread.start()

def jouer_feedback_court():
    """
    Joue le feedback court précédemment préparé
    Cette fonction doit être appelée après un preparer_feedback_court()
    """
    global feedback_court_message, feedback_court_pret, feedback_court_audio_file
    
    # Si le feedback n'est pas encore prêt, l'ajouter à la file d'attente normale
    if not feedback_court_pret:
        print("Feedback rapide non prêt, utilisation de la méthode standard")
        ajouter_texte_a_lire(feedback_court_message)
        return
    
    # Si l'audio est disponible, le jouer immédiatement
    if feedback_court_audio_file and os.path.exists(feedback_court_audio_file):
        try:
            # Vérifier si pygame est disponible
            if pygame and ensure_pygame_initialized():
                try:
                    # Jouer le fichier audio pré-généré
                    pygame.mixer.music.load(feedback_court_audio_file)
                    pygame.mixer.music.play()
                    print(f"Lecture immédiate du feedback: {feedback_court_message}")
                    
                    # Lancer un thread pour nettoyer le fichier après lecture
                    def cleanup_after_playback():
                        try:
                            # Attendre la fin de la lecture
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)
                            
                            # Nettoyer le fichier
                            if os.path.exists(feedback_court_audio_file):
                                os.remove(feedback_court_audio_file)
                        except:
                            pass
                    
                    cleanup_thread = threading.Thread(target=cleanup_after_playback)
                    cleanup_thread.daemon = True
                    cleanup_thread.start()
                    
                    return
                except Exception as e:
                    print(f"Erreur lors de la lecture du feedback rapide avec pygame: {e}")
            
            # Si pygame échoue, utiliser la méthode standard
            ajouter_texte_a_lire(feedback_court_message)
            
        except Exception as e:
            print(f"Erreur lors de la lecture du feedback rapide: {e}")
            ajouter_texte_a_lire(feedback_court_message)
    else:
        # Si l'audio n'est pas disponible, utiliser la méthode standard
        ajouter_texte_a_lire(feedback_court_message)

def ajouter_texte_a_lire(texte):
    """Ajoute du texte à la file d'attente pour lecture"""
    if not texte:
        return
    
    # S'assurer que le thread TTS est en cours d'exécution
    initialiser_tts()
    
    # Ajouter le texte à la file d'attente
    tts_queue.put(texte)
    print(f"Texte ajouté à la file d'attente TTS: {texte[:50]}...")

def arreter_tts():
    """Arrête le thread TTS"""
    global tts_thread_running, tts_engine
    
    tts_thread_running = False
    
    # Arrêter proprement le moteur TTS
    if tts_engine is not None:
        try:
            tts_engine.stop()
        except:
            pass
        tts_engine = None
    
    print("Thread TTS arrêté")

def arreter_tts_immediatement():
    """Arrête immédiatement le TTS et libère toutes les ressources"""
    global tts_thread_running, tts_engine, tts_queue, tts_is_speaking
    
    # Arrêter tous les flags
    tts_thread_running = False
    tts_is_speaking = False
    
    # Vider la file d'attente
    while not tts_queue.empty():
        try:
            tts_queue.get_nowait()
            tts_queue.task_done()
        except:
            pass
    
    # Arrêter le moteur TTS de manière forcée
    if tts_engine is not None:
        try:
            tts_engine.stop()
        except:
            pass
        
        try:
            # Libérer explicitement les ressources
            del tts_engine
        except:
            pass
        
        tts_engine = None
    
    print("TTS arrêté immédiatement")

def interrompre_lecture():
    """Interrompt la lecture TTS en cours"""
    global tts_is_speaking, tts_engine, tts_queue, tts_engine_type
    
    # Arrêter la lecture en cours
    tts_is_speaking = False
    
    # Vider la file d'attente des messages à lire
    while not tts_queue.empty():
        try:
            tts_queue.get_nowait()
            tts_queue.task_done()
        except:
            pass
    
    # Arrêter le moteur TTS en fonction du type avec gestion d'erreur robuste
    try:
        if tts_engine_type in ['gtts', 'coqui']:
            # Arrêter la lecture pygame
            try:
                pygame.mixer.music.stop()
            except Exception as e:
                print(f"Erreur lors de l'arrêt de pygame.mixer.music: {e}")
                
            # Réinitialiser pygame pour éviter les problèmes
            try:
                pygame.mixer.quit()
                time.sleep(0.1)  # Petit délai pour laisser les ressources se libérer
                pygame.mixer.init(frequency=44100, buffer=2048)
            except Exception as e:
                print(f"Erreur lors de la réinitialisation de pygame: {e}")
                
            # Essayer d'arrêter sounddevice si utilisé comme alternative
            try:
                import sounddevice as sd
                sd.stop()
            except:
                pass
                
        elif tts_engine_type == 'macos_say':
            # Arrêter tous les processus 'say' en cours
            try:
                subprocess.run(["killall", "say"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Erreur lors de l'arrêt des processus 'say': {e}")
                
        elif tts_engine_type == 'espeak':
            # Arrêter tous les processus espeak en cours
            try:
                subprocess.run(["killall", "espeak"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Erreur lors de l'arrêt des processus 'espeak': {e}")
                
        else:
            # Arrêter et réinitialiser complètement le moteur pyttsx3
            if tts_engine is not None:
                try:
                    tts_engine.stop()
                except Exception as e:
                    print(f"Erreur lors de l'arrêt du moteur pyttsx3: {e}")
                
                # Détruire et recréer le moteur pour éviter les problèmes de blocage
                try:
                    del tts_engine
                except:
                    pass
                
                tts_engine = None
                
                # Réinitialiser immédiatement le moteur
                try:
                    initialiser_moteur_tts()
                except Exception as e:
                    print(f"Erreur lors de la réinitialisation du moteur pyttsx3: {e}")
    
    except Exception as e:
        print(f"Erreur lors de l'interruption de la lecture TTS: {e}")
    
    print(f"Lecture TTS ({tts_engine_type}) interrompue")
    return True

def est_commande_arret_tts(texte):
    """Vérifie si le texte est une commande d'arrêt du TTS"""
    texte_lower = texte.lower().strip()
    
    # Liste des commandes d'arrêt exactes
    commandes_arret_exactes = [
        "stop", "arrête", "pause", "ok", "j'ai compris", 
        "ça suffit", "c'est bon", "merci", "tais-toi", 
        "silence", "chut", "assez", "stop tts", "arrête tts"
    ]
    
    # Vérifier les correspondances exactes
    if texte_lower in commandes_arret_exactes:
        return True
    
    # Vérifier si la commande commence par un mot d'arrêt
    mots_debut = ["stop", "arrête", "pause", "tais", "chut", "silence"]
    for mot in mots_debut:
        if texte_lower.startswith(mot):
            return True
    
    return False

# Paramètres de vitesse pour les différents moteurs TTS
tts_rate = {
    'pyttsx3': 180,  # Valeur par défaut
    'gtts': 1.4,     # Facteur de vitesse (1.0 = normal, 1.4 = 40% plus rapide)
    'macos_say': 180,  # Mots par minute
    'espeak': 160,   # Mots par minute
    'coqui': 1.0  # Facteur de vitesse pour CoquiTTS (1.0 = normal)
}

# Cette ligne est maintenant définie dans la section d'importation

def definir_vitesse_tts(vitesse, moteur=None):
    """
    Définit la vitesse de lecture pour le moteur TTS spécifié
    
    Args:
        vitesse: Valeur de vitesse (dépend du moteur)
        moteur: Type de moteur TTS (si None, utilise le moteur actuel)
    
    Returns:
        bool: True si la vitesse a été définie avec succès, False sinon
    """
    global tts_rate, tts_engine, tts_engine_type
    
    if moteur is None:
        moteur = tts_engine_type
    
    if moteur not in tts_rate:
        print(f"Moteur TTS non reconnu: {moteur}")
        return False
    
    # Mettre à jour la vitesse pour le moteur spécifié
    tts_rate[moteur] = vitesse
    
    # Appliquer immédiatement la vitesse si le moteur est pyttsx3
    if moteur == 'pyttsx3' and tts_engine is not None:
        try:
            tts_engine.setProperty('rate', vitesse)
            print(f"Vitesse du moteur {moteur} définie sur: {vitesse}")
            return True
        except Exception as e:
            print(f"Erreur lors de la définition de la vitesse: {e}")
            return False
    
    # Pour gTTS, limiter la vitesse à une plage raisonnable
    if moteur == 'gtts':
        # Limiter entre 0.8 (plus lent) et 2.0 (deux fois plus rapide)
        if vitesse < 0.8:
            tts_rate[moteur] = 0.8
            print(f"Vitesse gTTS limitée à 0.8 (minimum)")
        elif vitesse > 2.0:
            tts_rate[moteur] = 2.0
            print(f"Vitesse gTTS limitée à 2.0 (maximum)")
    
    print(f"Vitesse du moteur {moteur} définie sur: {tts_rate[moteur]}")
    return True

def definir_coqui_model(model_id):
    """Change le modèle Coqui TTS à utiliser"""
    global coqui_model, coqui_model_name, coqui_available, coqui_model_id
    
    if not coqui_available:
        print("CoquiTTS n'est pas disponible sur ce système")
        return False
    
    # Vérifier si le modèle existe
    model_found = False
    selected_model = None
    for model in COQUI_MODELS:
        if model["id"] == model_id:
            model_found = True
            selected_model = model
            break
    
    if not model_found:
        print(f"Modèle Coqui TTS non reconnu: {model_id}")
        print(f"Modèles disponibles: {', '.join([m['id'] for m in COQUI_MODELS])}")
        return False
    
    # Si le modèle est déjà chargé, ne rien faire
    if coqui_model_id == model_id and coqui_model is not None:
        print(f"Le modèle {model_id} est déjà chargé")
        return True
    
    # Libérer le modèle actuel si nécessaire
    if coqui_model is not None:
        try:
            # Libérer explicitement les ressources
            del coqui_model
            coqui_model = None
        except:
            pass
    
    # Charger le nouveau modèle
    print(f"Chargement du modèle {model_id}...")
    
    # Mettre à jour l'ID du modèle immédiatement pour que les autres fonctions sachent quel modèle est en cours de chargement
    coqui_model_id = model_id
    
    try:
        # Charger le modèle directement pour s'assurer qu'il est disponible pour le feedback vocal
        model_name = selected_model["name"]
        description = selected_model["description"]
        
        print(f"Chargement du modèle {description}...")
        
        # Désactiver les avertissements pendant le chargement du modèle
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            coqui_model = TTS_API(model_name=model_name, progress_bar=False)
        
        print(f"Modèle {description} chargé avec succès")
        coqui_model_name = description
        
        return True
    except Exception as e:
        print(f"Erreur lors du chargement du modèle {model_id}: {e}")
        
        # En cas d'erreur, essayer de charger un modèle de secours en arrière-plan
        import threading
        
        def load_fallback_model():
            try:
                load_coqui_model_fallback()
                print("Modèle de secours chargé avec succès")
            except Exception as fallback_error:
                print(f"Erreur lors du chargement du modèle de secours: {fallback_error}")
        
        fallback_thread = threading.Thread(target=load_fallback_model)
        fallback_thread.daemon = True
        fallback_thread.start()
        
        return False

def definir_moteur_tts(type_moteur):
    """Définit le moteur TTS à utiliser"""
    global tts_engine_type, coqui_available
    
    # Vérifier la disponibilité du moteur demandé avec gestion d'erreur
    try:
        if type_moteur == 'pyttsx3':
            if pyttsx3 is None:
                print("Module pyttsx3 non disponible")
                # Suggérer l'installation
                print("Vous pouvez l'installer avec: pip install pyttsx3")
                return False
        elif type_moteur == 'gtts':
            if gTTS is None:
                print("Module gTTS non disponible")
                # Suggérer l'installation
                print("Vous pouvez l'installer avec: pip install gTTS pygame")
                return False
            # Vérifier si pygame est disponible pour la lecture
            if not pygame_initialized:
                if not ensure_pygame_initialized():
                    print("Pygame n'est pas correctement initialisé pour gTTS")
                    print("Vous pouvez réinstaller pygame avec: pip install pygame --upgrade")
                    return False
        elif type_moteur == 'macos_say':
            if not is_mac():
                print("Commande 'say' disponible uniquement sur macOS")
                return False
            # Vérifier si la commande 'say' est disponible
            try:
                subprocess.run(["say", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except:
                print("Commande 'say' non disponible sur ce système macOS")
                return False
        elif type_moteur == 'espeak':
            if not is_linux():
                print("Commande 'espeak' principalement disponible sur Linux")
                return False
            # Vérifier si espeak est installé
            try:
                subprocess.run(["espeak", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            except:
                print("Commande 'espeak' non disponible. Installez-la avec 'sudo apt-get install espeak'")
                return False
        elif type_moteur == 'coqui':
            if not coqui_available:
                print("Module Coqui TTS non disponible.")
                print("Vous pouvez l'installer avec: pip install TTS numpy==1.24.3")
                return False
            
            # Vérifier si pygame est disponible pour la lecture
            if not pygame_initialized:
                if not ensure_pygame_initialized():
                    print("Pygame n'est pas correctement initialisé pour Tacotron")
                    print("Vous pouvez réinstaller pygame avec: pip install pygame --upgrade")
                    return False
        else:
            print(f"Type de moteur TTS non reconnu: {type_moteur}")
            print("Moteurs disponibles: pyttsx3, gtts, macos_say (macOS), espeak (Linux), coqui")
            return False
        
        # Définir le moteur si disponible
        if type_moteur in ['pyttsx3', 'gtts', 'macos_say', 'espeak', 'coqui']:
            # Si on passe à CoquiTTS, précharger le modèle en arrière-plan
            if type_moteur == 'coqui':
                print("Préchargement du modèle CoquiTTS en arrière-plan...")
                
                # Utiliser un thread pour ne pas bloquer l'application
                import threading
                
                def preload_coqui():
                    try:
                        # Désactiver les avertissements pendant le chargement
                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore")
                            load_coqui_model()
                        print("Modèle CoquiTTS préchargé avec succès")
                    except Exception as e:
                        print(f"Erreur lors du préchargement du modèle CoquiTTS: {e}")
                        print("CoquiTTS sera chargé à la première utilisation")
                
                preload_thread = threading.Thread(target=preload_coqui)
                preload_thread.daemon = True
                preload_thread.start()
            
            # Interrompre toute lecture en cours avant de changer de moteur
            interrompre_lecture()
            
            # Définir le nouveau moteur
            tts_engine_type = type_moteur
            print(f"Moteur TTS défini sur: {type_moteur}")
            
            # Sauvegarder dans la base de données
            try:
                from config import save_preference
                save_preference("tts_engine", type_moteur)
                print(f"Moteur TTS sauvegardé dans la base de données: {type_moteur}")
            except Exception as e:
                print(f"Erreur lors de la sauvegarde du moteur TTS dans la base de données: {e}")
            
            return True
    
    except Exception as e:
        print(f"Erreur lors du changement de moteur TTS: {e}")
        return False

def obtenir_moteur_tts():
    """Retourne le type de moteur TTS actuellement utilisé"""
    global tts_engine_type
    # Essayer de charger depuis la base de données
    try:
        from config import get_preference
        saved_engine = get_preference("tts_engine")
        if saved_engine:
            return saved_engine
    except Exception as e:
        print(f"Erreur lors de la récupération du moteur TTS depuis la base de données: {e}")
    
    # Retourner la valeur en mémoire si la base de données n'est pas disponible
    return tts_engine_type
