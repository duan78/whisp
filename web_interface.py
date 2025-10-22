"""
Module d'interface web pour l'assistant vocal Whisp
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import threading
import queue
import time
import json
import os
import sys
import traceback
import traceback
from datetime import datetime
from bug_tracker import bug_tracker
from config import (
    get_running, set_running, 
    get_stt_engine, set_stt_engine,
    get_openai_api_key, set_openai_api_key,
    get_mistral_api_key, set_mistral_api_key
)
from tts_module import obtenir_moteur_tts, definir_moteur_tts
from speech_recognition_module import get_stt_metrics, reset_stt_metrics
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Importer les modules de sécurité
try:
    from input_validation import (
        ValidationError, 
        InputValidator
    )
    from api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys
    security_available = True
except ImportError:
    security_available = False
    print("Modules de sécurité non disponibles")

# File d'attente pour les messages à afficher dans l'interface web
web_message_queue = queue.Queue()

# Créer l'application Flask
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Variable pour stocker l'état de l'assistant
assistant_state = {
    "running": True,
    "last_command": "",
    "last_response": "",
    "logs": [],
    "errors": []  # Nouvel attribut pour stocker les erreurs récentes
}

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

def add_log(message, type="info"):
    """Ajoute un message au journal des logs"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "type": type  # info, command, response, error, warning
    }
    assistant_state["logs"].append(log_entry)
    # Limiter le nombre de logs à 100 entrées
    if len(assistant_state["logs"]) > 100:
        assistant_state["logs"] = assistant_state["logs"][-100:]
    
    # Si c'est une erreur, l'ajouter aussi à la liste des erreurs
    if type == "error":
        assistant_state["errors"].append(log_entry)
        # Limiter le nombre d'erreurs à 20 entrées
        if len(assistant_state["errors"]) > 20:
            assistant_state["errors"] = assistant_state["errors"][-20:]
    
    # Ajouter à la file d'attente pour SSE
    web_message_queue.put(json.dumps({"type": "log", "data": log_entry}))
    
    # Si c'est une erreur ou un avertissement, enregistrer également dans le gestionnaire d'erreurs
    if type in ["error", "warning"]:
        severity = ErrorSeverity.MEDIUM if type == "error" else ErrorSeverity.LOW
        error_handler.handle_error(
            message,
            category=ErrorCategory.WEB_INTERFACE,
            severity=severity,
            notify_user=False,  # Déjà notifié via l'interface web
            context={"source": "web_interface", "function": "add_log"}
        )
    
    # Enregistrer le log dans la base de données
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import save_web_log
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import save_web_log
        
        # Enregistrer le log dans la base de données
        save_web_log(timestamp, message, type)
    except Exception as e:
        # Ne pas bloquer l'application si l'enregistrement en base échoue
        print(f"Erreur lors de l'enregistrement du log en base de données: {e}")

def add_command(command):
    """Enregistre une commande utilisateur"""
    assistant_state["last_command"] = command
    add_log(f"Commande: {command}", "command")
    # Envoyer directement la commande pour mise à jour en temps réel
    web_message_queue.put(json.dumps({"type": "command", "data": command}))

def add_response(response):
    """Enregistre une réponse de l'assistant"""
    if response:
        assistant_state["last_response"] = response
        add_log(f"Réponse: {response}", "response")
        # Envoyer directement la réponse pour mise à jour en temps réel
        web_message_queue.put(json.dumps({"type": "response", "data": response}))

def start_web_server(host='0.0.0.0', port=5000):
    """Démarre le serveur web dans un thread séparé"""
    # Enregistrer l'interface web auprès du gestionnaire d'erreurs
    error_handler.register_web_interface(sys.modules[__name__])
    
    # Démarrer le serveur dans un thread séparé
    threading.Thread(target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False),
                    daemon=True).start()
    
    print(f"Interface web disponible à l'adresse http://{host}:{port}")
    add_log(f"Interface web démarrée sur http://{host}:{port}", "info")

@app.route('/')
def index():
    """Page d'accueil de l'interface web"""
    return render_template('index.html')

@app.route('/presentation')
def presentation():
    """Page de présentation de l'assistant"""
    return render_template('presentation.html')

@app.route('/roadmap')
def roadmap():
    """Page de roadmap des fonctionnalités futures"""
    return render_template('roadmap.html')

@app.route('/bugs')
def bugs():
    """Page d'analyse des bugs et incohérences"""
    # Récupérer les erreurs récentes depuis le gestionnaire d'erreurs
    recent_errors = error_handler.get_error_history(limit=20)
    
    # Formater les timestamps pour un affichage plus lisible
    for error in recent_errors:
        if 'timestamp' in error:
            try:
                # Convertir le timestamp ISO en objet datetime
                dt = datetime.fromisoformat(error['timestamp'])
                # Formater pour l'affichage
                error['timestamp'] = dt.strftime('%d/%m/%Y %H:%M:%S')
            except (ValueError, TypeError):
                # En cas d'erreur, garder le timestamp original
                pass
    
    # Récupérer les tickets de bugs
    bug_tickets = bug_tracker.get_all_tickets()
    
    return render_template('bugs.html', errors=recent_errors, bug_tickets=bug_tickets)

@app.route('/finetune')
def finetune():
    """Page de gestion des données pour le fine-tuning des modèles de reconnaissance vocale.
    Cette page n'est pas référencée dans le menu et est accessible uniquement via l'URL."""
    try:
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            return render_template('finetune.html', error="Dossier records non trouvé", samples=[])
        
        # Récupérer la liste des échantillons
        samples = []
        
        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]
        
        for engine in engines:
            engine_dir = os.path.join(records_dir, engine)
            
            # Parcourir récursivement tous les fichiers JSON
            for root, dirs, files in os.walk(engine_dir):
                json_files = [f for f in files if f.endswith('.json')]
                
                for json_file in json_files:
                    json_path = os.path.join(root, json_file)
                    
                    try:
                        # Charger les métadonnées depuis le fichier JSON
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Obtenir le chemin du fichier audio
                        audio_file = metadata.get("audio_file")
                        if not audio_file:
                            continue
                            
                        audio_path = os.path.join(os.path.dirname(json_path), audio_file)
                        
                        # Obtenir le chemin du fichier texte (transcription)
                        base_name = os.path.splitext(audio_file)[0]
                        text_file = f"{base_name}.txt"
                        text_path = os.path.join(os.path.dirname(json_path), text_file)
                        
                        # Vérifier que les fichiers existent
                        if not os.path.exists(audio_path) or not os.path.exists(text_path):
                            continue
                        
                        # Lire le contenu du fichier texte
                        with open(text_path, 'r', encoding='utf-8') as f:
                            transcription = f.read().strip()
                        
                        # Déterminer le split (train, validation, test)
                        split_dir = os.path.basename(os.path.dirname(json_path))
                        split = split_dir if split_dir in ["train", "validation", "test"] else "unknown"
                        
                        # Déterminer les chemins relatifs pour le frontend
                        rel_audio_path = os.path.relpath(audio_path, os.getcwd())
                        rel_json_path = os.path.relpath(json_path, os.getcwd())
                        rel_text_path = os.path.relpath(text_path, os.getcwd())
                        
                        # Ajouter l'échantillon à la liste
                        sample = {
                            "id": f"{engine}_{os.path.basename(audio_path)}",
                            "engine": engine,
                            "split": split,
                            "transcription": transcription,
                            "audio_path": rel_audio_path.replace("\\", "/"),
                            "json_path": rel_json_path.replace("\\", "/"),
                            "text_path": rel_text_path.replace("\\", "/"),
                            "timestamp": metadata.get("timestamp", 0),
                            "duration": metadata.get("duration", 0),
                            "metadata": metadata
                        }
                        
                        samples.append(sample)
                    except Exception as e:
                        print(f"Erreur lors du traitement du fichier {json_path}: {e}")
                        continue
        
        # Tri des échantillons par timestamp (du plus récent au plus ancien)
        samples.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return render_template('finetune.html', samples=samples, error=None)
    except Exception as e:
        print(f"Erreur lors du chargement de la page finetune: {e}")
        import traceback
        traceback.print_exc()
        return render_template('finetune.html', error=str(e), samples=[])

@app.route('/config')
def config():
    """Page de configuration de l'assistant"""
    return render_template('config.html')

@app.route('/records/<path:filename>')
def serve_records(filename):
    """Sert les fichiers du dossier records"""
    records_dir = os.path.join(os.getcwd(), "records")
    return Response(open(os.path.join(records_dir, filename), 'rb').read(),
                    mimetype='audio/wav')

