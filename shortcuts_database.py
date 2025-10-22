"""
Base de données des raccourcis clavier pour l'assistant Whisp
"""

import json
from os_detection import get_os_type, adapt_shortcut

try:
    # Essayer d'abord l'import en tant que package
    from whisp_assistant.database_manager import ensure_connection
except ImportError:
    # Sinon, utiliser l'import relatif
    from database_manager import ensure_connection

# Dictionnaire des raccourcis clavier courants par application et par OS
# Ce dictionnaire sert de valeurs par défaut et sera stocké en base de données
DEFAULT_RACCOURCIS = {
    "windows": {
        "global": {
            "copier": ("ctrl", "c"),
            "coller": ("ctrl", "v"),
            "couper": ("ctrl", "x"),
            "annuler": ("ctrl", "z"),
            "rétablir": ("ctrl", "y"),
            "sélectionner tout": ("ctrl", "a"),
            "enregistrer": ("ctrl", "s"),
            "imprimer": ("ctrl", "p"),
            "rechercher": ("ctrl", "f"),
            "remplacer": ("ctrl", "h"),
            "nouveau": ("ctrl", "n"),
            "ouvrir": ("ctrl", "o"),
            "fermer": ("ctrl", "w"),
            "quitter": ("alt", "f4"),
            "rafraîchir": ("f5"),
            "aide": ("f1"),
        },
    },
    
    "mac": {
        "global": {
            "copier": ("cmd", "c"),
            "coller": ("cmd", "v"),
            "couper": ("cmd", "x"),
            "annuler": ("cmd", "z"),
            "rétablir": ("cmd", "shift", "z"),  # Différent sur Mac
            "sélectionner tout": ("cmd", "a"),
            "enregistrer": ("cmd", "s"),
            "imprimer": ("cmd", "p"),
            "rechercher": ("cmd", "f"),
            "remplacer": ("cmd", "option", "f"),  # Différent sur Mac
            "nouveau": ("cmd", "n"),
            "ouvrir": ("cmd", "o"),
            "fermer": ("cmd", "w"),
            "quitter": ("cmd", "q"),  # Différent sur Mac
            "rafraîchir": ("cmd", "r"),  # Différent sur Mac
            "aide": ("cmd", "?"),  # Différent sur Mac
        },
    },
    
    "linux": {
        "global": {
            "copier": ("ctrl", "c"),
            "coller": ("ctrl", "v"),
            "couper": ("ctrl", "x"),
            "annuler": ("ctrl", "z"),
            "rétablir": ("ctrl", "shift", "z"),  # Souvent comme sur Mac
            "sélectionner tout": ("ctrl", "a"),
            "enregistrer": ("ctrl", "s"),
            "imprimer": ("ctrl", "p"),
            "rechercher": ("ctrl", "f"),
            "remplacer": ("ctrl", "h"),
            "nouveau": ("ctrl", "n"),
            "ouvrir": ("ctrl", "o"),
            "fermer": ("ctrl", "w"),
            "quitter": ("ctrl", "q"),  # Différent sur Linux
            "rafraîchir": ("f5"),
            "aide": ("f1"),
        },
    },
    
    "windows": {
        "word": {
            "gras": ("ctrl", "b"),
            "italique": ("ctrl", "i"),
            "souligné": ("ctrl", "u"),
            "aligné à gauche": ("ctrl", "l"),
            "centré": ("ctrl", "e"),
            "aligné à droite": ("ctrl", "r"),
            "justifié": ("ctrl", "j"),
            "style normal": ("ctrl", "espace"),
            "augmenter taille police": ("ctrl", "shift", ">"),
            "diminuer taille police": ("ctrl", "shift", "<"),
            "insérer tableau": ("alt", "n", "t"),
            "insérer image": ("alt", "n", "p"),
            "insérer commentaire": ("alt", "r", "c"),
            "vérifier orthographe": ("f7"),
            "mode révision": ("ctrl", "shift", "e"),
            "accepter modification": ("alt", "r", "a"),
            "rejeter modification": ("alt", "r", "j"),
        },
    },
    
    "mac": {
        "word": {
            "gras": ("cmd", "b"),
            "italique": ("cmd", "i"),
            "souligné": ("cmd", "u"),
            "aligné à gauche": ("cmd", "l"),
            "centré": ("cmd", "e"),
            "aligné à droite": ("cmd", "r"),
            "justifié": ("cmd", "j"),
            "style normal": ("cmd", "espace"),
            "augmenter taille police": ("cmd", "shift", ">"),
            "diminuer taille police": ("cmd", "shift", "<"),
            "insérer tableau": ("option", "cmd", "t"),
            "insérer image": ("option", "cmd", "p"),
            "insérer commentaire": ("option", "cmd", "c"),
            "vérifier orthographe": ("cmd", ";"),
            "mode révision": ("cmd", "shift", "e"),
            "accepter modification": ("option", "cmd", "a"),
            "rejeter modification": ("option", "cmd", "r"),
        },
    },
    
    "linux": {
        "word": {
            "gras": ("ctrl", "b"),
            "italique": ("ctrl", "i"),
            "souligné": ("ctrl", "u"),
            "aligné à gauche": ("ctrl", "l"),
            "centré": ("ctrl", "e"),
            "aligné à droite": ("ctrl", "r"),
            "justifié": ("ctrl", "j"),
            "style normal": ("ctrl", "espace"),
            "augmenter taille police": ("ctrl", "shift", ">"),
            "diminuer taille police": ("ctrl", "shift", "<"),
            "insérer tableau": ("alt", "n", "t"),
            "insérer image": ("alt", "n", "p"),
            "insérer commentaire": ("alt", "r", "c"),
            "vérifier orthographe": ("f7"),
            "mode révision": ("ctrl", "shift", "e"),
            "accepter modification": ("alt", "r", "a"),
            "rejeter modification": ("alt", "r", "j"),
        },
    },
    
    "windows": {
        "excel": {
            "insérer fonction": ("shift", "f3"),
            "somme automatique": ("alt", "="),
            "insérer ligne": ("ctrl", "+"),
            "supprimer ligne": ("ctrl", "-"),
            "sélectionner colonne": ("ctrl", "espace"),
            "sélectionner ligne": ("shift", "espace"),
            "formater cellule": ("ctrl", "1"),
            "filtrer": ("ctrl", "shift", "l"),
            "créer graphique": ("f11"),
            "aller à cellule": ("ctrl", "g"),
            "éditer cellule": ("f2"),
            "figer les volets": ("alt", "w", "f"),
            "afficher formules": ("ctrl", "`"),
        },
    },
    
    "mac": {
        "excel": {
            "insérer fonction": ("shift", "fn", "f3"),
            "somme automatique": ("cmd", "shift", "t"),
            "insérer ligne": ("cmd", "shift", "+"),
            "supprimer ligne": ("cmd", "-"),
            "sélectionner colonne": ("ctrl", "espace"),
            "sélectionner ligne": ("shift", "espace"),
            "formater cellule": ("cmd", "1"),
            "filtrer": ("cmd", "shift", "f"),
            "créer graphique": ("fn", "f11"),
            "aller à cellule": ("cmd", "g"),
            "éditer cellule": ("ctrl", "u"),
            "figer les volets": ("cmd", "option", "f"),
            "afficher formules": ("cmd", "`"),
        },
    },
    
    "linux": {
        "excel": {
            "insérer fonction": ("shift", "f3"),
            "somme automatique": ("alt", "="),
            "insérer ligne": ("ctrl", "+"),
            "supprimer ligne": ("ctrl", "-"),
            "sélectionner colonne": ("ctrl", "espace"),
            "sélectionner ligne": ("shift", "espace"),
            "formater cellule": ("ctrl", "1"),
            "filtrer": ("ctrl", "shift", "l"),
            "créer graphique": ("f11"),
            "aller à cellule": ("ctrl", "g"),
            "éditer cellule": ("f2"),
            "figer les volets": ("alt", "w", "f"),
            "afficher formules": ("ctrl", "`"),
        },
    },
    
    "windows": {
        "powerpoint": {
            "nouvelle diapositive": ("ctrl", "m"),
            "démarrer présentation": ("f5"),
            "présentation depuis diapo actuelle": ("shift", "f5"),
            "diapositive suivante": ("n"),
            "diapositive précédente": ("p"),
            "aller à diapositive": ("g"),
            "écran noir": ("b"),
            "écran blanc": ("w"),
            "terminer présentation": ("escape"),
            "mode plan": ("alt", "shift", "tab"),
            "dupliquer diapositive": ("ctrl", "d"),
            "grouper objets": ("ctrl", "g"),
            "dégrouper objets": ("ctrl", "shift", "g"),
        },
    },
    
    "mac": {
        "powerpoint": {
            "nouvelle diapositive": ("cmd", "shift", "n"),
            "démarrer présentation": ("cmd", "shift", "return"),
            "présentation depuis diapo actuelle": ("option", "cmd", "return"),
            "diapositive suivante": ("n"),
            "diapositive précédente": ("p"),
            "aller à diapositive": ("g"),
            "écran noir": ("b"),
            "écran blanc": ("w"),
            "terminer présentation": ("escape"),
            "mode plan": ("cmd", "option", "tab"),
            "dupliquer diapositive": ("cmd", "d"),
            "grouper objets": ("cmd", "g"),
            "dégrouper objets": ("cmd", "shift", "g"),
        },
    },
    
    "linux": {
        "powerpoint": {
            "nouvelle diapositive": ("ctrl", "m"),
            "démarrer présentation": ("f5"),
            "présentation depuis diapo actuelle": ("shift", "f5"),
            "diapositive suivante": ("n"),
            "diapositive précédente": ("p"),
            "aller à diapositive": ("g"),
            "écran noir": ("b"),
            "écran blanc": ("w"),
            "terminer présentation": ("escape"),
            "mode plan": ("alt", "shift", "tab"),
            "dupliquer diapositive": ("ctrl", "d"),
            "grouper objets": ("ctrl", "g"),
            "dégrouper objets": ("ctrl", "shift", "g"),
        },
    },
    
    "windows": {
        "navigateur": {
            "nouvel onglet": ("ctrl", "t"),
            "fermer onglet": ("ctrl", "w"),
            "onglet suivant": ("ctrl", "tab"),
            "onglet précédent": ("ctrl", "shift", "tab"),
            "historique": ("ctrl", "h"),
            "favoris": ("ctrl", "d"),
            "téléchargements": ("ctrl", "j"),
            "page d'accueil": ("alt", "home"),
            "recharger page": ("f5"),
            "recharger sans cache": ("ctrl", "f5"),
            "zoom avant": ("ctrl", "+"),
            "zoom arrière": ("ctrl", "-"),
            "zoom normal": ("ctrl", "0"),
            "plein écran": ("f11"),
        },
    },
    
    "mac": {
        "navigateur": {
            "nouvel onglet": ("cmd", "t"),
            "fermer onglet": ("cmd", "w"),
            "onglet suivant": ("cmd", "option", "right"),
            "onglet précédent": ("cmd", "option", "left"),
            "historique": ("cmd", "y"),
            "favoris": ("cmd", "d"),
            "téléchargements": ("cmd", "shift", "j"),
            "page d'accueil": ("cmd", "shift", "h"),
            "recharger page": ("cmd", "r"),
            "recharger sans cache": ("cmd", "shift", "r"),
            "zoom avant": ("cmd", "+"),
            "zoom arrière": ("cmd", "-"),
            "zoom normal": ("cmd", "0"),
            "plein écran": ("cmd", "ctrl", "f"),
        },
    },
    
    "linux": {
        "navigateur": {
            "nouvel onglet": ("ctrl", "t"),
            "fermer onglet": ("ctrl", "w"),
            "onglet suivant": ("ctrl", "tab"),
            "onglet précédent": ("ctrl", "shift", "tab"),
            "historique": ("ctrl", "h"),
            "favoris": ("ctrl", "d"),
            "téléchargements": ("ctrl", "j"),
            "page d'accueil": ("alt", "home"),
            "recharger page": ("f5"),
            "recharger sans cache": ("ctrl", "f5"),
            "zoom avant": ("ctrl", "+"),
            "zoom arrière": ("ctrl", "-"),
            "zoom normal": ("ctrl", "0"),
            "plein écran": ("f11"),
        },
    },
    
    "windows": {
        "teams": {
            "activer/désactiver micro": ("ctrl", "shift", "m"),
            "activer/désactiver caméra": ("ctrl", "shift", "o"),
            "partager écran": ("ctrl", "shift", "e"),
            "lever la main": ("ctrl", "shift", "k"),
            "afficher participants": ("ctrl", "shift", "p"),
            "afficher conversation": ("ctrl", "shift", "c"),
            "accepter appel": ("ctrl", "shift", "a"),
            "refuser appel": ("ctrl", "shift", "d"),
            "raccrocher": ("ctrl", "shift", "h"),
        },
    },
    
    "mac": {
        "teams": {
            "activer/désactiver micro": ("cmd", "shift", "m"),
            "activer/désactiver caméra": ("cmd", "shift", "o"),
            "partager écran": ("cmd", "shift", "e"),
            "lever la main": ("cmd", "shift", "k"),
            "afficher participants": ("cmd", "shift", "p"),
            "afficher conversation": ("cmd", "shift", "c"),
            "accepter appel": ("cmd", "shift", "a"),
            "refuser appel": ("cmd", "shift", "d"),
            "raccrocher": ("cmd", "shift", "h"),
        },
    },
    
    "linux": {
        "teams": {
            "activer/désactiver micro": ("ctrl", "shift", "m"),
            "activer/désactiver caméra": ("ctrl", "shift", "o"),
            "partager écran": ("ctrl", "shift", "e"),
            "lever la main": ("ctrl", "shift", "k"),
            "afficher participants": ("ctrl", "shift", "p"),
            "afficher conversation": ("ctrl", "shift", "c"),
            "accepter appel": ("ctrl", "shift", "a"),
            "refuser appel": ("ctrl", "shift", "d"),
            "raccrocher": ("ctrl", "shift", "h"),
        },
    },
    
    "windows": {
        "zoom": {
            "activer/désactiver micro": ("alt", "a"),
            "activer/désactiver caméra": ("alt", "v"),
            "partager écran": ("alt", "s"),
            "lever la main": ("alt", "y"),
            "afficher participants": ("alt", "u"),
            "afficher conversation": ("alt", "h"),
            "quitter réunion": ("alt", "q"),
        }
    },
    
    "mac": {
        "zoom": {
            "activer/désactiver micro": ("cmd", "shift", "a"),
            "activer/désactiver caméra": ("cmd", "shift", "v"),
            "partager écran": ("cmd", "shift", "s"),
            "lever la main": ("option", "y"),
            "afficher participants": ("cmd", "u"),
            "afficher conversation": ("cmd", "shift", "h"),
            "quitter réunion": ("cmd", "w"),
        }
    },
    
    "linux": {
        "zoom": {
            "activer/désactiver micro": ("alt", "a"),
            "activer/désactiver caméra": ("alt", "v"),
            "partager écran": ("alt", "s"),
            "lever la main": ("alt", "y"),
            "afficher participants": ("alt", "u"),
            "afficher conversation": ("alt", "h"),
            "quitter réunion": ("alt", "q"),
        }
    },
    
    "windows": {
        "google meet": {
            "activer/désactiver micro": ("ctrl", "d"),
            "activer/désactiver caméra": ("ctrl", "e"),
            "lever la main": ("ctrl", "alt", "h"),
            "afficher participants": ("ctrl", "alt", "p"),
            "afficher conversation": ("ctrl", "alt", "c"),
            "partager écran": ("ctrl", "alt", "s"),
            "quitter réunion": ("ctrl", "w"),
            "afficher options": ("ctrl", "alt", "o"),
            "activer sous-titres": ("ctrl", "alt", "t"),
            "plein écran": ("f11"),
            "épingler/détacher": ("ctrl", "alt", "f"),
            "masquer/afficher vidéo": ("ctrl", "alt", "v"),
        }
    },
    
    "mac": {
        "google meet": {
            "activer/désactiver micro": ("cmd", "d"),
            "activer/désactiver caméra": ("cmd", "e"),
            "lever la main": ("cmd", "option", "h"),
            "afficher participants": ("cmd", "option", "p"),
            "afficher conversation": ("cmd", "option", "c"),
            "partager écran": ("cmd", "option", "s"),
            "quitter réunion": ("cmd", "w"),
            "afficher options": ("cmd", "option", "o"),
            "activer sous-titres": ("cmd", "option", "t"),
            "plein écran": ("cmd", "ctrl", "f"),
            "épingler/détacher": ("cmd", "option", "f"),
            "masquer/afficher vidéo": ("cmd", "option", "v"),
        }
    },
    
    "linux": {
        "google meet": {
            "activer/désactiver micro": ("ctrl", "d"),
            "activer/désactiver caméra": ("ctrl", "e"),
            "lever la main": ("ctrl", "alt", "h"),
            "afficher participants": ("ctrl", "alt", "p"),
            "afficher conversation": ("ctrl", "alt", "c"),
            "partager écran": ("ctrl", "alt", "s"),
            "quitter réunion": ("ctrl", "w"),
            "afficher options": ("ctrl", "alt", "o"),
            "activer sous-titres": ("ctrl", "alt", "t"),
            "plein écran": ("f11"),
            "épingler/détacher": ("ctrl", "alt", "f"),
            "masquer/afficher vidéo": ("ctrl", "alt", "v"),
        }
    }
}

