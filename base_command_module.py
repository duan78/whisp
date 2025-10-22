"""
Classe de base pour tous les modules de commandes
"""

import re
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Callable
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

class BaseCommandModule(ABC):
    """Classe de base abstraite pour les modules de commandes"""
    
    def __init__(self):
        self.command_patterns: List[Tuple[re.Pattern, Callable]] = []
        self.error_category = ErrorCategory.COMMAND_PROCESSING
        self.module_name = self.__class__.__name__
        self._initialize_patterns()
    
    @abstractmethod
    def _initialize_patterns(self):
        """Initialise les patterns de commandes. À implémenter dans les sous-classes."""
        pass
    
    def add_command_pattern(self, pattern: str, handler: Callable, flags=re.IGNORECASE):
        """Ajoute un pattern de commande avec son handler"""
        compiled_pattern = re.compile(pattern, flags)
        self.command_patterns.append((compiled_pattern, handler))
    
    @catch_errors(category=ErrorCategory.COMMAND_PROCESSING, severity=ErrorSeverity.MEDIUM)
    def process_command(self, commande: str) -> Optional[str]:
        """
        Traite une commande en vérifiant tous les patterns enregistrés
        
        Args:
            commande: La commande à traiter
            
        Returns:
            Le résultat du traitement ou None si aucun pattern ne correspond
        """
        # Nettoyer la commande
        commande = self._clean_command(commande)
        
        # Vérifier chaque pattern
        for pattern, handler in self.command_patterns:
            match = pattern.match(commande)
            if match:
                try:
                    # Appeler le handler avec le match
                    result = handler(match, commande)
                    if result:
                        return result
                except Exception as e:
                    error_handler.handle_error(
                        e,
                        category=self.error_category,
                        severity=ErrorSeverity.MEDIUM,
                        context={
                            "module": self.module_name,
                            "command": commande,
                            "pattern": pattern.pattern
                        }
                    )
                    return f"Erreur lors de l'exécution de la commande: {str(e)}"
        
        return None
    
    def _clean_command(self, commande: str) -> str:
        """Nettoie une commande (peut être surchargé dans les sous-classes)"""
        return commande.strip().lower()
    
    def can_handle(self, commande: str) -> bool:
        """Vérifie si ce module peut gérer la commande"""
        commande = self._clean_command(commande)
        return any(pattern.match(commande) for pattern, _ in self.command_patterns)
    
    def get_command_help(self) -> Dict[str, List[str]]:
        """Retourne l'aide pour les commandes de ce module"""
        help_dict = {}
        for pattern, handler in self.command_patterns:
            # Extraire le nom de la fonction pour la catégorie
            category = handler.__name__.replace('_', ' ').title()
            if category not in help_dict:
                help_dict[category] = []
            
            # Extraire une version lisible du pattern
            pattern_str = pattern.pattern
            # Simplifier les patterns regex courants
            pattern_str = pattern_str.replace(r'\s*', ' ')
            pattern_str = pattern_str.replace(r'\s+', ' ')
            pattern_str = pattern_str.replace(r'(?:', '')
            pattern_str = pattern_str.replace(r')?', '')
            pattern_str = pattern_str.replace('^', '')
            pattern_str = pattern_str.replace('$', '')
            
            help_dict[category].append(pattern_str)
        
        return help_dict

class CommandResult:
    """Classe pour encapsuler le résultat d'une commande"""
    
    def __init__(self, success: bool, message: str = "", data: Optional[Dict] = None):
        self.success = success
        self.message = message
        self.data = data or {}
    
    def __str__(self):
        return self.message
    
    def to_dict(self):
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data
        }

def extract_number(text: str, default: int = 1) -> int:
    """Extrait un nombre d'un texte"""
    # Chercher un nombre dans le texte
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    
    # Chercher des nombres en toutes lettres
    numbers_text = {
        'un': 1, 'une': 1, 'deux': 2, 'trois': 3, 'quatre': 4,
        'cinq': 5, 'six': 6, 'sept': 7, 'huit': 8, 'neuf': 9,
        'dix': 10, 'onze': 11, 'douze': 12, 'quinze': 15,
        'vingt': 20, 'trente': 30, 'quarante': 40, 'cinquante': 50,
        'cent': 100, 'mille': 1000
    }
    
    for word, value in numbers_text.items():
        if word in text.lower():
            return value
    
    return default

def extract_text_between(text: str, start_marker: str, end_marker: str = None) -> Optional[str]:
    """Extrait le texte entre deux marqueurs"""
    start_index = text.lower().find(start_marker.lower())
    if start_index == -1:
        return None
    
    start_index += len(start_marker)
    
    if end_marker:
        end_index = text.lower().find(end_marker.lower(), start_index)
        if end_index == -1:
            return text[start_index:].strip()
        return text[start_index:end_index].strip()
    
    return text[start_index:].strip()

def normalize_command(command: str) -> str:
    """Normalise une commande pour faciliter la comparaison"""
    # Convertir en minuscules
    command = command.lower()
    
    # Supprimer la ponctuation
    command = re.sub(r'[^\w\s]', ' ', command)
    
    # Normaliser les espaces
    command = ' '.join(command.split())
    
    return command