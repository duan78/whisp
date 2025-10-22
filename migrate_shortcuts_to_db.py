"""
Script de migration pour transférer les raccourcis clavier vers la base de données SQLite
"""
import json
import sqlite3
import os

# Importer le chemin de la base de données
try:
    from whisp_assistant.database_manager import DB_PATH, ensure_connection
except ImportError:
    from database_manager import DB_PATH, ensure_connection

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
        "zoom": {
            "activer/désactiver micro": ("alt", "a"),
            "activer/désactiver caméra": ("alt", "v"),
            "partager écran": ("alt", "s"),
            "lever la main": ("alt", "y"),
            "afficher participants": ("alt", "u"),
            "afficher conversation": ("alt", "h"),
            "quitter réunion": ("alt", "q"),
        },
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
        "zoom": {
            "activer/désactiver micro": ("cmd", "shift", "a"),
            "activer/désactiver caméra": ("cmd", "shift", "v"),
            "partager écran": ("cmd", "shift", "s"),
            "lever la main": ("option", "y"),
            "afficher participants": ("cmd", "u"),
            "afficher conversation": ("cmd", "shift", "h"),
            "quitter réunion": ("cmd", "w"),
        },
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
        "zoom": {
            "activer/désactiver micro": ("alt", "a"),
            "activer/désactiver caméra": ("alt", "v"),
            "partager écran": ("alt", "s"),
            "lever la main": ("alt", "y"),
            "afficher participants": ("alt", "u"),
            "afficher conversation": ("alt", "h"),
            "quitter réunion": ("alt", "q"),
        },
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

@ensure_connection
def add_or_update_shortcut(conn, os_type, application, command, shortcut):
    """Ajoute ou met à jour un raccourci dans la base de données"""
    cursor = conn.cursor()
    
    # Convertir le raccourci en JSON pour le stockage
    shortcut_json = json.dumps(shortcut)
    
    # Insérer ou mettre à jour le raccourci
    cursor.execute(
        "INSERT OR REPLACE INTO shortcuts (os_type, application, command, shortcut) VALUES (?, ?, ?, ?)",
        (os_type, application, command, shortcut_json)
    )
    
    conn.commit()
    return True

def migrate_shortcuts():
    """Migre les raccourcis clavier vers la base de données"""
    print("Migration des raccourcis clavier vers la base de données SQLite...")
    
    try:
        # Initialiser la base de données des raccourcis
        initialize_shortcuts_database()
        
        # Compter le nombre de raccourcis migrés
        shortcut_count = 0
        
        # Parcourir tous les OS
        for os_type in DEFAULT_RACCOURCIS:
            # Parcourir toutes les applications pour cet OS
            for app in DEFAULT_RACCOURCIS[os_type]:
                # Parcourir toutes les commandes pour cette application
                for cmd, shortcut in DEFAULT_RACCOURCIS[os_type][app].items():
                    # Ajouter le raccourci à la base de données
                    if add_or_update_shortcut(os_type, app, cmd, shortcut):
                        shortcut_count += 1
        
        print(f"Migration terminée avec succès: {shortcut_count} raccourcis migrés")
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des raccourcis: {e}")
        return False

def main():
    """Fonction principale pour exécuter la migration"""
    print("Début de la migration des raccourcis clavier vers la base de données SQLite...")
    
    success = migrate_shortcuts()
    
    if success:
        print("Migration des raccourcis terminée avec succès!")
    else:
        print("Migration des raccourcis terminée avec des erreurs.")

if __name__ == "__main__":
    main()
