"""
Module de gestion centralisée des erreurs pour l'assistant Whisp

Ce fichier maintient la compatibilité avec l'ancien code tout en déléguant
au nouveau package core pour éviter les imports circulaires.
"""

# Import everything from core for backward compatibility
from core.error_handler import *

# Export all symbols for backward compatibility
__all__ = [
    'ErrorHandler',
    'ErrorCategory',
    'ErrorSeverity',
    'get_error_handler',
    'catch_errors',
    'error_handler',
]