# Fonction pour initialiser la base de données des raccourcis
@ensure_connection
def initialize_shortcuts_database(conn):
    """Initialise la table des raccourcis clavier dans la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shortcuts (
        id INTEGER PRIMARY KEY,
        os_type TEXT NOT NULL,
        application TEXT NOT NULL,
        command TEXT NOT NULL,
        shortcut TEXT NOT NULL,
        UNIQUE(os_type, application, command)
    )
    ''')
    
    # Vérifier si la table est vide
    cursor.execute("SELECT COUNT(*) FROM shortcuts")
    count = cursor.fetchone()[0]
    
    # Si la table est vide, insérer les raccourcis par défaut
    if count == 0:
        print("Initialisation de la base de données des raccourcis...")
        
        # Parcourir tous les OS
        for os_type in DEFAULT_RACCOURCIS:
            # Parcourir toutes les applications pour cet OS
            for app in DEFAULT_RACCOURCIS[os_type]:
                # Parcourir toutes les commandes pour cette application
                for cmd, shortcut in DEFAULT_RACCOURCIS[os_type][app].items():
                    # Convertir le raccourci en JSON pour le stockage
                    shortcut_json = json.dumps(shortcut)
                    
                    # Insérer le raccourci dans la base de données
                    cursor.execute(
                        "INSERT OR REPLACE INTO shortcuts (os_type, application, command, shortcut) VALUES (?, ?, ?, ?)",
                        (os_type, app, cmd, shortcut_json)
                    )
        
        conn.commit()
        print("Base de données des raccourcis initialisée avec succès")
    
    return True

# Fonction pour obtenir tous les raccourcis de la base de données
@ensure_connection
def get_all_shortcuts(conn):
    """Récupère tous les raccourcis de la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    initialize_shortcuts_database(conn)
    
    # Récupérer tous les raccourcis
    cursor.execute("SELECT os_type, application, command, shortcut FROM shortcuts")
    rows = cursor.fetchall()
    
    # Convertir les résultats en dictionnaire
    shortcuts = {}
    for row in rows:
        os_type, app, cmd, shortcut_json = row
        
        # Créer les niveaux du dictionnaire s'ils n'existent pas
        if os_type not in shortcuts:
            shortcuts[os_type] = {}
        if app not in shortcuts[os_type]:
            shortcuts[os_type][app] = {}
        
        # Ajouter le raccourci au dictionnaire
        shortcuts[os_type][app][cmd] = json.loads(shortcut_json)
    
    return shortcuts

