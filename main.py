"""
Point d'entrée principal de l'assistant vocal Whisp
"""

import time
import sys
import os
import warnings
import threading
import signal

# Supprimer les avertissements concernant ffmpeg
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv")

# Correction pour NeMo sur Windows
if not hasattr(signal, 'SIGKILL'):
    signal.SIGKILL = signal.SIGTERM

# Importer le module de chargement paresseux
from lazy_loader import lazy_import, background_load

# Imports essentiels pour le démarrage
from os_detection import get_os_type
from config import running, set_running, get_running
from web_interface import start_web_server, log_to_web, command_to_web, response_to_web

# Importer le processeur de commandes
from command_processor import CommandProcessor

# Importer speech_recognition de manière paresseuse
sr = lazy_import('speech_recognition')

# Précharger certains modules en arrière-plan pendant que l'interface démarre
background_threads = []

# Définir une fonction de secours pour arreter_threads_reconnaissance
def _dummy_arreter_threads():
    print("Fonction de secours: arrêt des threads de reconnaissance")

# Variable globale pour stocker la fonction
arreter_threads_reconnaissance = _dummy_arreter_threads

# Fonction pour charger le module de reconnaissance vocale à la demande
def load_speech_recognition_module():
    global arreter_threads_reconnaissance
    
    try:
        # Import conditionnel pour éviter les erreurs d'importation
        from speech_recognition_module import setup_recognition, start_continuous_listening
        from speech_recognition_module import arreter_threads_reconnaissance as real_arreter_threads
        # Remplacer la fonction de secours par la vraie fonction
        arreter_threads_reconnaissance = real_arreter_threads
        return setup_recognition, start_continuous_listening
    except Exception as e:
        print(f"Erreur lors de l'importation du module de reconnaissance vocale: {e}")
        print("Tentative de correction...")
        
        # Forcer l'utilisation de SpeechRecognition
        from config import set_stt_engine
        set_stt_engine("speechrecognition")
        
        # Réessayer l'importation
        try:
            from speech_recognition_module import setup_recognition, start_continuous_listening
            from speech_recognition_module import arreter_threads_reconnaissance as real_arreter_threads
            # Remplacer la fonction de secours par la vraie fonction
            arreter_threads_reconnaissance = real_arreter_threads
            return setup_recognition, start_continuous_listening
        except Exception as e:
            print(f"Échec de la réimportation: {e}")
            print("Utilisation de fonctions de secours")
            return None, None