@app.route('/aliases')
def aliases():
    """Page de gestion des alias de commandes"""
    try:
        # Importer le module des alias de commandes
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.command_aliases import command_aliases
        except ImportError:
            # Sinon, utiliser l'import relatif
            from command_aliases import command_aliases
            
        # Récupérer tous les alias pour les passer au template
        all_aliases = command_aliases.aliases
        
        # Obtenir la liste des commandes uniques pour le menu déroulant
        unique_commands = sorted(list(all_aliases.keys()))
        
        return render_template('aliases.html', 
                              commands=unique_commands,
                              aliases=all_aliases)
    except Exception as e:
        add_log(f"Erreur lors du chargement de la page des alias: {str(e)}", "error")
        return render_template('aliases.html')

@app.route('/status')
def status():
    """Retourne l'état actuel de l'assistant"""
    tts_engine = obtenir_moteur_tts()
    
    # Récupérer les informations sur le modèle Coqui si c'est le moteur actuel
    coqui_model_info = None
    if tts_engine == 'coqui':
        try:
            from tts_module import get_current_coqui_model
            coqui_model_info = get_current_coqui_model()
        except:
            pass
    
    return jsonify({
        "running": get_running(),
        "last_command": assistant_state["last_command"],
        "last_response": assistant_state["last_response"],
        "logs": assistant_state["logs"][-20:],  # Retourner seulement les 20 derniers logs
        "stt_engine": get_stt_engine(),
        "tts_engine": tts_engine,
        "coqui_model": coqui_model_info,
        "stt_metrics": get_stt_metrics()
    })

@app.route('/toggle', methods=['POST'])
def toggle():
    """Active ou désactive l'assistant"""
    current_state = get_running()
    set_running(not current_state)
    new_state = get_running()
    
    if new_state:
        add_log("Assistant activé", "info")
    else:
        add_log("Assistant désactivé", "info")
    
    # Envoyer l'état mis à jour via SSE
    status_data = {
        "running": new_state,
        "last_command": assistant_state["last_command"],
        "last_response": assistant_state["last_response"],
        "stt_engine": get_stt_engine(),
        "tts_engine": obtenir_moteur_tts()
    }
    web_message_queue.put(json.dumps({"type": "status", "data": status_data}))
    
    return jsonify({"success": True, "running": new_state})