# Fonction pour ajouter ou mettre à jour un raccourci
@ensure_connection
def add_or_update_shortcut(conn, os_type, application, command, shortcut):
    """Ajoute ou met à jour un raccourci dans la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    initialize_shortcuts_database(conn)
    
    # Convertir le raccourci en JSON pour le stockage
    shortcut_json = json.dumps(shortcut)
    
    # Insérer ou mettre à jour le raccourci
    cursor.execute(
        "INSERT OR REPLACE INTO shortcuts (os_type, application, command, shortcut) VALUES (?, ?, ?, ?)",
        (os_type, application, command, shortcut_json)
    )
    
    conn.commit()
    return True

# Fonction pour supprimer un raccourci
@ensure_connection
def delete_shortcut(conn, os_type, application, command):
    """Supprime un raccourci de la base de données"""
    cursor = conn.cursor()
    
    # Supprimer le raccourci
    cursor.execute(
        "DELETE FROM shortcuts WHERE os_type = ? AND application = ? AND command = ?",
        (os_type, application, command)
    )
    
    conn.commit()
    return cursor.rowcount > 0

# Variable pour stocker les raccourcis en cache
_shortcuts_cache = None

def obtenir_raccourci(application, commande):
    """Obtient un raccourci clavier pour une application et une commande données"""
    global _shortcuts_cache
    
    # Charger les raccourcis depuis la base de données si le cache est vide
    if _shortcuts_cache is None:
        _shortcuts_cache = get_all_shortcuts()
        
        # Si la base de données est vide, utiliser les raccourcis par défaut
        if not _shortcuts_cache:
            _shortcuts_cache = DEFAULT_RACCOURCIS
    
    app = application.lower()
    cmd = commande.lower()
    os_type = get_os_type()
    
    # Gérer les alias d'applications
    app_aliases = {
        "chrome": "navigateur",
        "firefox": "navigateur",
        "safari": "navigateur",
        "edge": "navigateur",
        "brave": "navigateur",
        "opera": "navigateur",
        "meet": "google meet",
        "google": "google meet",
        "visio": "google meet",
        "visioconférence": "google meet",
        "conférence": "google meet",
        "réunion": "google meet",
        "appel": "google meet",
        "appel vidéo": "google meet",
        "vidéoconférence": "google meet",
    }
    
    # Remplacer l'application par son alias si nécessaire
    if app in app_aliases:
        app = app_aliases[app]
    
    # Si l'OS n'est pas reconnu, utiliser Windows par défaut
    if os_type not in _shortcuts_cache:
        os_type = "windows"
    
    # Vérifier d'abord dans les raccourcis spécifiques à l'application pour l'OS actuel
    if app in _shortcuts_cache[os_type] and cmd in _shortcuts_cache[os_type][app]:
        return adapt_shortcut(_shortcuts_cache[os_type][app][cmd])
    
    # Sinon, chercher dans les raccourcis globaux pour l'OS actuel
    if "global" in _shortcuts_cache[os_type] and cmd in _shortcuts_cache[os_type]["global"]:
        return adapt_shortcut(_shortcuts_cache[os_type]["global"][cmd])
    
    # Si toujours pas trouvé, essayer avec les raccourcis Windows (plus courants)
    if os_type != "windows" and "windows" in _shortcuts_cache:
        if app in _shortcuts_cache["windows"] and cmd in _shortcuts_cache["windows"][app]:
            return adapt_shortcut(_shortcuts_cache["windows"][app][cmd])
        
        if "global" in _shortcuts_cache["windows"] and cmd in _shortcuts_cache["windows"]["global"]:
            return adapt_shortcut(_shortcuts_cache["windows"]["global"][cmd])
    
    return None

# Fonction pour rafraîchir le cache des raccourcis
def refresh_shortcuts_cache():
    """Rafraîchit le cache des raccourcis depuis la base de données"""
    global _shortcuts_cache
    _shortcuts_cache = get_all_shortcuts()
    return _shortcuts_cache is not None

# Fonction pour exécuter un raccourci personnalisé
def executer_raccourci_personnalise(voice_command):
    """
    Exécute un raccourci personnalisé en fonction de la commande vocale
    
    Args:
        voice_command: Commande vocale à exécuter
        
    Returns:
        bool: True si un raccourci a été exécuté, False sinon
    """
    try:
        # Importer le module de base de données
        try:
            # Essayer d'abord l'import en tant que package
            from whisp_assistant.database_manager import get_custom_shortcut_by_command, update_custom_shortcut_usage, get_custom_shortcuts
        except ImportError:
            # Sinon, utiliser l'import relatif
            from database_manager import get_custom_shortcut_by_command, update_custom_shortcut_usage, get_custom_shortcuts
        
        # Nettoyer la commande vocale pour améliorer la correspondance
        voice_command = voice_command.lower().strip()
        if voice_command.endswith((".", "!", "?")):
            voice_command = voice_command[:-1].strip()
        
        print(f"Recherche de raccourci personnalisé pour: '{voice_command}'")
        
        # Rechercher le raccourci correspondant à la commande vocale
        shortcut = get_custom_shortcut_by_command(voice_command)
        if not shortcut:
            # Essayer une recherche plus souple (contient la commande)
            try:
                all_shortcuts = get_custom_shortcuts()
                for s in all_shortcuts:
                    # Vérifier si la commande vocale est contenue dans le texte
                    if s["voice_command"].lower() == voice_command:
                        shortcut = s
                        print(f"Raccourci trouvé par correspondance exacte: {s['name']}")
                        break
            except Exception as e:
                print(f"Erreur lors de la recherche étendue de raccourcis: {e}")
                
            # Si toujours pas trouvé, retourner False
            if not shortcut:
                return False
        
        # Mettre à jour les statistiques d'utilisation
        update_custom_shortcut_usage(shortcut['id'])
        
        # Exécuter l'action en fonction du type
        action_type = shortcut['action_type']
        action_data = shortcut['action_data']
        
        if action_type == 'keyboard':
            # Simuler un raccourci clavier
            import pyautogui
            keys = action_data.split('+')
            pyautogui.hotkey(*keys)
            return True
            
        elif action_type == 'text':
            # Saisir du texte
            import pyautogui
            pyautogui.write(action_data)
            return True
            
        elif action_type == 'url':
            # Ouvrir une URL
            import webbrowser
            webbrowser.open(action_data)
            return True
            
        elif action_type == 'app':
            # Lancer une application
            import subprocess
            import os
            
            # Vérifier si le chemin existe
            if not os.path.exists(action_data):
                print(f"Chemin d'application non trouvé: {action_data}")
                return False
            
            # Lancer l'application
            if os.name == 'nt':  # Windows
                subprocess.Popen([action_data], shell=True)
            else:  # Linux/Mac
                subprocess.Popen(['open' if os.name == 'darwin' else 'xdg-open', action_data])
            
            return True
            
        elif action_type == 'script':
            # Exécuter un script Python
            try:
                # Créer un environnement d'exécution sécurisé
                exec_globals = {
                    '__builtins__': __builtins__,
                    'pyautogui': __import__('pyautogui'),
                    'webbrowser': __import__('webbrowser'),
                    'os': __import__('os'),
                    'subprocess': __import__('subprocess'),
                    'time': __import__('time')
                }
                
                # Exécuter le script
                exec(action_data, exec_globals)
                return True
            except Exception as e:
                print(f"Erreur lors de l'exécution du script: {e}")
                return False
        
        # Type d'action non reconnu
        return False
    except Exception as e:
        print(f"Erreur lors de l'exécution du raccourci personnalisé: {e}")
        return False

# Initialiser la base de données des raccourcis au démarrage
initialize_shortcuts_database()
