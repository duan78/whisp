"""
Module de traitement central des commandes pour l'assistant Whisp - Version refactorisée
"""

import time
import re
import sys
import traceback
from typing import Optional

# Import des utilitaires
from import_utils import safe_import, get_function
from command_router import CommandDispatcher, create_command_modules

# Imports essentiels
from config import get_dictation_mode, get_translation_mode
from text_processing import ecrire_texte_avec_accents, nettoyer_commande
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Importer les fonctions de l'interface web
try:
    from web_interface import command_to_web, response_to_web, log_to_web
    web_interface_available = True
except ImportError:
    web_interface_available = False
    print("Interface web non disponible")

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

class CommandProcessorV2:
    """Classe refactorisée pour le traitement des commandes vocales"""
    
    def __init__(self):
        """Initialisation du processeur de commandes"""
        self.dispatcher = CommandDispatcher()
        self._initialize_dispatcher()
        self._start_services()
    
    def _initialize_dispatcher(self):
        """Configure le dispatcher avec tous les modules et handlers"""
        
        # Ajouter les pré-processeurs
        self.dispatcher.add_pre_processor(self._log_command)
        self.dispatcher.add_pre_processor(self._check_exit_confirmation)
        self.dispatcher.add_pre_processor(self._check_tts_stop)
        
        # Ajouter les handlers prioritaires
        self._register_priority_handlers()
        
        # Créer et enregistrer tous les modules
        self._register_command_modules()
        
        # Définir le handler par défaut
        self.dispatcher.router.set_fallback_handler(self._handle_unknown_command)
        
        # Ajouter les post-processeurs
        self.dispatcher.add_post_processor(self._log_response)
    
    def _register_priority_handlers(self):
        """Enregistre les handlers qui doivent être vérifiés en priorité"""
        
        # Mode traduction
        self.dispatcher.router.register_priority_handler(
            r'.*',  # Toutes les commandes
            self._check_translation_mode
        )
        
        # Mode dictée
        self.dispatcher.router.register_priority_handler(
            r'.*',  # Toutes les commandes
            self._check_dictation_mode
        )
        
        # Commandes de sortie
        self.dispatcher.router.register_priority_handler(
            r'^(?:quitte?r?|arr[êe]te?r?|ferme?r?|stop|exit|bye|au revoir|salut|à plus|goodbye)',
            self._handle_exit_command
        )
        
        # Commandes d'aide
        self.dispatcher.router.register_priority_handler(
            r'^aide(?:\s+(.+))?$',
            self._handle_help_command
        )
    
    def _register_command_modules(self):
        """Enregistre tous les modules de commandes"""
        modules = create_command_modules()
        
        for module_name, module in modules.items():
            if module:
                self.dispatcher.router.register_module(module)
                print(f"Module {module_name} enregistré")
    
    def _start_services(self):
        """Démarre les services nécessaires"""
        # Démarrer le vérificateur de rappels
        reminder_module = safe_import('reminder_commands')
        if reminder_module:
            start_func = get_function('reminder_commands', 'start_reminder_checker')
            if start_func:
                start_func()
    
    @catch_errors(category=ErrorCategory.COMMAND_PROCESSING, severity=ErrorSeverity.HIGH)
    def process_command(self, texte: str) -> Optional[str]:
        """
        Traite une commande vocale et retourne le résultat
        
        Args:
            texte: La commande vocale à traiter
            
        Returns:
            Le résultat du traitement ou None
        """
        return self.dispatcher.process(texte)
    
    # === Pré-processeurs ===
    
    def _log_command(self, command: str) -> str:
        """Log la commande reçue"""
        if web_interface_available:
            command_to_web(command)
        return command
    
    def _check_exit_confirmation(self, command: str) -> str:
        """Vérifie si une confirmation de sortie est en cours"""
        exit_module = safe_import('exit_commands')
        if exit_module:
            confirmation_en_cours = getattr(exit_module, 'confirmation_en_cours', False)
            if confirmation_en_cours:
                traiter_reponse = get_function('exit_commands', 'traiter_reponse_confirmation')
                if traiter_reponse and traiter_reponse(command):
                    return None  # Stopper le traitement
        return command
    
    def _check_tts_stop(self, command: str) -> str:
        """Vérifie si c'est une commande d'arrêt du TTS"""
        tts_module = safe_import('tts_module')
        if tts_module:
            est_arret = get_function('tts_module', 'est_commande_arret_tts')
            interrompre = get_function('tts_module', 'interrompre_lecture')
            
            if est_arret and interrompre and est_arret(command):
                interrompre()
                return None  # Stopper le traitement
        return command
    
    # === Handlers prioritaires ===
    
    def _check_translation_mode(self, command: str) -> Optional[str]:
        """Vérifie et traite le mode traduction"""
        if not get_translation_mode():
            return None
        
        try:
            analysis_module = safe_import('analysis_commands')
            if analysis_module:
                executer_traduction = get_function('analysis_commands', 'executer_commande_traduction')
                if executer_traduction:
                    return executer_traduction(command)
        except Exception as e:
            error_handler.handle_error(
                e,
                category=ErrorCategory.COMMAND_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                context={"mode": "traduction", "texte": command}
            )
            return "Erreur lors de la traduction. Veuillez réessayer."
        
        return None
    
    def _check_dictation_mode(self, command: str) -> Optional[str]:
        """Vérifie et traite le mode dictée"""
        if not get_dictation_mode():
            return None
        
        dictation_module = safe_import('dictation_mode')
        if dictation_module:
            traiter_dictee = get_function('dictation_mode', 'traiter_dictee')
            if traiter_dictee:
                return traiter_dictee(command)
        
        return None
    
    def _handle_exit_command(self, command: str) -> Optional[str]:
        """Gère les commandes de sortie"""
        exit_module = safe_import('exit_commands')
        if exit_module:
            demander_confirmation = get_function('exit_commands', 'demander_confirmation_sortie')
            if demander_confirmation:
                print(f"Commande de sortie détectée: '{command}'")
                demander_confirmation()
                return "Confirmation de sortie demandée"
        return None
    
    def _handle_help_command(self, command: str) -> Optional[str]:
        """Gère les commandes d'aide"""
        match = re.match(r'^aide(?:\s+(.+))?$', command, re.IGNORECASE)
        if not match:
            return None
        
        help_topic = match.group(1)
        
        if not help_topic:
            return self._get_general_help()
        elif 'développeur' in help_topic or 'dev' in help_topic:
            return self._get_developer_help()
        elif 'productivité' in help_topic or 'prod' in help_topic:
            return self._get_productivity_help()
        else:
            return self._get_module_help(help_topic)
    
    def _get_general_help(self) -> str:
        """Retourne l'aide générale"""
        return \"\"\"
