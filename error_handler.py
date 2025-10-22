"""
Module de gestion centralisée des erreurs pour l'assistant Whisp
"""

import sys
import traceback
import logging
import os
import time
from datetime import datetime
from functools import wraps

# Configuration du logger
log_dir = os.path.join(os.path.expanduser("~"), ".whisp", "logs")
os.makedirs(log_dir, exist_ok=True)

# Format du nom de fichier de log avec date
log_file = os.path.join(log_dir, f"whisp_errors_{datetime.now().strftime('%Y%m%d')}.log")

# Configuration du logger
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('whisp_assistant')

# Catégories d'erreurs
class ErrorCategory:
    SPEECH_RECOGNITION = "Reconnaissance vocale"
    TTS = "Synthèse vocale"
    COMMAND_PROCESSING = "Traitement des commandes"
    WEB_INTERFACE = "Interface web"
    SYSTEM = "Système"
    NETWORK = "Réseau"
    API = "API externe"
    UNKNOWN = "Erreur inconnue"

# Niveaux de gravité
class ErrorSeverity:
    CRITICAL = "Critique"  # Erreur qui empêche l'application de fonctionner
    HIGH = "Élevée"        # Erreur qui affecte une fonctionnalité majeure
    MEDIUM = "Moyenne"     # Erreur qui affecte une fonctionnalité mineure
    LOW = "Faible"         # Erreur qui n'affecte pas le fonctionnement

# Classe principale de gestion des erreurs
class ErrorHandler:
    """Gestionnaire centralisé des erreurs pour l'assistant Whisp"""
    
    def __init__(self):
        self.error_count = 0
        self.error_history = []
        self.max_history = 50
        self.web_interface = None
        
    def register_web_interface(self, web_interface):
        """Enregistre l'interface web pour les notifications"""
        self.web_interface = web_interface
    
    def handle_error(self, error, category=ErrorCategory.UNKNOWN, severity=ErrorSeverity.MEDIUM, 
                    context=None, notify_user=True, recovery_action=None):
        """
        Gère une erreur de manière centralisée
        
        Args:
            error: L'exception ou le message d'erreur
            category: Catégorie de l'erreur
            severity: Niveau de gravité
            context: Informations contextuelles sur l'erreur
            notify_user: Si True, notifie l'utilisateur
            recovery_action: Action de récupération à effectuer
            
        Returns:
            bool: True si l'erreur a été gérée avec succès
        """
        self.error_count += 1
        
        # Créer un identifiant unique pour l'erreur
        error_id = f"ERR-{int(time.time())}-{self.error_count}"
        
        # Obtenir la trace d'erreur
        if isinstance(error, Exception):
            error_message = str(error)
            error_traceback = traceback.format_exc()
        else:
            error_message = str(error)
            try:
                # Utiliser format_exc() au lieu de format_stack() pour plus de fiabilité
                # format_stack() peut échouer dans certains contextes de thread
                tb = traceback.format_exc()
                error_traceback = tb if tb and tb.strip() != "NoneType: None" else "".join(traceback.format_stack())
            except Exception:
                error_traceback = "Traceback non disponible"
        
        # Créer l'entrée d'erreur
        error_entry = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "severity": severity,
            "message": error_message,
            "traceback": error_traceback,
            "context": context or {}
        }
        
        # Ajouter à l'historique
        self.error_history.append(error_entry)
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
        
        # Journaliser l'erreur
        log_message = f"[{error_id}] [{category}] [{severity}] {error_message}"
        if context:
            log_message += f" - Contexte: {context}"
            
        logger.error(log_message)
        if error_traceback:
            logger.error(f"Traceback: {error_traceback}")
        
        # Notifier l'utilisateur via l'interface web
        if notify_user and self.web_interface:
            try:
                # Message utilisateur simplifié
                user_message = self._create_user_message(error_entry)
                self.web_interface.log_to_web(user_message, "error")
            except Exception as e:
                logger.error(f"Erreur lors de la notification à l'interface web: {e}")
        
        # Exécuter l'action de récupération si fournie
        if recovery_action and callable(recovery_action):
            try:
                recovery_action()
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de l'action de récupération: {e}")
                return False
        
        return True
    
    def _create_user_message(self, error_entry):
        """Crée un message d'erreur adapté à l'utilisateur"""
        category = error_entry["category"]
        severity = error_entry["severity"]
        message = error_entry["message"]
        
        # Simplifier le message d'erreur pour l'utilisateur
        if "No module named" in message:
            return f"Module manquant: {message.split('No module named')[1].strip()}. Veuillez installer les dépendances requises."
        
        if "Connection refused" in message or "ConnectionError" in message:
            return f"Erreur de connexion: Impossible de se connecter au service requis. Vérifiez votre connexion internet."
        
        if "API key" in message or "Authentication" in message:
            return f"Erreur d'authentification: Vérifiez votre clé API ou vos identifiants."
        
        # Messages spécifiques par catégorie
        if category == ErrorCategory.SPEECH_RECOGNITION:
            return f"Problème de reconnaissance vocale: {message}. Essayez de parler plus clairement ou de changer de moteur STT."
        
        if category == ErrorCategory.TTS:
            return f"Problème de synthèse vocale: {message}. Essayez de changer de moteur TTS."
        
        if category == ErrorCategory.API:
            return f"Erreur d'API externe: {message}. Vérifiez votre connexion et vos clés API."
        
        # Message par défaut
        return f"Erreur {severity.lower()}: {message}"
    
    def get_error_history(self, limit=10, category=None, min_severity=None):
        """Récupère l'historique des erreurs avec filtrage"""
        filtered_history = self.error_history
        
        if category:
            filtered_history = [e for e in filtered_history if e["category"] == category]
        
        if min_severity:
            severity_levels = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            min_index = severity_levels.index(min_severity)
            filtered_history = [e for e in filtered_history if severity_levels.index(e["severity"]) >= min_index]
        
        return filtered_history[-limit:]
    
    def clear_error_history(self):
        """Efface l'historique des erreurs"""
        self.error_history = []
        self.error_count = 0
        return True

# Décorateur pour capturer les exceptions dans les fonctions
def catch_errors(category=ErrorCategory.UNKNOWN, severity=ErrorSeverity.MEDIUM, notify_user=True):
    """
    Décorateur pour capturer et gérer les exceptions dans une fonction
    
    Args:
        category: Catégorie de l'erreur
        severity: Niveau de gravité
        notify_user: Si True, notifie l'utilisateur
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Contexte de l'erreur
                context = {
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
                
                # Gérer l'erreur
                error_handler.handle_error(
                    error=e,
                    category=category,
                    severity=severity,
                    context=context,
                    notify_user=notify_user
                )
                
                # Valeur de retour par défaut selon le type de retour attendu
                # Pour les fonctions qui retournent un booléen, retourner False
                if func.__annotations__.get('return') == bool:
                    return False
                # Pour les fonctions qui retournent une chaîne, retourner un message d'erreur
                elif func.__annotations__.get('return') == str:
                    return f"Erreur: {str(e)}"
                # Pour les fonctions qui retournent une liste ou un dictionnaire, retourner une structure vide
                elif func.__annotations__.get('return') in (list, dict):
                    return func.__annotations__.get('return')()
                # Par défaut, retourner None
                return None
        return wrapper
    return decorator

# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()

# Fonction pour obtenir l'instance du gestionnaire d'erreurs
def get_error_handler():
    """Retourne l'instance globale du gestionnaire d'erreurs"""
    return error_handler
