"""
Module de gestion des fenêtres pour l'assistant Whisp.

Shim de compatibilité — l'implémentation réelle vit dans le package `window/`.
"""
from window.commands import executer_commande_fenetre
from window.monitors import get_monitor_count, deplacer_fenetre_vers_ecran
from window.focus import basculer_vers_fenetre, basculer_vers_application
from window.enumeration import obtenir_fenetres_ouvertes, obtenir_applications_ouvertes
from window.active_app import (
    get_active_application, is_browser_active, get_active_browser,
    get_active_browser_tab_info, detect_application_context,
)

__all__ = [
    'executer_commande_fenetre', 'get_monitor_count', 'deplacer_fenetre_vers_ecran',
    'basculer_vers_fenetre', 'basculer_vers_application', 'obtenir_fenetres_ouvertes',
    'obtenir_applications_ouvertes', 'get_active_application', 'is_browser_active',
    'get_active_browser', 'get_active_browser_tab_info', 'detect_application_context',
]
