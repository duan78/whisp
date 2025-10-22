"""
Module de routage des commandes pour réduire la complexité du processeur principal
"""

from typing import Dict, List, Tuple, Callable, Optional
import re
from base_command_module import BaseCommandModule

class CommandRouter:
    """Routeur pour diriger les commandes vers les bons modules"""
    
    def __init__(self):
        self.modules: List[BaseCommandModule] = []
        self.priority_handlers: List[Tuple[re.Pattern, Callable]] = []
        self.fallback_handler: Optional[Callable] = None
    
    def register_module(self, module: BaseCommandModule):
        """Enregistre un module de commandes"""
        self.modules.append(module)
    
    def register_priority_handler(self, pattern: str, handler: Callable):
        """Enregistre un handler prioritaire qui sera vérifié avant les modules"""
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        self.priority_handlers.append((compiled_pattern, handler))
    
    def set_fallback_handler(self, handler: Callable):
        """Définit le handler par défaut si aucune commande ne correspond"""
        self.fallback_handler = handler
    
    def route_command(self, command: str) -> Optional[str]:
        """
        Route une commande vers le bon handler
        
        Returns:
            Le résultat du traitement ou None si aucun handler n'a pu traiter la commande
        """
        # Vérifier d'abord les handlers prioritaires
        for pattern, handler in self.priority_handlers:
            if pattern.match(command):
                result = handler(command)
                if result is not None:
                    return result
        
        # Ensuite vérifier les modules enregistrés
        for module in self.modules:
            if module.can_handle(command):
                result = module.process_command(command)
                if result is not None:
                    return result
        
        # Si aucun module ne peut traiter, utiliser le fallback
        if self.fallback_handler:
            return self.fallback_handler(command)
        
        return None
    
    def get_all_commands_help(self) -> Dict[str, Dict[str, List[str]]]:
        """Récupère l'aide de tous les modules"""
        all_help = {}
        
        for module in self.modules:
            module_name = module.__class__.__name__.replace('Commands', '')
            all_help[module_name] = module.get_command_help()
        
        return all_help

class CommandDispatcher:
    """Dispatcher pour organiser le traitement des commandes"""
    
    def __init__(self):
        self.pre_processors: List[Callable] = []
        self.post_processors: List[Callable] = []
        self.router = CommandRouter()
    
    def add_pre_processor(self, processor: Callable):
        """Ajoute un pré-processeur qui sera appelé avant le routage"""
        self.pre_processors.append(processor)
    
    def add_post_processor(self, processor: Callable):
        """Ajoute un post-processeur qui sera appelé après le traitement"""
        self.post_processors.append(processor)
    
    def process(self, command: str) -> Optional[str]:
        """
        Traite une commande en appliquant les pré/post processeurs et le routage
        """
        # Appliquer les pré-processeurs
        for processor in self.pre_processors:
            command = processor(command)
            if command is None:
                return None
        
        # Router la commande
        result = self.router.route_command(command)
        
        # Appliquer les post-processeurs
        if result is not None:
            for processor in self.post_processors:
                result = processor(result)
        
        return result

def create_command_modules() -> Dict[str, BaseCommandModule]:
    """
    Factory pour créer et initialiser tous les modules de commandes
    """
    modules = {}
    
    # Importer et créer les modules de manière paresseuse
    module_configs = [
        ('keyboard', 'keyboard_commands', 'KeyboardCommands'),
        ('mouse', 'mouse_commands', 'MouseCommands'),
        ('system', 'system_commands', 'SystemCommands'),
        ('browser', 'browser_commands', 'BrowserCommands'),
        ('productivity', 'productivity_commands', 'ProductivityCommands'),
        ('window', 'window_manager', 'WindowCommands'),
        ('git', 'git_commands', 'GitCommands'),
        ('dev', 'dev_environment_commands', 'DevCommands'),
        ('project', 'project_management_commands', 'ProjectCommands'),
        ('web_dev', 'web_dev_commands', 'WebDevCommands'),
        ('database', 'database_commands', 'DatabaseCommands'),
        ('reminder', 'reminder_commands', 'ReminderCommands'),
        ('search', 'search_commands', 'SearchCommands'),
        ('file', 'file_commands', 'FileCommands'),
        ('accessibility', 'accessibility_commands', 'AccessibilityCommands'),
        ('analysis', 'analysis_commands', 'AnalysisCommands'),
        ('screen_reader', 'screen_reader_commands', 'ScreenReaderCommands'),
    ]
    
    for module_name, module_file, class_name in module_configs:
        try:
            # Import dynamique du module
            module = __import__(module_file, fromlist=[class_name])
            
            # Si le module utilise déjà BaseCommandModule, créer une instance
            if hasattr(module, class_name):
                command_class = getattr(module, class_name)
                modules[module_name] = command_class()
            else:
                # Sinon, créer un wrapper pour l'ancien module
                modules[module_name] = create_legacy_wrapper(module_name, module)
                
        except ImportError as e:
            print(f"Impossible d'importer le module {module_file}: {e}")
        except Exception as e:
            print(f"Erreur lors de la création du module {module_name}: {e}")
    
    return modules

def create_legacy_wrapper(module_name: str, module) -> BaseCommandModule:
    """
    Crée un wrapper pour les modules qui n'utilisent pas encore BaseCommandModule
    """
    from base_command_module import BaseCommandModule
    
    class LegacyWrapper(BaseCommandModule):
        def __init__(self):
            super().__init__()
            self.module = module
            self.module_name = module_name
        
        def _initialize_patterns(self):
            # Pour les modules legacy, on n'initialise pas de patterns
            # car ils ont leur propre logique de traitement
            pass
        
        def process_command(self, command: str) -> Optional[str]:
            # Chercher la fonction de traitement appropriée dans le module
            process_func_names = [
                f'executer_commande_{module_name}',
                f'traiter_commande_{module_name}',
                f'process_{module_name}_command',
                'process_command',
                'execute_command'
            ]
            
            for func_name in process_func_names:
                if hasattr(self.module, func_name):
                    func = getattr(self.module, func_name)
                    try:
                        return func(command)
                    except Exception:
                        return None
            
            return None
        
        def can_handle(self, command: str) -> bool:
            # Pour les modules legacy, on essaie de traiter et on voit si ça marche
            # C'est moins efficace mais permet la compatibilité
            result = self.process_command(command)
            return result is not None
    
    return LegacyWrapper()