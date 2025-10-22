"""
Module de détection du système d'exploitation pour l'assistant Whisp
"""

import platform
import sys

def get_os_type():
    """
    Détecte le système d'exploitation actuel.
    
    Returns:
        str: 'windows', 'mac', 'linux' ou 'unknown'
    """
    system = platform.system().lower()
    
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'mac'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'

def get_modifier_keys():
    """
    Retourne les touches modificatrices spécifiques à l'OS actuel.
    
    Returns:
        dict: Dictionnaire des touches modificatrices
    """
    os_type = get_os_type()
    
    if os_type == 'mac':
        return {
            'ctrl': 'command',
            'alt': 'option',
            'win': 'command',
            'cmd': 'command',
            'meta': 'command'
        }
    elif os_type == 'windows':
        return {
            'ctrl': 'ctrl',
            'alt': 'alt',
            'win': 'win',
            'cmd': 'win',
            'meta': 'win'
        }
    elif os_type == 'linux':
        return {
            'ctrl': 'ctrl',
            'alt': 'alt',
            'win': 'meta',
            'cmd': 'meta',
            'meta': 'meta'
        }
    else:
        # Par défaut, utiliser les touches Windows
        return {
            'ctrl': 'ctrl',
            'alt': 'alt',
            'win': 'win',
            'cmd': 'win',
            'meta': 'win'
        }

def adapt_shortcut(shortcut):
    """
    Adapte un raccourci clavier en fonction de l'OS.
    
    Args:
        shortcut: Tuple ou chaîne représentant un raccourci
        
    Returns:
        Tuple ou chaîne adaptée à l'OS actuel
    """
    if shortcut is None:
        return None
        
    os_type = get_os_type()
    modifiers = get_modifier_keys()
    
    # Si c'est une simple touche (chaîne), la retourner telle quelle
    if isinstance(shortcut, str):
        return shortcut
    
    # Si c'est un tuple, adapter chaque élément
    adapted_shortcut = []
    for key in shortcut:
        # Remplacer les touches modificatrices par leur équivalent spécifique à l'OS
        if key.lower() in modifiers:
            adapted_shortcut.append(modifiers[key.lower()])
        else:
            adapted_shortcut.append(key)
    
    return tuple(adapted_shortcut)

def is_windows():
    """Vérifie si le système est Windows"""
    return get_os_type() == 'windows'

def is_mac():
    """Vérifie si le système est macOS"""
    return get_os_type() == 'mac'

def is_linux():
    """Vérifie si le système est Linux"""
    return get_os_type() == 'linux'

def get_platform_command(windows_cmd, mac_cmd, linux_cmd):
    """
    Retourne la commande appropriée selon la plateforme
    
    Args:
        windows_cmd: Commande pour Windows
        mac_cmd: Commande pour macOS
        linux_cmd: Commande pour Linux
        
    Returns:
        La commande correspondant à la plateforme actuelle
    """
    os_type = get_os_type()
    
    if os_type == 'windows':
        return windows_cmd
    elif os_type == 'mac':
        return mac_cmd
    elif os_type == 'linux':
        return linux_cmd
    else:
        # Par défaut, utiliser la commande Windows
        return windows_cmd
