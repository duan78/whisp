"""
Module d'interface web pour l'assistant vocal Whisp

Migrated to Flask 3:
- All request.json replaced with request.get_json()
- All route decorators updated to use shorthand decorators (@app.get, @app.post, @app.put, @app.delete)
- All JSON responses use jsonify() with proper status codes

Performance Optimizations:
- Lazy-loaded imports for better startup time
- Optimized import order
- Security modules loaded on-demand
- Async/await support for I/O-bound operations
- Concurrent execution with ThreadPoolExecutor
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, abort
import threading
import queue
import time
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
import functools

# Core imports (always needed)
from config import (
    get_running, set_running,
    get_stt_engine, set_stt_engine,
    get_openai_api_key, set_openai_api_key,
    get_mistral_api_key, set_mistral_api_key
)
from tts_module import obtenir_moteur_tts, definir_moteur_tts
from speech_recognition_module import get_stt_metrics, reset_stt_metrics

# Security modules - lazy loaded (only imported when needed)
security_available = False
_InputValidator = None
_ValidationError = None
_api_security = None

def _init_security():
    """Lazy initialization of security modules"""
    global security_available, _InputValidator, _ValidationError, _api_security
    if _InputValidator is None:
        try:
            from input_validation import ValidationError, InputValidator
            from api_security import get_secure_api_key, set_secure_api_key, migrate_api_keys
            _InputValidator = InputValidator
            _ValidationError = ValidationError
            _api_security = {
                'get': get_secure_api_key,
                'set': set_secure_api_key,
                'migrate': migrate_api_keys
            }
            security_available = True
        except ImportError:
            security_available = False
            print("Modules de sécurité non disponibles")

# Shared state and helpers (extracted to web.state to avoid duplication with Blueprints)
from web.state import (
    assistant_state,
    web_message_queue,
    executor,
    run_async,
    add_log,
    add_command,
    add_response,
    get_error_handler,
    get_error_types,
    get_bug_tracker,
)

# Créer l'application Flask
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Register Blueprints extracted into the web.blueprints package
from web.blueprints.bugs import bp as bugs_bp
from web.blueprints.shortcuts import bp as shortcuts_bp
from web.blueprints.aliases import bp as aliases_bp
from web.blueprints.finetune import bp as finetune_bp

app.register_blueprint(bugs_bp)
app.register_blueprint(shortcuts_bp)
app.register_blueprint(aliases_bp)
app.register_blueprint(finetune_bp)

def start_web_server(host=None, port=None):
    """Démarre le serveur web dans un thread séparé.

    Par défaut, le serveur se lie à 127.0.0.1 (localhost) uniquement, afin de
    ne pas exposer l'interface sur le réseau. Pour l'exposer (déconseillé), il
    faut définir explicitement WEB_HOST=0.0.0.0 dans l'environnement.
    """
    # Enregistrer l'interface web auprès du gestionnaire d'erreurs
    error_handler = get_error_handler()
    get_error_handler().register_web_interface(sys.modules[__name__])

    # Configuration depuis l'environnement (voir config.example.env).
    # Valeur par défaut sûre : 127.0.0.1 (accessible uniquement en local).
    if host is None:
        host = os.environ.get('WEB_HOST', '127.0.0.1')
    if port is None:
        port = int(os.environ.get('WEB_PORT', '5000'))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('1', 'true', 'yes')

    # Démarrer le serveur dans un thread séparé
    threading.Thread(target=lambda: app.run(host=host, port=port, debug=debug, use_reloader=False),
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
    from datetime import datetime

    # Récupérer les erreurs récentes depuis le gestionnaire d'erreurs
    error_handler = get_error_handler()
    recent_errors = get_error_handler().get_error_history(limit=20)

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
    bug_tracker = get_bug_tracker()
    bug_tickets = get_bug_tracker().get_all_tickets()

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
    """Sert les fichiers du dossier records.

    Sécurisé contre le path traversal : le chemin résolu doit rester dans le
    dossier ``records/`` (comparaison par realpath).
    """
    records_dir = os.path.realpath(os.path.join(os.getcwd(), "records"))
    file_path = os.path.realpath(os.path.join(records_dir, filename))

    # Empêcher la sortie du dossier records (path traversal type ../)
    if not file_path.startswith(records_dir + os.sep) and file_path != records_dir:
        add_log(f"Tentative d'accès hors de records/ : {filename}", "warning")
        abort(403)

    if not os.path.isfile(file_path):
        abort(404)

    with open(file_path, 'rb') as f:
        audio_data = f.read()

    return Response(audio_data, mimetype='audio/wav')

@app.route('/aliases')
def aliases():
    """Page de gestion des alias de commandes"""
    try:
        # Importer le module des alias de commandes
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
        except (ValueError, KeyError, AttributeError, OSError) as e:
            from error_handler import ErrorCategory, ErrorSeverity
            error_handler = get_error_handler()
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass

    return jsonify({
        "running": get_running(),
        "last_command": assistant_state["last_command"],
        "last_response": assistant_state["last_response"],
        "logs": assistant_state["logs"][-20:],  # Retourner seulement les 20 derniers logs
        "stt_engine": get_stt_engine(),
        "tts_engine": tts_engine,
        "coqui_model": coqui_model_info
    })

@app.post('/toggle')
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

@app.post('/change_stt_engine')
@app.post('/set_stt_engine')  # Route alternative pour compatibilité
def change_stt_engine_route():
    """Change le moteur de reconnaissance vocale"""
    try:
        data = request.get_json()
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

@app.post('/set_api_key')
def set_api_key():
    """Configure une clé API"""
    try:
        # Validation des données
        if not request.is_json:
            return jsonify({'error': 'Content-Type doit être application/json'}), 400

        data = request.get_json()
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

@app.get('/get_api_keys')
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

@app.get('/get_stt_metrics')
def get_stt_metrics_route():
    """Récupère les métriques de performance STT"""
    try:
        # Vérifier si on demande l'historique
        history = request.args.get('history', 'false').lower() == 'true'
        engine = request.args.get('engine', None)
        
        if history:
            try:
                # Importer le module de base de données
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

@app.get('/get_logs')
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_logs"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.get('/get_errors')
def get_errors():
    """
    Récupère l'historique des erreurs.

    Performance optimized: Uses concurrent execution for parallel error fetching
    """
    try:
        # Récupérer le nombre d'erreurs demandées (par défaut 20)
        count = request.args.get('count', 20, type=int)
        category = request.args.get('category', None)

        # Run error fetching concurrently with web errors retrieval
        future_errors = run_async(
            get_error_handler().get_error_history,
            limit=count,
            category=category
        )

        # Wait for concurrent operation to complete
        errors = future_errors.result(timeout=5)

        # Récupérer aussi les erreurs de l'interface web (already in memory, fast)
        web_errors = assistant_state["errors"]

        return jsonify({
            "success": True,
            "system_errors": errors,
            "web_errors": web_errors
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.post('/reset_stt_metrics')
def reset_metrics():
    """Réinitialise les métriques de performance STT"""
    try:
        reset_stt_metrics()
        add_log("Métriques STT réinitialisées", "info")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.post('/restart_recognition')
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

@app.get('/get_coqui_models')
def get_coqui_models_route():
    """
    Récupère la liste des modèles Coqui TTS disponibles.

    Performance optimized: Uses caching to avoid repeated model scanning
    """
    try:
        from tts_module import get_coqui_models, get_current_coqui_model
        from cache_manager import tts_cache

        # Check cache first
        cache_key = 'coqui_models_list'
        cached_models = tts_cache.get(cache_key)

        if cached_models is not None:
            current_model = get_current_coqui_model()
            return jsonify({
                "success": True,
                "models": cached_models,
                "current_model": current_model,
                "cached": True
            })

        # Cache miss - fetch models
        models = get_coqui_models()
        current_model = get_current_coqui_model()

        # Store in cache for 5 minutes (300 seconds)
        tts_cache.set(cache_key, models)

        return jsonify({
            "success": True,
            "models": models,
            "current_model": current_model,
            "cached": False
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.post('/change_coqui_model')
def change_coqui_model():
    """Change le modèle Coqui TTS à utiliser"""
    try:
        data = request.get_json()
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

@app.post('/change_tts_engine')
@app.post('/set_tts_engine')  # Route alternative pour compatibilité
def change_tts_engine():
    """Change le moteur de synthèse vocale"""
    try:
        data = request.get_json()
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
@app.get('/get_preferences')
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_preferences"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.post('/set_preference')
def set_preference_route():
    """Définit une préférence utilisateur"""
    try:
        from config import save_preference

        data = request.get_json()
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/set_preference"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.get('/get_stt_settings')
def get_stt_settings_route():
    """Récupère les paramètres de reconnaissance vocale"""
    try:
        # Importer le module de reconnaissance vocale
        from speech_recognition_module import get_stt_settings, DEFAULT_STT_SETTINGS
        
        # Récupérer les paramètres
        settings = get_stt_settings()
        
        return jsonify({
            "success": True,
            "settings": settings,
            "default_settings": DEFAULT_STT_SETTINGS
        })
    except Exception as e:
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_stt_settings"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.post('/update_stt_setting')
def update_stt_setting_route():
    """Met à jour un paramètre de reconnaissance vocale"""
    try:
        # Importer le module de reconnaissance vocale
        from speech_recognition_module import update_stt_setting

        data = request.get_json()
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/update_stt_setting"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.post('/reset_stt_settings')
def reset_stt_settings_route():
    """Réinitialise les paramètres de reconnaissance vocale aux valeurs par défaut"""
    try:
        # Importer les modules nécessaires
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/reset_stt_settings"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.get('/get_all_config')
def get_all_config():
    """
    Récupère toutes les configurations de l'application depuis la base de données.

    Performance optimized: Uses concurrent execution for I/O-bound operations
    """
    try:
        ErrorCategory, ErrorSeverity = get_error_types()
        # Importer les modules nécessaires
        from config import get_all_preferences, get_stt_engine, get_running
        from tts_module import obtenir_moteur_tts, get_coqui_models, get_current_coqui_model

        # Use concurrent execution for I/O-bound operations
        # These operations can run in parallel since they're independent
        future_preferences = run_async(get_all_preferences)
        future_metrics = run_async(get_stt_metrics)
        future_errors = run_async(get_error_handler().get_error_history, limit=10)

        # Récupérer les logs web
        try:
            from database_manager import get_web_logs
            future_logs = run_async(get_web_logs, limit=20)
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            logs = []
            future_logs = None

        # Get results from concurrent operations
        preferences = future_preferences.result(timeout=5)
        metrics = future_metrics.result(timeout=5)
        errors = future_errors.result(timeout=5)
        if future_logs:
            logs = future_logs.result(timeout=5)
        else:
            logs = []

        # Récupérer les informations sur les moteurs et paramètres STT
        stt_engine = get_stt_engine()
        tts_engine = obtenir_moteur_tts()

        # Récupérer les paramètres STT
        stt_settings = {}
        try:
            from speech_recognition_module import get_stt_settings
            stt_settings = get_stt_settings()
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass
        
        # Récupérer les informations sur les modèles Coqui
        coqui_models = []
        current_coqui_model = None
        try:
            coqui_models = get_coqui_models()
            current_coqui_model = get_current_coqui_model()
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
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
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass
        
        # Récupérer les tickets de bugs
        bug_tickets = []
        try:
            from bug_tracker import bug_tracker
            bug_tickets = get_bug_tracker().get_all_tickets()
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass
        
        # Récupérer les informations sur les raccourcis clavier
        shortcuts = {}
        try:
            from shortcuts_database import get_all_shortcuts
            shortcuts = get_all_shortcuts()
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass
        
        # Récupérer les informations sur les tâches
        tasks = []
        try:
            from project_management_commands import load_tasks
            tasks_data = load_tasks()
            if tasks_data and "tasks" in tasks_data:
                tasks = tasks_data["tasks"]
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
            pass
        
        # Récupérer les informations sur les rappels
        reminders = []
        try:
            from reminder_commands import load_reminders
            reminders_data = load_reminders()
            if reminders_data and "reminders" in reminders_data:
                reminders = reminders_data["reminders"]
        except (ValueError, KeyError, AttributeError, OSError) as e:
            get_error_handler().log_error(ErrorCategory.WEB_INTERFACE, f"Error: {e}", ErrorSeverity.MEDIUM)
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_all_config"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.post('/optimize_database')
def optimize_database_route():
    """Optimise la base de données SQLite"""
    try:
        # Importer le module de base de données
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.MEDIUM,
            context={"route": "/optimize_database"}
        )
        return jsonify({"success": False, "error": str(e)})

@app.post('/backup_database')
def backup_database_route():
    """Crée une sauvegarde de la base de données"""
    try:
        import os
        import shutil
        import datetime
        
        # Importer le module de base de données
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
        get_error_handler().handle_error(
            e, 
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.MEDIUM,
            context={"route": "/backup_database"}
        )
        return jsonify({"success": False, "error": str(e)})

# Routes for cache management
@app.get('/get_cache_stats')
def get_cache_stats_route():
    """Récupère les statistiques du cache"""
    try:
        from cache_manager import get_cache_stats

        stats = get_cache_stats()

        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.post('/clear_cache')
def clear_cache_route():
    """Efface tous les caches"""
    try:
        from cache_manager import clear_all_caches

        clear_all_caches()

        add_log("Tous les caches ont été effacés", "info")

        return jsonify({
            "success": True,
            "message": "Caches effacés avec succès"
        })
    except Exception as e:
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