@app.route('/change_stt_engine', methods=['POST'])
@app.route('/set_stt_engine', methods=['POST'])  # Route alternative pour compatibilité
def change_stt_engine_route():
    """Change le moteur de reconnaissance vocale"""
    try:
        data = request.json
        engine = data.get('engine')
        
        if engine not in ['speechrecognition', 'whisper', 'vosk', 'whisper_ct2', 'whisper_french']:
            return jsonify({"success": False, "error": "Moteur STT non valide"})
        
        # Vérifier si Vosk est disponible
        if engine == 'vosk':
            try:
                from speech_recognition_module import VOSK_AVAILABLE, setup_vosk_model
                if not VOSK_AVAILABLE:
                    return jsonify({
                        "success": False, 
                        "error": "Vosk n'est pas installé. Veuillez l'installer avec 'pip install vosk'"
                    })
                
                # Vérifier si le modèle Vosk est disponible ou peut être téléchargé
                add_log("Vérification du modèle Vosk...", "info")
                model_ready = setup_vosk_model()
                if not model_ready:
                    return jsonify({
                        "success": False,
                        "error": "Impossible de charger ou télécharger le modèle Vosk. Vérifiez les logs pour plus de détails."
                    })
                add_log("Modèle Vosk prêt à l'emploi", "info")
            except ImportError:
                return jsonify({
                    "success": False, 
                    "error": "Vosk n'est pas installé. Veuillez l'installer avec 'pip install vosk'"
                })
        
        
        # Vérifier si Whisper CT2 est disponible
        if engine == 'whisper_ct2':
            try:
                from speech_recognition_module import WHISPER_CT2_AVAILABLE, setup_whisper_ct2_model
                if not WHISPER_CT2_AVAILABLE:
                    return jsonify({
                        "success": False, 
                        "error": "Whisper CT2 n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper'"
                    })
                
                # Vérifier si le modèle Whisper CT2 est disponible ou peut être téléchargé
                add_log("Vérification du modèle Whisper CT2...", "info")
                model_ready = setup_whisper_ct2_model()
                if not model_ready:
                    return jsonify({
                        "success": False,
                        "error": "Impossible de charger ou télécharger le modèle Whisper CT2. Vérifiez les logs pour plus de détails."
                    })
                add_log("Modèle Whisper CT2 prêt à l'emploi", "info")
            except ImportError:
                return jsonify({
                    "success": False, 
                    "error": "Whisper CT2 n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper'"
                })
                
        # Vérifier si Whisper French est disponible
        if engine == 'whisper_french':
            try:
                from speech_recognition_module import WHISPER_CT2_AVAILABLE, setup_whisper_french_model
                if not WHISPER_CT2_AVAILABLE:
                    return jsonify({
                        "success": False, 
                        "error": "Whisper French n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper huggingface_hub'"
                    })
                
                # Vérifier si le modèle Whisper French est disponible ou peut être téléchargé
                add_log("Vérification du modèle Whisper French...", "info")
                model_ready = setup_whisper_french_model()
                if not model_ready:
                    return jsonify({
                        "success": False,
                        "error": "Impossible de charger ou télécharger le modèle Whisper French. Vérifiez les logs pour plus de détails."
                    })
                add_log("Modèle Whisper French prêt à l'emploi", "info")
            except ImportError:
                return jsonify({
                    "success": False, 
                    "error": "Whisper French n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper huggingface_hub'"
                })
                
        # Vérifier si Whisper French est disponible
        if engine == 'whisper_french':
            try:
                from speech_recognition_module import WHISPER_CT2_AVAILABLE, setup_whisper_french_model
                if not WHISPER_CT2_AVAILABLE:
                    return jsonify({
                        "success": False, 
                        "error": "Whisper French n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper huggingface_hub'"
                    })
                
                # Vérifier si le modèle Whisper French est disponible ou peut être téléchargé
                add_log("Vérification du modèle Whisper French...", "info")
                model_ready = setup_whisper_french_model()
                if not model_ready:
                    return jsonify({
                        "success": False,
                        "error": "Impossible de charger ou télécharger le modèle Whisper French. Vérifiez les logs pour plus de détails."
                    })
                add_log("Modèle Whisper French prêt à l'emploi", "info")
            except ImportError:
                return jsonify({
                    "success": False, 
                    "error": "Whisper French n'est pas installé. Veuillez l'installer avec 'pip install ctranslate2 faster-whisper huggingface_hub'"
                })
        
        # Vérifier si la clé API OpenAI est configurée pour Whisper
        if engine == 'whisper':
            api_key = get_openai_api_key()
            if not api_key:
                return jsonify({
                    "success": False,
                    "error": "Clé API OpenAI non configurée. Veuillez la configurer dans les paramètres."
                })
            else:
                # Vérifier le format de la clé API
                if not api_key.startswith('sk-') or len(api_key) < 30:
                    return jsonify({
                        "success": False,
                        "error": "Format de clé API OpenAI invalide. La clé doit commencer par 'sk-'."
                    })
                add_log(f"Clé API OpenAI valide détectée: {api_key[:4]}...{api_key[-4:]}", "info")
        
        # Vérifier si le moteur est déjà celui sélectionné
        current_engine = get_stt_engine()
        if current_engine == engine:
            add_log(f"Le moteur STT est déjà configuré sur {engine}", "info")
            return jsonify({"success": True, "engine": engine})
        
        # Changer le moteur sans arrêter l'assistant
        try:
            # Importer la fonction pour arrêter les threads existants
            from speech_recognition_module import arreter_threads_reconnaissance
            
            # Arrêter d'abord tous les threads de reconnaissance vocale existants
            add_log("Arrêt des threads de reconnaissance vocale existants...", "info")
            arreter_threads_reconnaissance()
            
            # Changer le moteur STT
            add_log(f"Changement du moteur STT vers {engine}...", "info")
            try:
                success = set_stt_engine(engine)
            
                if not success:
                    add_log(f"Échec du changement de moteur STT vers {engine}", "error")
                    return jsonify({"success": False, "error": f"Échec du changement de moteur STT vers {engine}"})
            except Exception as e:
                add_log(f"Exception lors du changement de moteur STT: {str(e)}", "error")
                # Continuer malgré l'erreur, car set_stt_engine peut avoir réussi même si une exception est levée
                # Vérifier si le moteur a bien été changé
                current_engine = get_stt_engine()
                if current_engine == engine:
                    add_log(f"Le moteur STT a été changé avec succès malgré l'erreur", "info")
                    success = True
                else:
                    return jsonify({"success": False, "error": f"Exception: {str(e)}"})
        except Exception as e:
            add_log(f"Exception lors du changement de moteur STT: {str(e)}", "error")
            return jsonify({"success": False, "error": f"Exception: {str(e)}"})
        
        # Notifier le changement de moteur
        if success:
            engine_names = {
                "speechrecognition": "SpeechRecognition (par lot)",
                "nemo": "NVIDIA NeMo (continu)",
                "whisper": "OpenAI Whisper API (continu)",
                "vosk": "Vosk (continu, hors ligne)",
                "sherpa_ncnn": "Sherpa NCNN (continu, hors ligne)",
                "whisper_ct2": "Whisper CT2 (continu, hors ligne)",
                "whisper_french": "Whisper French (continu, optimisé pour le français)"
            }
            engine_name = engine_names.get(engine, engine)
            add_log(f"Moteur STT changé pour: {engine_name}", "info")
            
            # Importer les fonctions nécessaires en dehors du bloc try
            from speech_recognition_module import redemarrer_reconnaissance_vocale
            
            # Redémarrer la reconnaissance vocale sans arrêter l'assistant
            try:
                # Vérifier que le moteur a bien été changé
                current_engine = get_stt_engine()  # Utilise l'import global en haut du fichier
                if current_engine != engine:
                    add_log(f"Erreur: Le moteur n'a pas été correctement changé. Attendu: {engine}, Actuel: {current_engine}", "error")
                    return jsonify({"success": False, "error": f"Échec du changement de moteur STT. Le moteur actuel est {current_engine}."})
                
                # Essayer de récupérer le processeur de commandes
                try:
                    # D'abord essayer de l'importer depuis main
                    try:
                        import main
                        if hasattr(main, 'command_processor'):
                            print("Processeur de commandes trouvé dans main.py")
                            success = redemarrer_reconnaissance_vocale(main.command_processor)
                        else:
                            raise AttributeError("command_processor non trouvé dans main.py")
                    except (ImportError, AttributeError):
                        # Ensuite, essayer de créer une nouvelle instance
                        from command_processor import CommandProcessor
                        cmd_processor = CommandProcessor()
                        print("Nouvelle instance de CommandProcessor créée pour le redémarrage")
                        success = redemarrer_reconnaissance_vocale(cmd_processor)
                except Exception as e:
                    print(f"Erreur lors de la récupération du processeur de commandes: {e}")
                    add_log(f"Tentative de redémarrage sans processeur de commandes", "warning")
                    # Dernière tentative sans processeur
                    success = redemarrer_reconnaissance_vocale()
                if success:
                    add_log(f"Reconnaissance vocale redémarrée avec le moteur {engine}", "info")
                else:
                    add_log(f"Échec du redémarrage de la reconnaissance vocale avec le moteur {engine}", "error")
                    return jsonify({"success": False, "error": "Échec du redémarrage de la reconnaissance vocale"})
            except Exception as e:
                add_log(f"Erreur lors du redémarrage de la reconnaissance vocale: {str(e)}", "error")
                return jsonify({"success": False, "error": f"Erreur: {str(e)}"})
            
            return jsonify({"success": True, "engine": engine})
        else:
            return jsonify({"success": False, "error": "Échec du changement de moteur STT"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """Configure une clé API"""
    try:
        # Validation des données
        if not request.is_json:
            return jsonify({'error': 'Content-Type doit être application/json'}), 400
        
        data = request.json
        api_type = data.get('type')
        api_key = data.get('key', '')
        
        # Valider les entrées si le module est disponible
        if security_available:
            try:
                api_type = InputValidator.sanitize_string(api_type, max_length=20)
                if api_key:
                    api_key = InputValidator.validate_api_key(api_key)
            except ValidationError as e:
                return jsonify({"success": False, "error": str(e)}), 400
        
        if api_type == 'openai':
            # Vérifier le format de la clé API OpenAI
            if api_key and (not api_key.startswith('sk-') or len(api_key) < 30):
                add_log(f"Format de clé API OpenAI invalide. La clé doit commencer par 'sk-'.", "error")
                return jsonify({"success": False, "error": "Format de clé API OpenAI invalide. La clé doit commencer par 'sk-'."})
            
            # Stocker de manière sécurisée si disponible
            if security_available and api_key:
                set_secure_api_key('openai', api_key)
            
            success = set_openai_api_key(api_key)
            if success:
                # Vérifier que la clé est bien définie comme variable d'environnement
                env_key = os.environ.get("OPENAI_API_KEY", "")
                if api_key and not env_key:
                    add_log(f"Avertissement: La clé API OpenAI n'a pas été correctement définie comme variable d'environnement", "warning")
                else:
                    add_log(f"Clé API OpenAI configurée et définie comme variable d'environnement OPENAI_API_KEY", "info")
                
                # Vérifier si le moteur actuel est Whisper et redémarrer si nécessaire
                if get_stt_engine() == 'whisper':
                    try:
                        from speech_recognition_module import redemarrer_reconnaissance_vocale
                        redemarrer_reconnaissance_vocale()
                        add_log("Reconnaissance vocale redémarrée avec la nouvelle clé API", "info")
                    except Exception as e:
                        add_log(f"Erreur lors du redémarrage de la reconnaissance vocale: {str(e)}", "error")
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Échec de la configuration de la clé API OpenAI"})
        elif api_type == 'mistral':
            # Vérifier le format de la clé API Mistral
            if api_key and len(api_key) < 20:
                add_log(f"Format de clé API Mistral potentiellement invalide. Veuillez vérifier votre clé.", "warning")
            
            # Stocker de manière sécurisée si disponible
            if security_available and api_key:
                set_secure_api_key('mistral', api_key)
            
            success = set_mistral_api_key(api_key)
            if success:
                # Vérifier que la clé est bien définie comme variable d'environnement
                env_key = os.environ.get("MISTRAL_API_KEY", "")
                if api_key and not env_key:
                    add_log(f"Avertissement: La clé API Mistral n'a pas été correctement définie comme variable d'environnement", "warning")
                    return jsonify({"success": False, "error": "La clé API Mistral n'a pas été correctement définie comme variable d'environnement"})
                
                add_log(f"Clé API Mistral configurée et définie comme variable d'environnement MISTRAL_API_KEY", "info")
                
                # Afficher la clé masquée pour le débogage
                masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
                add_log(f"Clé API Mistral définie: {masked_key}", "info")
                
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "error": "Échec de la configuration de la clé API Mistral"})
        else:
            return jsonify({"success": False, "error": "Type d'API non valide"})
    except Exception as e:
        add_log(f"Erreur lors de la configuration de la clé API: {str(e)}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_api_keys', methods=['GET'])
def get_api_keys():
    """Récupère les clés API configurées (masquées)"""
    try:
        openai_key = get_openai_api_key()
        mistral_key = get_mistral_api_key()
        
        # Masquer les clés pour la sécurité
        masked_openai = "•••••••••••••••••••••••" if openai_key else ""
        masked_mistral = "•••••••••••••••••••••••" if mistral_key else ""
        
        return jsonify({
            "success": True,
            "openai": masked_openai,
            "mistral": masked_mistral
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_stt_metrics', methods=['GET'])
def get_stt_metrics_route():
    """Récupère les métriques de performance STT"""
    try:
        # Vérifier si on demande l'historique
        history = request.args.get('history', 'false').lower() == 'true'
        engine = request.args.get('engine', None)
        
        if history:
            try:
                # Importer le module de base de données
                try:
                    # Essayer d'abord l'import en tant que package
                    from whisp_assistant.database_manager import get_stt_metrics_history
                except ImportError:
                    # Sinon, utiliser l'import relatif
                    from database_manager import get_stt_metrics_history
                
                # Récupérer l'historique des métriques
                metrics_history = get_stt_metrics_history(engine=engine, limit=50)
                
                return jsonify({
                    "success": True,
                    "history": metrics_history
                })
            except Exception as e:
                print(f"Erreur lors de la récupération de l'historique des métriques: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"success": False, "error": str(e)})
        else:
            # Récupérer les métriques actuelles depuis la base de données
            metrics = get_stt_metrics(from_db=True)
            return jsonify({
                "success": True,
                "metrics": metrics
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    """Récupère les logs de l'assistant"""
    try:
        # Récupérer le nombre de logs demandés (par défaut 50)
        count = request.args.get('count', 50, type=int)
        # Limiter à 100 logs maximum pour des raisons de performance
        count = min(count, 100)
        
        # Vérifier si on demande les logs depuis la base de données
        from_db = request.args.get('from_db', 'false').lower() == 'true'
        
        if from_db:
            # Récupérer les logs depuis la base de données
            try:
                # Importer le module de base de données
                try:
                    # Essayer d'abord l'import en tant que package
                    from whisp_assistant.database_manager import get_web_logs
                except ImportError:
                    # Sinon, utiliser l'import relatif
                    from database_manager import get_web_logs
                
                # Récupérer les logs depuis la base de données
                logs = get_web_logs(limit=count)
                
                return jsonify({
                    "success": True,
                    "logs": logs,
                    "source": "database"
                })
            except Exception as e:
                # En cas d'erreur, revenir aux logs en mémoire
                print(f"Erreur lors de la récupération des logs depuis la base de données: {e}")
                logs = assistant_state["logs"][-count:] if count > 0 else []
                
                return jsonify({
                    "success": True,
                    "logs": logs,
                    "source": "memory",
                    "error": f"Erreur lors de la récupération depuis la base de données: {str(e)}"
                })
        else:
            # Utiliser les logs en mémoire
            logs = assistant_state["logs"][-count:] if count > 0 else []
            
            return jsonify({
                "success": True,
                "logs": logs,
                "source": "memory"
            })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_logs"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_errors', methods=['GET'])
def get_errors():
    """Récupère l'historique des erreurs"""
    try:
        # Récupérer le nombre d'erreurs demandées (par défaut 20)
        count = request.args.get('count', 20, type=int)
        category = request.args.get('category', None)
        
        # Récupérer les erreurs depuis le gestionnaire d'erreurs
        errors = error_handler.get_error_history(limit=count, category=category)
        
        # Récupérer aussi les erreurs de l'interface web
        web_errors = assistant_state["errors"]
        
        return jsonify({
            "success": True,
            "system_errors": errors,
            "web_errors": web_errors
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Routes pour la gestion des tickets de bugs
@app.route('/api/bug_tickets', methods=['GET'])
def get_bug_tickets():
    """Récupère tous les tickets de bugs"""
    try:
        tickets = bug_tracker.get_all_tickets()
        return jsonify({
            "success": True,
            "tickets": tickets
        })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/api/bug_tickets"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bug_tickets/<ticket_id>', methods=['GET'])
def get_bug_ticket(ticket_id):
    """Récupère un ticket spécifique"""
    try:
        ticket = bug_tracker.get_ticket(ticket_id)
        if ticket:
            return jsonify({
                "success": True,
                "ticket": ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bug_tickets', methods=['POST'])
def create_bug_ticket():
    """Crée un nouveau ticket de bug"""
    try:
        data = request.json
        
        # Vérifier les champs requis
        required_fields = ["title", "description", "category", "priority"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Champ requis manquant: {field}"
                }), 400
        
        # Créer le ticket
        ticket = bug_tracker.create_ticket(
            title=data["title"],
            description=data["description"],
            steps=data.get("steps", ""),
            category=data["category"],
            priority=data["priority"]
        )
        
        add_log(f"Nouveau ticket de bug créé: {ticket['title']}", "info")
        
        return jsonify({
            "success": True,
            "ticket": ticket
        }), 201
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/api/bug_tickets"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bug_tickets/<ticket_id>', methods=['PUT'])
def update_bug_ticket(ticket_id):
    """Met à jour un ticket existant"""
    try:
        data = request.json
        
        # Vérifier si le ticket existe
        ticket = bug_tracker.get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404
        
        # Mettre à jour le ticket
        success = bug_tracker.update_ticket(ticket_id, **data)
        
        if success:
            add_log(f"Ticket de bug mis à jour: {ticket_id}", "info")
            updated_ticket = bug_tracker.get_ticket(ticket_id)
            return jsonify({
                "success": True,
                "ticket": updated_ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la mise à jour du ticket"
            }), 400
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bug_tickets/<ticket_id>/comments', methods=['POST'])
def add_bug_ticket_comment(ticket_id):
    """Ajoute un commentaire à un ticket"""
    try:
        data = request.json
        
        # Vérifier si le ticket existe
        ticket = bug_tracker.get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404
        
        # Vérifier le champ requis
        if "text" not in data:
            return jsonify({
                "success": False,
                "error": "Champ requis manquant: text"
            }), 400
        
        # Ajouter le commentaire
        success = bug_tracker.add_comment(ticket_id, data["text"])
        
        if success:
            add_log(f"Commentaire ajouté au ticket: {ticket_id}", "info")
            updated_ticket = bug_tracker.get_ticket(ticket_id)
            return jsonify({
                "success": True,
                "ticket": updated_ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de l'ajout du commentaire"
            }), 400
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}/comments"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/bug_tickets/<ticket_id>', methods=['DELETE'])
def delete_bug_ticket(ticket_id):
    """Supprime un ticket"""
    try:
        # Vérifier si le ticket existe
        ticket = bug_tracker.get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404
        
        # Supprimer le ticket
        success = bug_tracker.delete_ticket(ticket_id)
        
        if success:
            add_log(f"Ticket de bug supprimé: {ticket_id}", "info")
            return jsonify({
                "success": True
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la suppression du ticket"
            }), 400
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/reset_stt_metrics', methods=['POST'])
def reset_metrics():
    """Réinitialise les métriques de performance STT"""
    try:
        reset_stt_metrics()
        add_log("Métriques STT réinitialisées", "info")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/restart_recognition', methods=['POST'])
def restart_recognition():
    """Redémarre la reconnaissance vocale"""
    try:
        from speech_recognition_module import redemarrer_reconnaissance_vocale
        success = redemarrer_reconnaissance_vocale()
        
        if success:
            add_log("Reconnaissance vocale redémarrée avec succès", "info")
            return jsonify({"success": True})
        else:
            add_log("Échec du redémarrage de la reconnaissance vocale", "error")
            return jsonify({"success": False, "error": "Échec du redémarrage"})
    except Exception as e:
        add_log(f"Erreur lors du redémarrage de la reconnaissance vocale: {str(e)}", "error")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_coqui_models', methods=['GET'])
def get_coqui_models_route():
    """Récupère la liste des modèles Coqui TTS disponibles"""
    try:
        from tts_module import get_coqui_models, get_current_coqui_model
        
        models = get_coqui_models()
        current_model = get_current_coqui_model()
        
        return jsonify({
            "success": True,
            "models": models,
            "current_model": current_model
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/change_coqui_model', methods=['POST'])
def change_coqui_model():
    """Change le modèle Coqui TTS à utiliser"""
    try:
        data = request.json
        model_id = data.get('model_id')
        
        if not model_id:
            return jsonify({"success": False, "error": "ID de modèle non spécifié"})
        
        from tts_module import definir_coqui_model, get_current_coqui_model, get_coqui_model_description, lire_texte
        
        # Vérifier si le modèle est déjà celui sélectionné
        current_model = get_current_coqui_model()
        if current_model == model_id:
            add_log(f"Le modèle Coqui TTS est déjà configuré sur {model_id}", "info")
            return jsonify({"success": True, "model_id": model_id})
        
        # Changer le modèle Coqui TTS
        success = definir_coqui_model(model_id)
        
        if success:
            add_log(f"Modèle Coqui TTS changé pour: {model_id}", "info")
            
            # Obtenir la description du modèle pour le feedback vocal
            model_description = get_coqui_model_description(model_id)
            
            # Ajouter un feedback vocal avec le nouveau modèle
            # Utiliser un thread pour ne pas bloquer la réponse HTTP
            import threading
            def announce_model_change():
                # Attendre un peu pour laisser le temps au modèle de se charger
                import time
                time.sleep(1)
                lire_texte(f"Assistant vocal démarré avec {model_description}")
            
            # Démarrer le thread pour le feedback vocal
            announce_thread = threading.Thread(target=announce_model_change)
            announce_thread.daemon = True
            announce_thread.start()
            
            return jsonify({"success": True, "model_id": model_id})
        else:
            return jsonify({"success": False, "error": f"Échec du changement de modèle Coqui TTS vers {model_id}"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/change_tts_engine', methods=['POST'])
@app.route('/set_tts_engine', methods=['POST'])  # Route alternative pour compatibilité
def change_tts_engine():
    """Change le moteur de synthèse vocale"""
    try:
        data = request.json
        engine = data.get('engine')
        
        if engine not in ['pyttsx3', 'gtts', 'coqui']:
            return jsonify({"success": False, "error": "Moteur TTS non valide"})
        
        # Vérifier si le moteur est déjà celui sélectionné
        current_engine = obtenir_moteur_tts()
        if current_engine == engine:
            add_log(f"Le moteur TTS est déjà configuré sur {engine}", "info")
            return jsonify({"success": True, "engine": engine})
        
        # Changer le moteur TTS
        success = definir_moteur_tts(engine)
        
        if success:
            engine_names = {
                "pyttsx3": "Windows TTS (natif)",
                "gtts": "Google TTS (en ligne)",
                "coqui": "CoquiTTS (haute qualité)"
            }
            engine_name = engine_names.get(engine, engine)
            add_log(f"Moteur TTS changé pour: {engine_name}", "info")
            
            # Annoncer le changement de moteur avec le nouveau moteur
            from tts_module import lire_texte, coqui_model_name
            if engine == 'coqui' and coqui_model_name:
                lire_texte(f"Assistant vocal démarré avec {coqui_model_name}")
            else:
                lire_texte(f"Assistant vocal démarré avec {engine_name}")
                
            return jsonify({"success": True, "engine": engine})
        else:
            return jsonify({"success": False, "error": "Échec du changement de moteur TTS"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Routes pour la gestion des préférences utilisateur
@app.route('/get_preferences', methods=['GET'])
def get_preferences_route():
    """Récupère les préférences utilisateur"""
    try:
        from config import get_all_preferences, get_preference
        
        # Récupérer une préférence spécifique si demandée
        key = request.args.get('key', None)
        if key:
            value = get_preference(key)
            return jsonify({
                "success": True,
                "key": key,
                "value": value
            })
        
        # Sinon, récupérer toutes les préférences
        preferences = get_all_preferences()
        return jsonify({
            "success": True,
            "preferences": preferences
        })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_preferences"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/set_preference', methods=['POST'])
def set_preference_route():
    """Définit une préférence utilisateur"""
    try:
        from config import save_preference
        
        data = request.json
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({"success": False, "error": "Clé de préférence non spécifiée"})
        
        # Sauvegarder la préférence
        save_preference(key, value)
        add_log(f"Préférence '{key}' définie avec succès", "info")
        
        return jsonify({
            "success": True,
            "key": key,
            "value": value
        })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/set_preference"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_stt_settings', methods=['GET'])
def get_stt_settings_route():
    """Récupère les paramètres de reconnaissance vocale"""
    try:
        # Importer le module de reconnaissance vocale
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.speech_recognition_module import get_stt_settings, DEFAULT_STT_SETTINGS
        except ImportError:
            # Sinon, utiliser l'import relatif
            from speech_recognition_module import get_stt_settings, DEFAULT_STT_SETTINGS
        
        # Récupérer les paramètres
        settings = get_stt_settings()
        
        return jsonify({
            "success": True,
            "settings": settings,
            "default_settings": DEFAULT_STT_SETTINGS
        })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_stt_settings"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_stt_setting', methods=['POST'])
def update_stt_setting_route():
    """Met à jour un paramètre de reconnaissance vocale"""
    try:
        # Importer le module de reconnaissance vocale
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.speech_recognition_module import update_stt_setting
        except ImportError:
            # Sinon, utiliser l'import relatif
            from speech_recognition_module import update_stt_setting
        
        data = request.json
        key = data.get('key')
        value = data.get('value')
        
        if not key:
            return jsonify({"success": False, "error": "Clé de paramètre non spécifiée"})
        
        # Mettre à jour le paramètre
        success = update_stt_setting(key, value)
        
        if success:
            add_log(f"Paramètre STT '{key}' mis à jour avec succès", "info")
            return jsonify({
                "success": True,
                "key": key,
                "value": value
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de la mise à jour du paramètre STT '{key}'"
            })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/update_stt_setting"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/reset_stt_settings', methods=['POST'])
def reset_stt_settings_route():
    """Réinitialise les paramètres de reconnaissance vocale aux valeurs par défaut"""
    try:
        # Importer les modules nécessaires
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.speech_recognition_module import DEFAULT_STT_SETTINGS, update_stt_setting
        except ImportError:
            # Sinon, utiliser l'import relatif
            from speech_recognition_module import DEFAULT_STT_SETTINGS, update_stt_setting
        
        # Réinitialiser chaque paramètre
        for key, value in DEFAULT_STT_SETTINGS.items():
            update_stt_setting(key, value)
        
        add_log("Paramètres STT réinitialisés aux valeurs par défaut", "info")
        
        return jsonify({
            "success": True,
            "settings": DEFAULT_STT_SETTINGS
        })
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/reset_stt_settings"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_all_config', methods=['GET'])
def get_all_config():
    """Récupère toutes les configurations de l'application depuis la base de données"""
    try:
        # Importer les modules nécessaires
        from config import get_all_preferences, get_stt_engine, get_running
        from tts_module import obtenir_moteur_tts, get_coqui_models, get_current_coqui_model
        
        # Récupérer les préférences utilisateur
        preferences = get_all_preferences()
        
        # Récupérer les métriques STT
        metrics = get_stt_metrics()
        
        # Récupérer les erreurs récentes
        errors = error_handler.get_error_history(limit=10)
        
        # Récupérer les logs web
        try:
            from database_manager import get_web_logs
            logs = get_web_logs(limit=20)
        except:
            logs = []
        
        # Récupérer les informations sur les moteurs et paramètres STT
        stt_engine = get_stt_engine()
        tts_engine = obtenir_moteur_tts()
        
        # Récupérer les paramètres STT
        stt_settings = {}
        try:
            from speech_recognition_module import get_stt_settings
            stt_settings = get_stt_settings()
        except:
            pass
        
        # Récupérer les informations sur les modèles Coqui
        coqui_models = []
        current_coqui_model = None
        try:
            coqui_models = get_coqui_models()
            current_coqui_model = get_current_coqui_model()
        except:
            pass
        
        # Récupérer les informations sur les clés API
        api_keys = {
            "openai": bool(get_openai_api_key()),
            "mistral": bool(get_mistral_api_key())
        }
        
        # Récupérer les alias de commandes
        command_aliases = {}
        try:
            from command_aliases import command_aliases as aliases_manager
            command_aliases = aliases_manager.aliases
        except:
            pass
        
        # Récupérer les tickets de bugs
        bug_tickets = []
        try:
            from bug_tracker import bug_tracker
            bug_tickets = bug_tracker.get_all_tickets()
        except:
            pass
        
        # Récupérer les informations sur les raccourcis clavier
        shortcuts = {}
        try:
            from shortcuts_database import get_all_shortcuts
            shortcuts = get_all_shortcuts()
        except:
            pass
        
        # Récupérer les informations sur les tâches
        tasks = []
        try:
            from project_management_commands import load_tasks
            tasks_data = load_tasks()
            if tasks_data and "tasks" in tasks_data:
                tasks = tasks_data["tasks"]
        except:
            pass
        
        # Récupérer les informations sur les rappels
        reminders = []
        try:
            from reminder_commands import load_reminders
            reminders_data = load_reminders()
            if reminders_data and "reminders" in reminders_data:
                reminders = reminders_data["reminders"]
        except:
            pass
            
        # Récupérer les informations système
        system_info = {}
        try:
            import platform
            import sys
            
            system_info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "python_version": sys.version,
                "python_path": sys.executable
            }
            
            # Ajouter des informations sur la mémoire si psutil est disponible
            try:
                import psutil
                system_info.update({
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                    "memory_total_formatted": f"{psutil.virtual_memory().total / (1024*1024*1024):.2f} GB",
                    "memory_available": psutil.virtual_memory().available,
                    "memory_available_formatted": f"{psutil.virtual_memory().available / (1024*1024*1024):.2f} GB"
                })
            except ImportError:
                pass
            
            # Ajouter des informations sur le GPU
            try:
                # Vérifier si CUDA est disponible via torch
                gpu_info = {"available": False}
                
                # Essayer d'abord avec nvidia-smi (plus fiable pour la détection)
                try:
                    import subprocess
                    # Vérifier si nvidia-smi est disponible
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,driver_version,cuda_version', '--format=csv,noheader,nounits'], 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        gpu_data = result.stdout.strip().split(',')
                        gpu_info["available"] = True
                        gpu_info["name"] = gpu_data[0].strip()
                        
                        # Convertir les valeurs de mémoire en octets
                        memory_total = int(gpu_data[1].strip()) * 1024 * 1024  # MiB to bytes
                        memory_used = int(gpu_data[2].strip()) * 1024 * 1024
                        memory_free = int(gpu_data[3].strip()) * 1024 * 1024
                        
                        gpu_info["memory_total"] = memory_total
                        gpu_info["memory_total_formatted"] = f"{memory_total / (1024*1024*1024):.2f} GB"
                        gpu_info["memory_allocated"] = memory_used
                        gpu_info["memory_allocated_formatted"] = f"{memory_used / (1024*1024*1024):.2f} GB"
                        gpu_info["memory_free"] = memory_free
                        gpu_info["memory_free_formatted"] = f"{memory_free / (1024*1024*1024):.2f} GB"
                        gpu_info["memory_usage_percent"] = int((memory_used / memory_total) * 100)
                        
                        # Informations sur les versions
                        gpu_info["driver_version"] = gpu_data[4].strip() if len(gpu_data) > 4 else "Inconnu"
                        gpu_info["cuda_version"] = gpu_data[5].strip() if len(gpu_data) > 5 else "Inconnu"
                        
                        print(f"GPU détecté via nvidia-smi: {gpu_info['name']}")
                except (subprocess.SubprocessError, FileNotFoundError, IndexError) as e:
                    print(f"Erreur lors de l'exécution de nvidia-smi: {e}")
                    
                    # Si nvidia-smi échoue, essayer avec torch
                    try:
                        import torch
                        cuda_available = torch.cuda.is_available()
                        gpu_info["available"] = cuda_available
                        
                        if cuda_available:
                            gpu_info["count"] = torch.cuda.device_count()
                            gpu_info["name"] = torch.cuda.get_device_name(0)
                            gpu_info["cuda_version"] = torch.version.cuda
                            
                            # Obtenir la mémoire GPU si disponible
                            try:
                                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory
                                gpu_memory_allocated = torch.cuda.memory_allocated(0)
                                gpu_memory_reserved = torch.cuda.memory_reserved(0)
                                gpu_memory_free = gpu_memory_total - gpu_memory_reserved
                                
                                gpu_info["memory_total"] = gpu_memory_total
                                gpu_info["memory_total_formatted"] = f"{gpu_memory_total / (1024*1024*1024):.2f} GB"
                                gpu_info["memory_allocated"] = gpu_memory_allocated
                                gpu_info["memory_allocated_formatted"] = f"{gpu_memory_allocated / (1024*1024*1024):.2f} GB"
                                gpu_info["memory_free"] = gpu_memory_free
                                gpu_info["memory_free_formatted"] = f"{gpu_memory_free / (1024*1024*1024):.2f} GB"
                                gpu_info["memory_usage_percent"] = int((gpu_memory_allocated / gpu_memory_total) * 100)
                                
                                print(f"GPU détecté via torch: {gpu_info['name']}")
                            except Exception as e:
                                print(f"Erreur lors de la récupération des informations de mémoire GPU via torch: {e}")
                    except ImportError:
                        print("Torch n'est pas installé, impossible de détecter le GPU via torch")
                
                # Essayer avec GPUtil comme méthode de secours
                if not gpu_info["available"]:
                    try:
                        import GPUtil
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            gpu = gpus[0]  # Prendre le premier GPU
                            gpu_info["available"] = True
                            gpu_info["name"] = gpu.name
                            
                            # Convertir les valeurs de mémoire en octets
                            memory_total = gpu.memoryTotal * 1024 * 1024  # MiB to bytes
                            memory_used = gpu.memoryUsed * 1024 * 1024
                            memory_free = memory_total - memory_used
                            
                            gpu_info["memory_total"] = memory_total
                            gpu_info["memory_total_formatted"] = f"{memory_total / (1024*1024*1024):.2f} GB"
                            gpu_info["memory_allocated"] = memory_used
                            gpu_info["memory_allocated_formatted"] = f"{memory_used / (1024*1024*1024):.2f} GB"
                            gpu_info["memory_free"] = memory_free
                            gpu_info["memory_free_formatted"] = f"{memory_free / (1024*1024*1024):.2f} GB"
                            gpu_info["memory_usage_percent"] = int((memory_used / memory_total) * 100)
                            
                            print(f"GPU détecté via GPUtil: {gpu_info['name']}")
                    except (ImportError, Exception) as e:
                        print(f"Erreur lors de la détection du GPU via GPUtil: {e}")
                
                system_info["gpu"] = gpu_info
            except Exception as e:
                print(f"Erreur lors de la récupération des informations GPU: {e}")
                system_info["gpu"] = {"available": False, "error": str(e)}
                
        except Exception as e:
            print(f"Erreur lors de la récupération des informations système: {e}")
            system_info = {
                "os": platform.system() if 'platform' in sys.modules else "Inconnu",
                "os_version": platform.version() if 'platform' in sys.modules else "Inconnu",
                "python_version": sys.version
            }
            
        # Récupérer les informations sur la base de données
        db_info = {}
        try:
            from database_manager import get_db_info
            db_info = get_db_info()
        except Exception as e:
            print(f"Erreur lors de la récupération des informations de la base de données: {e}")
            # Informations minimales sur la base de données
            import os
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whisp_data.db")
            db_info = {
                "path": db_path,
                "exists": os.path.exists(db_path),
                "size": os.path.getsize(db_path) if os.path.exists(db_path) else 0
            }
        
        # Construire la réponse
        response = {
            "success": True,
            "preferences": preferences,
            "metrics": metrics,
            "errors": errors,
            "logs": logs,
            "engines": {
                "stt": stt_engine,
                "tts": tts_engine,
                "stt_settings": stt_settings
            },
            "coqui": {
                "models": coqui_models,
                "current_model": current_coqui_model
            },
            "api_keys": api_keys,
            "command_aliases": command_aliases,
            "bug_tickets": bug_tickets,
            "shortcuts": shortcuts,
            "tasks": tasks,
            "reminders": reminders,
            "running": get_running(),
            "system_info": system_info,
            "db_info": db_info
        }
        
        return jsonify(response)
    except Exception as e:
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_all_config"}
        )
        return jsonify({"success": False, "error": str(e)})

# Routes pour la gestion des alias de commandes
@app.route('/get_custom_shortcuts', methods=['GET'])
def get_custom_shortcuts_route():
    """Récupère les raccourcis vocaux personnalisés"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import get_custom_shortcuts
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import get_custom_shortcuts
        
        # Récupérer un type d'action spécifique si demandé
        action_type = request.args.get('action_type', None)
        
        # Récupérer les raccourcis
        shortcuts = get_custom_shortcuts(action_type=action_type)
        
        return jsonify({
            "success": True,
            "shortcuts": shortcuts
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des raccourcis personnalisés: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_custom_shortcuts"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_custom_shortcut', methods=['POST'])
def add_custom_shortcut_route():
    """Ajoute un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import save_custom_shortcut
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import save_custom_shortcut
        
        data = request.json
        name = data.get('name')
        voice_command = data.get('voice_command')
        action_type = data.get('action_type')
        action_data = data.get('action_data')
        
        print(f"Tentative d'ajout de raccourci personnalisé: nom='{name}', commande='{voice_command}'")
        
        if not name or not voice_command or not action_type or not action_data:
            return jsonify({"success": False, "error": "Tous les champs sont requis"})
        
        # Sauvegarder le raccourci
        shortcut_id = save_custom_shortcut(name, voice_command, action_type, action_data)
        
        if shortcut_id:
            add_log(f"Raccourci personnalisé '{name}' ajouté avec la commande '{voice_command}'", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id,
                "name": name,
                "voice_command": voice_command
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Échec de l'ajout du raccourci. La commande vocale '{voice_command}' existe peut-être déjà."
            })
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/add_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/update_custom_shortcut', methods=['POST'])
def update_custom_shortcut_route():
    """Met à jour un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import update_custom_shortcut
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import update_custom_shortcut
        
        data = request.json
        shortcut_id = data.get('id')
        name = data.get('name')
        voice_command = data.get('voice_command')
        action_type = data.get('action_type')
        action_data = data.get('action_data')
        
        if not shortcut_id:
            return jsonify({"success": False, "error": "ID du raccourci non spécifié"})
        
        # Mettre à jour le raccourci
        success = update_custom_shortcut(
            shortcut_id, 
            name=name, 
            voice_command=voice_command, 
            action_type=action_type, 
            action_data=action_data
        )
        
        if success:
            add_log(f"Raccourci personnalisé mis à jour: ID {shortcut_id}", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Échec de la mise à jour du raccourci. La commande vocale existe peut-être déjà."
            })
    except Exception as e:
        print(f"Erreur lors de la mise à jour d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/update_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/delete_custom_shortcut', methods=['POST'])
def delete_custom_shortcut_route():
    """Supprime un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import delete_custom_shortcut
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import delete_custom_shortcut
        
        data = request.json
        shortcut_id = data.get('id')
        
        if not shortcut_id:
            return jsonify({"success": False, "error": "ID du raccourci non spécifié"})
        
        # Supprimer le raccourci
        success = delete_custom_shortcut(shortcut_id)
        
        if success:
            add_log(f"Raccourci personnalisé supprimé: ID {shortcut_id}", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Échec de la suppression du raccourci. ID {shortcut_id} non trouvé."
            })
    except Exception as e:
        print(f"Erreur lors de la suppression d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/delete_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_command_aliases', methods=['GET'])
def get_command_aliases_route():
    """Récupère les alias de commandes"""
    try:
        # Importer le module des alias de commandes
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.command_aliases import command_aliases
        except ImportError:
            # Sinon, utiliser l'import relatif
            from command_aliases import command_aliases
        
        # Récupérer une commande spécifique si demandée
        command = request.args.get('command', None)
        if command:
            aliases = command_aliases.get_aliases_for_command(command)
            return jsonify({
                "success": True,
                "command": command,
                "aliases": aliases
            })
        
        # Sinon, récupérer tous les alias
        all_aliases = command_aliases.aliases
        print(f"Alias récupérés: {len(all_aliases)} commandes")
        
        # Convertir le dictionnaire en format plus adapté pour le frontend
        formatted_aliases = {}
        for command, alias_list in all_aliases.items():
            formatted_aliases[command] = sorted(alias_list)
        
        return jsonify({
            "success": True,
            "aliases": formatted_aliases
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des alias: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_command_aliases"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/add_command_alias', methods=['POST'])
def add_command_alias_route():
    """Ajoute un alias de commande"""
    try:
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.command_aliases import command_aliases
        except ImportError:
            # Sinon, utiliser l'import relatif
            from command_aliases import command_aliases
        
        data = request.json
        command = data.get('command')
        alias = data.get('alias')
        
        print(f"Tentative d'ajout d'alias: commande='{command}', alias='{alias}'")
        
        if not command or not alias:
            return jsonify({"success": False, "error": "Commande ou alias non spécifié"})
        
        # Nettoyer les entrées
        command = command.strip()
        alias = alias.strip()
        
        # Vérifier si l'alias existe déjà
        if alias in command_aliases.command_lookup:
            existing_command = command_aliases.command_lookup[alias]
            if existing_command != command:
                return jsonify({
                    "success": False, 
                    "error": f"L'alias '{alias}' existe déjà pour la commande '{existing_command}'"
                })
            else:
                # L'alias existe déjà pour cette commande, on considère que c'est un succès
                return jsonify({
                    "success": True,
                    "command": command,
                    "alias": alias,
                    "message": "Cet alias existe déjà pour cette commande"
                })
        
        # Ajouter l'alias
        success = command_aliases.add_alias(command, alias)
        
        if success:
            add_log(f"Alias '{alias}' ajouté pour la commande '{command}'", "info")
            # Sauvegarder les modifications dans la base de données
            command_aliases.save_to_database()
            return jsonify({
                "success": True,
                "command": command,
                "alias": alias
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Échec de l'ajout de l'alias '{alias}' pour la commande '{command}'"
            })
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un alias: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/add_command_alias"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/remove_command_alias', methods=['POST'])
def remove_command_alias_route():
    """Supprime un alias de commande"""
    try:
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.command_aliases import command_aliases
        except ImportError:
            # Sinon, utiliser l'import relatif
            from command_aliases import command_aliases
        
        data = request.json
        alias = data.get('alias')
        
        print(f"Tentative de suppression d'alias: '{alias}'")
        
        if not alias:
            return jsonify({"success": False, "error": "Alias non spécifié"})
        
        # Vérifier si l'alias existe
        if alias not in command_aliases.command_lookup:
            return jsonify({
                "success": False, 
                "error": f"L'alias '{alias}' n'existe pas"
            })
        
        # Récupérer la commande associée pour le message de log
        command = command_aliases.command_lookup[alias]
        
        # Supprimer l'alias
        success = command_aliases.remove_alias(alias)
        
        if success:
            add_log(f"Alias '{alias}' supprimé pour la commande '{command}'", "info")
            # Sauvegarder les modifications dans la base de données
            command_aliases.save_to_database()
            return jsonify({
                "success": True,
                "alias": alias
            })
        else:
            return jsonify({
                "success": False, 
                "error": f"Échec de la suppression de l'alias '{alias}'"
            })
    except Exception as e:
        print(f"Erreur lors de la suppression d'un alias: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/remove_command_alias"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/reload_command_aliases', methods=['POST'])
def reload_command_aliases_route():
    """Recharge les alias de commandes depuis la base de données"""
    try:
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.command_aliases import command_aliases
        except ImportError:
            # Sinon, utiliser l'import relatif
            from command_aliases import command_aliases
        
        # Recharger les alias depuis la base de données
        success = command_aliases.reload_from_database()
        
        if success:
            add_log("Alias de commandes rechargés avec succès", "info")
            return jsonify({
                "success": True,
                "message": "Alias rechargés avec succès",
                "count": len(command_aliases.aliases)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec du rechargement des alias"
            })
    except Exception as e:
        print(f"Erreur lors du rechargement des alias: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/reload_command_aliases"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/optimize_database', methods=['POST'])
def optimize_database_route():
    """Optimise la base de données SQLite"""
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import ensure_connection
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import ensure_connection
        
        @ensure_connection
        def optimize_db(conn):
            cursor = conn.cursor()
            # Exécuter VACUUM pour optimiser la base de données
            cursor.execute("VACUUM")
            # Exécuter ANALYZE pour mettre à jour les statistiques
            cursor.execute("ANALYZE")
            return True
        
        success = optimize_db()
        
        if success:
            add_log("Base de données optimisée avec succès", "info")
            return jsonify({
                "success": True,
                "message": "Base de données optimisée avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de l'optimisation de la base de données"
            })
    except Exception as e:
        print(f"Erreur lors de l'optimisation de la base de données: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.MEDIUM,
            context={"route": "/optimize_database"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.route('/backup_database', methods=['POST'])
def backup_database_route():
    """Crée une sauvegarde de la base de données"""
    try:
        import os
        import shutil
        import datetime
        
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import DB_PATH
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import DB_PATH
        
        # Créer un répertoire de sauvegarde s'il n'existe pas
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Générer un nom de fichier avec la date et l'heure
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"whisp_data_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copier le fichier de base de données
        shutil.copy2(DB_PATH, backup_path)
        
        add_log(f"Base de données sauvegardée dans {backup_path}", "info")
        return jsonify({
            "success": True,
            "message": "Base de données sauvegardée avec succès",
            "backup_path": backup_path
        })
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la base de données: {str(e)}")
        traceback.print_exc()
        error_handler.handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.MEDIUM,
            context={"route": "/backup_database"}
        )
        return jsonify({"success": False, "error": str(e)})

# Routes API pour la gestion des données de fine-tuning

@app.route('/api/finetune/samples', methods=['GET'])
def get_finetune_samples():
    """Récupère tous les échantillons pour le fine-tuning"""
    try:
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            return jsonify({"success": False, "error": "Dossier records non trouvé", "samples": []})
        
        # Récupérer la liste des échantillons
        samples = []
        
        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]
        
        for engine in engines:
            engine_dir = os.path.join(records_dir, engine)
            
            # Parcourir récursivement tous les fichiers JSON
            for root, dirs, files in os.walk(engine_dir):
                json_files = [f for f in files if f.endswith('.json')]
                
                for json_file in json_files:
                    json_path = os.path.join(root, json_file)
                    
                    try:
                        # Charger les métadonnées depuis le fichier JSON
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Obtenir le chemin du fichier audio
                        audio_file = metadata.get("audio_file")
                        if not audio_file:
                            continue
                            
                        audio_path = os.path.join(os.path.dirname(json_path), audio_file)
                        
                        # Obtenir le chemin du fichier texte (transcription)
                        base_name = os.path.splitext(audio_file)[0]
                        text_file = f"{base_name}.txt"
                        text_path = os.path.join(os.path.dirname(json_path), text_file)
                        
                        # Vérifier que les fichiers existent
                        if not os.path.exists(audio_path) or not os.path.exists(text_path):
                            continue
                        
                        # Lire le contenu du fichier texte
                        with open(text_path, 'r', encoding='utf-8') as f:
                            transcription = f.read().strip()
                        
                        # Déterminer le split (train, validation, test)
                        split_dir = os.path.basename(os.path.dirname(json_path))
                        split = split_dir if split_dir in ["train", "validation", "test"] else "unknown"
                        
                        # Déterminer les chemins relatifs pour le frontend
                        rel_audio_path = os.path.relpath(audio_path, os.getcwd())
                        rel_json_path = os.path.relpath(json_path, os.getcwd())
                        rel_text_path = os.path.relpath(text_path, os.getcwd())
                        
                        # Ajouter l'échantillon à la liste
                        sample = {
                            "id": f"{engine}_{os.path.basename(audio_path)}",
                            "engine": engine,
                            "split": split,
                            "transcription": transcription,
                            "audio_path": rel_audio_path.replace("\\", "/"),
                            "json_path": rel_json_path.replace("\\", "/"),
                            "text_path": rel_text_path.replace("\\", "/"),
                            "timestamp": metadata.get("timestamp", 0),
                            "duration": metadata.get("duration", 0),
                            "metadata": metadata
                        }
                        
                        samples.append(sample)
                    except Exception as e:
                        print(f"Erreur lors du traitement du fichier {json_path}: {e}")
                        continue
        
        # Tri des échantillons par timestamp (du plus récent au plus ancien)
        samples.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return jsonify({"success": True, "samples": samples})
    except Exception as e:
        print(f"Erreur lors de la récupération des échantillons: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "samples": []})

@app.route('/api/finetune/update_transcription', methods=['POST'])
def update_transcription():
    """Met à jour la transcription d'un échantillon"""
    try:
        data = request.json
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        new_transcription = data.get('transcription')
        
        if not text_path or not new_transcription or not json_path:
            return jsonify({"success": False, "error": "Paramètres manquants"})
        
        # Convertir le chemin relatif en chemin absolu
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)
        
        # Vérifier que les fichiers existent
        if not os.path.exists(abs_text_path) or not os.path.exists(abs_json_path):
            return jsonify({"success": False, "error": "Fichier non trouvé"})
        
        # Mettre à jour le fichier texte
        with open(abs_text_path, 'w', encoding='utf-8') as f:
            f.write(new_transcription)
        
        # Mettre à jour les métadonnées dans le fichier JSON
        with open(abs_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Mettre à jour le champ text dans les métadonnées
        metadata['text'] = new_transcription
        
        with open(abs_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            records_dir = os.path.join(os.getcwd(), "records")
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
            
            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Chemin relatif pour l'identification dans le fichier JSONL
                rel_path = os.path.relpath(abs_text_path, records_dir).replace(".txt", os.path.splitext(metadata['audio_file'])[1])
                
                # Mettre à jour la ligne correspondante
                updated = False
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'].endswith(rel_path.replace(".txt", "")):
                            # Mettre à jour la transcription
                            entry['sentence'] = new_transcription
                            entry['transcription'] = new_transcription
                            # Réécrire la ligne mise à jour
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            updated = True
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)
                
                if updated:
                    print(f"metadata.jsonl mis à jour pour {rel_path}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été mis à jour
        
        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue
        
        return jsonify({"success": True, "message": "Transcription mise à jour avec succès"})
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la transcription: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/finetune/delete_sample', methods=['POST'])
def delete_sample():
    """Supprime un échantillon de données"""
    try:
        data = request.json
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        audio_path = data.get('audio_path')
        
        if not text_path or not json_path or not audio_path:
            return jsonify({"success": False, "error": "Paramètres manquants"})
        
        # Convertir les chemins relatifs en chemins absolus
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)
        abs_audio_path = os.path.join(os.getcwd(), audio_path)
        
        # Vérifier que les fichiers existent
        files_to_delete = []
        for file_path in [abs_text_path, abs_json_path, abs_audio_path]:
            if os.path.exists(file_path):
                files_to_delete.append(file_path)
        
        if not files_to_delete:
            return jsonify({"success": False, "error": "Aucun fichier à supprimer"})
        
        # Supprimer les fichiers
        for file_path in files_to_delete:
            os.remove(file_path)
            print(f"Fichier supprimé: {file_path}")
        
        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            records_dir = os.path.join(os.getcwd(), "records")
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
            
            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Chemin relatif pour l'identification dans le fichier JSONL
                rel_path = os.path.relpath(abs_audio_path, records_dir)
                
                # Filtrer la ligne correspondante
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'] == rel_path:
                            # Ignorer cette ligne
                            print(f"Entrée supprimée de metadata.jsonl: {rel_path}")
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été supprimés
        
        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue
        
        return jsonify({
            "success": True, 
            "message": f"{len(files_to_delete)} fichiers supprimés avec succès",
            "deleted_files": files_to_delete
        })
    except Exception as e:
        print(f"Erreur lors de la suppression de l'échantillon: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/finetune/change_split', methods=['POST'])
def change_split():
    """Change le split (train/validation/test) d'un échantillon"""
    try:
        data = request.json
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        audio_path = data.get('audio_path')
        new_split = data.get('split')
        
        if not text_path or not json_path or not audio_path or not new_split:
            return jsonify({"success": False, "error": "Paramètres manquants"})
        
        if new_split not in ["train", "validation", "test"]:
            return jsonify({"success": False, "error": "Split invalide. Doit être 'train', 'validation' ou 'test'"})
        
        # Convertir les chemins relatifs en chemins absolus
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)
        abs_audio_path = os.path.join(os.getcwd(), audio_path)
        
        # Vérifier que les fichiers existent
        for file_path in [abs_text_path, abs_json_path, abs_audio_path]:
            if not os.path.exists(file_path):
                return jsonify({"success": False, "error": f"Fichier non trouvé: {file_path}"})
        
        # Déterminer le moteur à partir du chemin
        engine = None
        try:
            parts = abs_audio_path.split(os.sep)
            records_index = parts.index("records")
            if records_index < len(parts) - 1:
                engine = parts[records_index + 1]
        except (ValueError, IndexError):
            return jsonify({"success": False, "error": "Impossible de déterminer le moteur à partir du chemin"})
        
        if not engine:
            return jsonify({"success": False, "error": "Moteur non trouvé dans le chemin"})
        
        # Construire les nouveaux chemins dans le dossier du split souhaité
        records_dir = os.path.join(os.getcwd(), "records")
        engine_dir = os.path.join(records_dir, engine)
        split_dir = os.path.join(engine_dir, new_split)
        
        # Créer le dossier du split s'il n'existe pas
        os.makedirs(split_dir, exist_ok=True)
        
        # Déterminer les nouveaux chemins
        new_audio_path = os.path.join(split_dir, os.path.basename(abs_audio_path))
        new_text_path = os.path.join(split_dir, os.path.basename(abs_text_path))
        new_json_path = os.path.join(split_dir, os.path.basename(abs_json_path))
        
        # Vérifier si les fichiers existent déjà dans le dossier cible
        for file_path in [new_audio_path, new_text_path, new_json_path]:
            if os.path.exists(file_path):
                return jsonify({
                    "success": False, 
                    "error": f"Un fichier portant le même nom existe déjà dans le dossier {new_split}"
                })
        
        # Déplacer les fichiers
        import shutil
        shutil.move(abs_audio_path, new_audio_path)
        shutil.move(abs_text_path, new_text_path)
        shutil.move(abs_json_path, new_json_path)
        
        # Mettre à jour le champ split dans le fichier JSON
        with open(new_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Mettre à jour le champ split dans les métadonnées
        metadata['split'] = new_split
        
        with open(new_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
            
            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Chemin relatif pour l'identification dans le fichier JSONL
                old_rel_path = os.path.relpath(abs_audio_path, records_dir)
                new_rel_path = os.path.relpath(new_audio_path, records_dir)
                
                # Mettre à jour la ligne correspondante
                updated = False
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'] == old_rel_path:
                            # Mettre à jour le chemin et le split
                            entry['path'] = new_rel_path
                            entry['audio']['path'] = new_rel_path
                            entry['split'] = new_split
                            # Réécrire la ligne mise à jour
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            updated = True
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)
                
                if updated:
                    print(f"metadata.jsonl mis à jour pour {old_rel_path} -> {new_rel_path}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été déplacés
        
        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue
        
        # Retourner les nouveaux chemins relatifs
        rel_new_audio_path = os.path.relpath(new_audio_path, os.getcwd()).replace("\\", "/")
        rel_new_text_path = os.path.relpath(new_text_path, os.getcwd()).replace("\\", "/")
        rel_new_json_path = os.path.relpath(new_json_path, os.getcwd()).replace("\\", "/")
        
        return jsonify({
            "success": True, 
            "message": f"Échantillon déplacé vers le split {new_split}",
            "new_paths": {
                "audio_path": rel_new_audio_path,
                "text_path": rel_new_text_path,
                "json_path": rel_new_json_path
            }
        })
    except Exception as e:
        print(f"Erreur lors du changement de split: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/finetune/regenerate_dataset', methods=['POST'])
def regenerate_dataset():
    """Régénère le dataset Hugging Face à partir des échantillons existants"""
    try:
        from speech_recognition_module import generate_huggingface_dataset
        
        success = generate_huggingface_dataset()
        
        if success:
            return jsonify({
                "success": True, 
                "message": "Dataset régénéré avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la régénération du dataset"
            })
    except Exception as e:
        print(f"Erreur lors de la régénération du dataset: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/events')
def events():
    """Flux SSE (Server-Sent Events) pour les mises à jour en temps réel"""
    def generate():
        yield "data: {\"initial\": true}\n\n"
        
        # Envoyer les métriques STT initiales
        from speech_recognition_module import get_stt_metrics
        metrics_data = get_stt_metrics()
        yield f"data: {json.dumps({'type': 'metrics', 'data': metrics_data})}\n\n"
        
        # Compteur pour les mises à jour périodiques des métriques
        metrics_counter = 0
        
        while True:
            try:
                # Attendre un message avec timeout
                message = web_message_queue.get(timeout=1.0)
                yield f"data: {message}\n\n"
                web_message_queue.task_done()
                
                # Incrémenter le compteur
                metrics_counter += 1
                
                # Envoyer les métriques STT toutes les 5 itérations
                if metrics_counter >= 5:
                    metrics_counter = 0
                    metrics_data = get_stt_metrics()
                    yield f"data: {json.dumps({'type': 'metrics', 'data': metrics_data})}\n\n"
                
            except queue.Empty:
                # Envoyer un ping pour maintenir la connexion
                yield "data: {\"ping\": true}\n\n"
                
                # Envoyer les métriques STT périodiquement même sans activité
                metrics_counter += 1
                if metrics_counter >= 5:
                    metrics_counter = 0
                    metrics_data = get_stt_metrics()
                    yield f"data: {json.dumps({'type': 'metrics', 'data': metrics_data})}\n\n"
                
            except Exception as e:
                print(f"Erreur dans le flux SSE: {e}")
                break
    
    return Response(stream_with_context(generate()),
                   mimetype='text/event-stream')

# Fonction pour être appelée depuis d'autres modules
def log_to_web(message, type="info"):
    """Ajoute un message au journal des logs depuis d'autres modules"""
    add_log(message, type)

def command_to_web(command):
    """Enregistre une commande utilisateur depuis d'autres modules"""
    add_command(command)

def response_to_web(response):
    """Enregistre une réponse de l'assistant depuis d'autres modules"""
    add_response(response)
