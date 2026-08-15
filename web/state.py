"""Shared module-level state and helpers for the Whisp web interface.

These definitions were extracted verbatim from ``web_interface.py`` so that
Flask Blueprints (and the application module itself) can import the same
mutable singletons and helper functions.
"""

import queue
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor

# Error handler - lazy loaded to avoid circular imports
_error_handler = None
_ErrorCategory = None
_ErrorSeverity = None

def get_error_handler():
    """Lazy load error handler to avoid circular imports"""
    global _error_handler
    if _error_handler is None:
        from error_handler import get_error_handler as _get_handler
        _error_handler = _get_handler()
    return _error_handler

def get_error_types():
    """Lazy load error types to avoid circular imports"""
    global _ErrorCategory, _ErrorSeverity
    if _ErrorCategory is None:
        from error_handler import ErrorCategory, ErrorSeverity
        _ErrorCategory = ErrorCategory
        _ErrorSeverity = ErrorSeverity
    return _ErrorCategory, _ErrorSeverity

# Bug tracker - lazy loaded
_bug_tracker = None

def get_bug_tracker():
    """Lazy load bug tracker"""
    global _bug_tracker
    if _bug_tracker is None:
        from bug_tracker import bug_tracker as _tracker
        _bug_tracker = _tracker
    return _bug_tracker

# File d'attente pour les messages à afficher dans l'interface web
web_message_queue = queue.Queue()

# Registre des clients SSE : chaque client /events reçoit sa propre file.
# Une file unique partagée entre les clients faisait que chaque message
# n'était livré qu'à un seul d'entre eux (round-robin du Queue.get).
_sse_clients = []
_sse_clients_lock = threading.Lock()

def register_sse_client(maxsize=500):
    """Inscrit un nouveau client SSE et retourne sa file dédiée"""
    client_queue = queue.Queue(maxsize=maxsize)
    with _sse_clients_lock:
        _sse_clients.append(client_queue)
    return client_queue

def unregister_sse_client(client_queue):
    """Retire la file d'un client SSE déconnecté"""
    with _sse_clients_lock:
        if client_queue in _sse_clients:
            _sse_clients.remove(client_queue)

def publish_web_message(message):
    """Publie un message vers tous les clients SSE (fan-out).

    Le message est aussi placé dans web_message_queue pour les éventuels
    consommateurs historiques.
    """
    web_message_queue.put(message)
    with _sse_clients_lock:
        clients = list(_sse_clients)
    for client_queue in clients:
        try:
            client_queue.put_nowait(message)
        except queue.Full:
            # Client lent : abandonner son message le plus ancien
            try:
                client_queue.get_nowait()
                client_queue.task_done()
                client_queue.put_nowait(message)
            except (queue.Empty, queue.Full):
                pass

# Thread pool for concurrent I/O operations
executor = ThreadPoolExecutor(max_workers=4)

def run_async(func, *args, **kwargs):
    """
    Run a synchronous function asynchronously in a thread pool.

    This helper function allows blocking I/O operations to run concurrently,
    improving performance for database queries, file operations, etc.

    Args:
        func: The function to run asynchronously
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Future object that can be awaited or used with callbacks

    Example:
        >>> future = run_async(db_query, "SELECT * FROM users")
        >>> result = future.result(timeout=5)
    """
    return executor.submit(func, *args, **kwargs)

# Variable pour stocker l'état de l'assistant
assistant_state = {
    "running": True,
    "last_command": "",
    "last_response": "",
    "logs": [],
    "errors": []  # Nouvel attribut pour stocker les erreurs récentes
}

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
    publish_web_message(json.dumps({"type": "log", "data": log_entry}))

    # Si c'est une erreur ou un avertissement, enregistrer également dans le gestionnaire d'erreurs
    if type in ["error", "warning"]:
        from error_handler import ErrorCategory, ErrorSeverity
        severity = ErrorSeverity.MEDIUM if type == "error" else ErrorSeverity.LOW
        error_handler = get_error_handler()
        get_error_handler().handle_error(
            message,
            category=ErrorCategory.WEB_INTERFACE,
            severity=severity,
            notify_user=False,  # Déjà notifié via l'interface web
            context={"source": "web_interface", "function": "add_log"}
        )

    # Enregistrer le log dans la base de données
    try:
        # Importer le module de base de données
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
    publish_web_message(json.dumps({"type": "command", "data": command}))

def add_response(response):
    """Enregistre une réponse de l'assistant"""
    if response:
        assistant_state["last_response"] = response
        add_log(f"Réponse: {response}", "response")
        # Envoyer directement la réponse pour mise à jour en temps réel
        publish_web_message(json.dumps({"type": "response", "data": response}))