Commandes générales disponibles:
- Dictée : "écris [texte]" ou "dictée" puis "fin de dictée"
- Souris : "clic gauche", "double clic", "souris en haut à gauche"
- Clavier : "entrée", "espace", "copier", "coller"
- Navigation : "ouvre le navigateur", "va sur [site]", "nouvel onglet"
- Système : "quelle heure est-il", "ouvre le bloc-notes"
- Fenêtres : "change de fenêtre", "minimise", "maximise"
- Aide : "aide développeur" pour les commandes de développement

Dites "quitte l'assistant" pour arrêter.
\"\"\"
    
    def _get_developer_help(self) -> str:
        \"\"\"Retourne l'aide développeur\"\"\"
        return \"\"\"
Commandes développeur disponibles:
- Git : "git status", "git add tout", "git commit avec message [msg]"
- IDE : "ouvre vs code", "vs code palette de commandes"
- Packages : "installe package [nom]", "npm install [package]"
- Tests : "lance les tests", "exécute pytest"
- Docker : "docker status", "lance conteneur [nom]"
- Projets : "crée projet python [nom]", "ajoute tâche [description]"
\"\"\"
    
    def _get_productivity_help(self) -> str:
        \"\"\"Retourne l'aide productivité\"\"\"
        return \"\"\"
Commandes productivité disponibles:
- Office : "ouvre word", "ouvre excel", "nouveau document"
- Formatage : "mets en gras", "centre le texte", "souligne"
- Présentation : "lance la présentation", "diapositive suivante"
- Réunions : "active le micro", "partage mon écran"
- Notes : "note rapide [texte]", "affiche mes notes"
- Minuteur : "démarre un minuteur", "démarre un pomodoro de 25 minutes"
\"\"\"
    
    def _get_module_help(self, module_name: str) -> str:
        \"\"\"Retourne l'aide pour un module spécifique\"\"\"
        modules_disponibles = {
            "system": "Commandes système: 'éteins l'ordinateur', 'redémarre', 'verrouille'",
            "browser": "Navigation web: 'ouvre google', 'nouvel onglet', 'ferme l'onglet'",
            "development": "Développement: 'exécute le code', 'crée un projet', 'git status'",
            "accessibility": "Accessibilité: 'lire le texte', 'loupe', 'contraste élevé'"
        }

        help_text = modules_disponibles.get(module_name.lower())
        if help_text:
            return f"📚 **Module {module_name.title()}**\n{help_text}"
        else:
            modules = ", ".join(modules_disponibles.keys())
            return f"Module '{module_name}' inconnu. Modules disponibles: {modules}"
    
    # === Handler par défaut ===
    
    def _handle_unknown_command(self, command: str) -> str:
        \"\"\"Gère les commandes non reconnues\"\"\"
        # Vérifier si c'est un raccourci personnalisé
        shortcuts_module = safe_import('shortcuts_database')
        if shortcuts_module:
            executer_raccourci = get_function('shortcuts_database', 'executer_raccourci_personnalise')
            if executer_raccourci:
                resultat = executer_raccourci(command)
                if resultat:
                    return resultat
        
        # Si ce n'est pas un raccourci, écrire le texte
        ecrire_texte_avec_accents(command)
        return f\"Texte écrit: {command}\"
    
    # === Post-processeurs ===
    
    def _log_response(self, response: str) -> str:
        \"\"\"Log la réponse\"\"\"
        if web_interface_available and response:
            response_to_web(response)
        return response

# Instance globale du processeur
command_processor = None

def get_command_processor() -> CommandProcessorV2:
    \"\"\"Obtient l'instance globale du processeur de commandes\"\"\"
    global command_processor
    if command_processor is None:
        command_processor = CommandProcessorV2()
    return command_processor