def assistant_vocal():
    """Fonction principale de l'assistant vocal"""
    
    # Mesurer le temps de démarrage
    start_time = time.time()
    
    # Définir l'état initial à running
    set_running(True)
    
    # Démarrer l'interface web en premier pour montrer rapidement quelque chose à l'utilisateur
    print("Démarrage de l'interface web...")
    start_web_server()
    
    # Journaliser le démarrage
    log_to_web("Assistant vocal en cours d'initialisation...", "info")
    log_to_web("Interface web disponible à l'adresse http://localhost:5000", "info")
    
    # Détecter et afficher le système d'exploitation
    os_type = get_os_type()
    log_to_web(f"Système d'exploitation détecté: {os_type.capitalize()}", "info")
    print(f"Système d'exploitation détecté: {os_type.capitalize()}")
    
    # Précharger certains modules en arrière-plan
    print("Préchargement des modules en arrière-plan...")
    background_threads.append(background_load('speech_recognition_module'))
    background_threads.append(background_load('tts_module'))
    
    # Vérifier si ffmpeg est installé (en arrière-plan)
    def check_ffmpeg():
        try:
            import subprocess
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Avertissement: ffmpeg n'est pas installé. Certaines fonctionnalités audio pourraient ne pas fonctionner correctement.")
            print("Exécutez 'python whisp_assistant\\install_ffmpeg.py' pour installer ffmpeg.")
            log_to_web("Avertissement: ffmpeg n'est pas installé. Certaines fonctionnalités audio pourraient ne pas fonctionner correctement.", "warning")
    
    # Démarrer la vérification de ffmpeg en arrière-plan
    threading.Thread(target=check_ffmpeg, daemon=True).start()
    
    # Initialisation du processeur de commandes (variable globale)
    global command_processor
    command_processor = CommandProcessor()
    
    # Charger le module de reconnaissance vocale à la demande
    setup_recognition, start_continuous_listening = load_speech_recognition_module()
    
    if setup_recognition is None:
        log_to_web("Erreur critique: Impossible de charger le module de reconnaissance vocale", "error")
        print("Erreur critique: Impossible de charger le module de reconnaissance vocale")
        return
    
    # Initialisation du recognizer et du microphone
    print("Initialisation du recognizer et du microphone...")
    recognizer, microphone, _ = setup_recognition()
    
    # S'assurer que tous les threads précédents sont arrêtés
    arreter_threads_reconnaissance()
    
    # Initialisation du TTS de manière progressive
    def init_tts():
        try:
            # Import à la demande pour réduire le temps de démarrage
            from tts_module import initialiser_tts, definir_moteur_tts, coqui_available, load_coqui_model, lire_texte
            
            print("Initialisation du moteur TTS...")
            initialiser_tts()
            
            # Utiliser directement gTTS pour une meilleure fiabilité
            print("Utilisation de gTTS comme moteur TTS principal pour une meilleure fiabilité")
            definir_moteur_tts('gtts')
            
            # Précharger le modèle CoquiTTS en arrière-plan si disponible
            if coqui_available:
                print("Préchargement du modèle CoquiTTS en arrière-plan...")
                
                def preload_tts_model():
                    try:
                        model, _ = load_coqui_model()
                        if model is not None:
                            # Obtenir le nom du modèle directement depuis la fonction
                            model_name = model.model_name if hasattr(model, 'model_name') else "modèle inconnu"
                            print(f"Modèle CoquiTTS préchargé avec succès: {model_name}")
                            log_to_web(f"Modèle CoquiTTS préchargé: {model_name}", "info")
                        else:
                            print("Échec du préchargement du modèle CoquiTTS")
                    except Exception as e:
                        print(f"Erreur lors du préchargement du modèle CoquiTTS: {e}")
                
                # Démarrer le préchargement en arrière-plan
                threading.Thread(target=preload_tts_model, daemon=True).start()
            else:
                print("CoquiTTS non disponible sur ce système")
                
            print("Moteur TTS initialisé avec succès")
            
            # Tester avec une phrase courte
            lire_texte("L'assistant vocal est prêt.")
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'initialisation du TTS : {e}")
            print("Utilisation du moteur TTS par défaut")
            try:
                from tts_module import definir_moteur_tts
                definir_moteur_tts('gtts')
            except:
                pass
            return False
    
    # Initialiser le TTS en arrière-plan
    tts_thread = threading.Thread(target=init_tts, daemon=True)
    tts_thread.start()
    
    # Afficher les instructions pendant que le TTS s'initialise
    print("Assistant vocal prêt. Parlez maintenant...")
    print("Interface web disponible à l'adresse http://localhost:5000")
    print("Dites 'écris' ou 'dictée' pour commencer la dictée, puis 'fin de dictée' pour terminer.")
    print("Dites 'aide' pour connaître les commandes générales disponibles.")
    print("Dites 'aide développeur' pour les commandes spécifiques au développement.")
    print("Dites 'quitte l'assistant' pour arrêter le programme.")
    
    # Attendre que le TTS soit initialisé avant de démarrer l'écoute
    tts_thread.join(timeout=5.0)  # Attendre max 5 secondes
    
    # Démarrage de l'écoute continue en arrière-plan avec traitement asynchrone
    print("Démarrage de l'écoute continue...")
    stop_listening = start_continuous_listening(recognizer, microphone, command_processor)
    
    # Calculer et afficher le temps de démarrage
    startup_time = time.time() - start_time
    print(f"Assistant vocal démarré en {startup_time:.2f} secondes")
    log_to_web(f"Assistant vocal démarré en {startup_time:.2f} secondes", "info")
    
    # Configurer un gestionnaire de signal pour CTRL+C
    import signal
    
    def signal_handler(sig, frame):
        print("\nInterruption par l'utilisateur - Arrêt immédiat...")
        set_running(False)
        
        # Arrêter le TTS immédiatement sans attendre
        try:
            from tts_module import arreter_tts_immediatement
            arreter_tts_immediatement()
        except Exception:
            pass
        
        # Arrêter l'écoute sans attendre
        if stop_listening:
            stop_listening(wait_for_stop=False)
        
        # Forcer l'arrêt des threads de reconnaissance vocale
        try:
            arreter_threads_reconnaissance()
        except Exception:
            pass
        
        print("Assistant vocal arrêté.")
        
        # Forcer la sortie immédiate du programme
        os._exit(0)
    
    # Installer le gestionnaire de signal
    signal.signal(signal.SIGINT, signal_handler)
    
    # Maintenir le programme en cours d'exécution
    try:
        print("Assistant vocal en écoute continue. Utilisez Ctrl+C pour quitter.")
        while get_running():
            time.sleep(0.1)
            # Vérifier périodiquement si l'état a changé
            if not get_running():
                print("Arrêt demandé par commande vocale")
                break
    finally:
        # Arrêt de l'écoute en arrière-plan
        set_running(False)
        
        # Arrêter le TTS immédiatement
        try:
            from tts_module import arreter_tts_immediatement
            print("Arrêt du moteur TTS...")
            arreter_tts_immediatement()
        except Exception as e:
            print(f"Erreur lors de l'arrêt du TTS : {e}")
        
        # Arrêter l'écoute sans attendre
        if stop_listening:
            stop_listening(wait_for_stop=False)
            
        # Forcer l'arrêt des threads de reconnaissance vocale
        try:
            arreter_threads_reconnaissance()
        except Exception as e:
            print(f"Erreur lors de l'arrêt des threads: {e}")
        
        print("Assistant vocal arrêté.")
        
        # Forcer la sortie du programme
        print("Sortie du programme...")
        os._exit(0)  # Utiliser os._exit() pour une sortie immédiate et fiable

if __name__ == "__main__":
    assistant_vocal()
