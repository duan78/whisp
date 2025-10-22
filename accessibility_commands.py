"""
Module de commandes d'accessibilité pour l'assistant Whisp
Conçu pour les personnes ayant des difficultés à utiliser le clavier ou la souris
"""

import re
import time
import pyautogui
import keyboard
import subprocess
from text_processing import ecrire_texte_avec_accents
from window_manager import basculer_vers_application

# Configuration de la grille vocale pour la navigation précise
GRID_SIZE = 9  # Grille 9x9 pour la navigation précise
screen_width, screen_height = pyautogui.size()
grid_width = screen_width // GRID_SIZE
grid_height = screen_height // GRID_SIZE

# État de la grille vocale
grid_active = False
current_grid_level = 0  # 0: pas de grille, 1: grille principale, 2: sous-grille
last_grid_position = (0, 0)  # Dernière position sélectionnée dans la grille

# Fonctions d'aide pour la navigation vocale
def activer_grille_vocale():
    """Active la grille de navigation vocale à l'écran"""
    global grid_active, current_grid_level
    grid_active = True
    current_grid_level = 1
    # Ici on pourrait ajouter un affichage visuel de la grille
    return "Grille de navigation vocale activée. Dites un numéro de 1 à 9 pour sélectionner une zone."

def desactiver_grille_vocale():
    """Désactive la grille de navigation vocale"""
    global grid_active, current_grid_level
    grid_active = False
    current_grid_level = 0
    return "Grille de navigation vocale désactivée."

def naviguer_grille(numero):
    """Navigue dans la grille vocale selon le numéro prononcé"""
    global current_grid_level, last_grid_position
    
    if not grid_active:
        return None
    
    try:
        numero = int(numero)
        if numero < 1 or numero > 9:
            return "Veuillez dire un numéro entre 1 et 9."
    except ValueError:
        return "Numéro de grille non valide."
    
    # Calcul de la position dans la grille
    row = (numero - 1) // 3  # 0, 1, ou 2
    col = (numero - 1) % 3   # 0, 1, ou 2
    
    if current_grid_level == 1:
        # Premier niveau: sélection d'une zone
        x_start = col * (screen_width // 3)
        y_start = row * (screen_height // 3)
        
        # Stocker la position actuelle
        last_grid_position = (row, col)
        
        # Passer au niveau 2 (sous-grille)
        current_grid_level = 2
        return f"Zone {numero} sélectionnée. Dites un autre numéro pour préciser."
    
    elif current_grid_level == 2:
        # Deuxième niveau: sélection précise dans la sous-grille
        prev_row, prev_col = last_grid_position
        
        # Calculer la position finale
        x_base = prev_col * (screen_width // 3)
        y_base = prev_row * (screen_height // 3)
        
        x_offset = col * ((screen_width // 3) // 3)
        y_offset = row * ((screen_height // 3) // 3)
        
        x_pos = x_base + x_offset + ((screen_width // 3) // 6)
        y_pos = y_base + y_offset + ((screen_height // 3) // 6)
        
        # Déplacer le curseur à cette position
        pyautogui.moveTo(x_pos, y_pos)
        
        # Revenir au niveau 1
        current_grid_level = 1
        return f"Curseur déplacé à la position précise."

def executer_clic(type_clic="gauche"):
    """Exécute un clic de souris à la position actuelle"""
    if type_clic.lower() in ["gauche", "left"]:
        pyautogui.click()
        return "Clic gauche effectué."
    elif type_clic.lower() in ["droit", "right"]:
        pyautogui.rightClick()
        return "Clic droit effectué."
    elif type_clic.lower() in ["double", "double-clic"]:
        pyautogui.doubleClick()
        return "Double-clic effectué."
    return "Type de clic non reconnu."

def defiler(direction, quantite=3):
    """Fait défiler la page dans la direction spécifiée"""
    if direction.lower() in ["haut", "up"]:
        pyautogui.scroll(quantite * 100)  # Valeur positive pour défiler vers le haut
        return "Défilement vers le haut."
    elif direction.lower() in ["bas", "down"]:
        pyautogui.scroll(-quantite * 100)  # Valeur négative pour défiler vers le bas
        return "Défilement vers le bas."
    return "Direction de défilement non reconnue."

def dicter_texte(texte):
    """Dicte du texte à l'emplacement actuel du curseur"""
    ecrire_texte_avec_accents(texte)
    return f"Texte dicté : {texte}"

def activer_mode_lecture_ecran():
    """Active le mode de lecture d'écran (utilise Narrator sous Windows)"""
    try:
        # Raccourci Windows pour activer/désactiver Narrator
        keyboard.press_and_release('windows+ctrl+enter')
        return "Mode de lecture d'écran activé."
    except Exception as e:
        return f"Erreur lors de l'activation du mode de lecture d'écran: {str(e)}"

def executer_commande_accessibilite(texte):
    """Traite les commandes d'accessibilité"""
    texte_lower = texte.lower().strip()
    
    # Commandes de grille vocale avec de nombreux synonymes
    if any(cmd in texte_lower for cmd in [
        "active grille", "active la grille", "active grill", "active la grill", 
        "activer grille", "activer la grille", "activer grill", "activer la grill",
        "grille vocale", "grill vocale", "grille vocal", "grill vocal",
        "active navigation grille", "active la navigation grille", 
        "active navigation par grille", "active la navigation par grille",
        "démarre grille", "démarre la grille", "démarrer grille", "démarrer la grille",
        "lance grille", "lance la grille", "lancer grille", "lancer la grille",
        "mode grille", "mode grill", "active mode grille", "active mode grill",
        "commence grille", "commence la grille", "commencer grille", "commencer la grille",
        "utilise grille", "utilise la grille", "utiliser grille", "utiliser la grille",
        "navigation grille", "navigation par grille", "navigation grill", "navigation par grill"
    ]):
        return activer_grille_vocale()
    
    if any(cmd in texte_lower for cmd in [
        "désactive grille", "désactive la grille", "désactive grill", "désactive la grill",
        "désactiver grille", "désactiver la grille", "désactiver grill", "désactiver la grill",
        "ferme grille", "ferme la grille", "ferme grill", "ferme la grill",
        "fermer grille", "fermer la grille", "fermer grill", "fermer la grill",
        "arrête grille", "arrête la grille", "arrête grill", "arrête la grill",
        "arrêter grille", "arrêter la grille", "arrêter grill", "arrêter la grill",
        "quitte grille", "quitte la grille", "quitte grill", "quitte la grill",
        "quitter grille", "quitter la grille", "quitter grill", "quitter la grill",
        "stop grille", "stop la grille", "stop grill", "stop la grill",
        "stopper grille", "stopper la grille", "stopper grill", "stopper la grill",
        "termine grille", "termine la grille", "termine grill", "termine la grill",
        "terminer grille", "terminer la grille", "terminer grill", "terminer la grill"
    ]):
        return desactiver_grille_vocale()
    
    # Navigation dans la grille avec de nombreux synonymes
    grid_match = re.match(r"^(grille |grill |zone |position |case |cellule |numéro |emplacement |)([1-9])$", texte_lower)
    if grid_match:
        numero = grid_match.group(2)
        resultat = naviguer_grille(numero)
        if resultat:
            return resultat
    
    # Commandes de clic avec de nombreux synonymes
    if any(cmd == texte_lower for cmd in [
        "clic", "click", "cliquer", "clique", "clicker", "tape", "taper", "appuie", "appuyer",
        "clic gauche", "click gauche", "cliquer gauche", "clique gauche", "clicker gauche",
        "clic à gauche", "click à gauche", "cliquer à gauche", "clique à gauche", "clicker à gauche",
        "bouton gauche", "appuie bouton gauche", "appuyer bouton gauche",
        "presse bouton gauche", "presser bouton gauche", "tape bouton gauche", "taper bouton gauche"
    ]):
        return executer_clic("gauche")
    
    if any(cmd == texte_lower for cmd in [
        "clic droit", "click droit", "cliquer droit", "clique droit", "clicker droit",
        "clic à droite", "click à droite", "cliquer à droite", "clique à droite", "clicker à droite",
        "bouton droit", "appuie bouton droit", "appuyer bouton droit",
        "presse bouton droit", "presser bouton droit", "tape bouton droit", "taper bouton droit",
        "menu contextuel", "ouvre menu contextuel", "ouvrir menu contextuel"
    ]):
        return executer_clic("droit")
    
    if any(cmd == texte_lower for cmd in [
        "double clic", "double click", "double-clic", "double-click", 
        "double clique", "double clicker", "double tape", "double taper",
        "clic double", "click double", "clique double", "clicker double",
        "cliquer deux fois", "clique deux fois", "tape deux fois", "taper deux fois",
        "appuie deux fois", "appuyer deux fois", "presse deux fois", "presser deux fois"
    ]):
        return executer_clic("double")
    
    # Commandes de défilement avec de nombreux synonymes
    defiler_haut_cmds = [
        "défiler haut", "défilé haut", "défiler en haut", "défilé en haut", 
        "défiler vers le haut", "défilé vers le haut", "scroll up", "scrolle up",
        "monte la page", "monter la page", "page vers le haut", "page up"
    ]
    
    if any(cmd in texte_lower for cmd in defiler_haut_cmds):
        match = re.search(r"(\d+)", texte_lower)
        quantite = int(match.group(1)) if match else 3
        return defiler("haut", quantite)
    
    defiler_bas_cmds = [
        "défiler bas", "défilé bas", "défiler en bas", "défilé en bas", 
        "défiler vers le bas", "défilé vers le bas", "scroll down", "scrolle down",
        "descend la page", "descendre la page", "page vers le bas", "page down"
    ]
    
    if any(cmd in texte_lower for cmd in defiler_bas_cmds):
        match = re.search(r"(\d+)", texte_lower)
        quantite = int(match.group(1)) if match else 3
        return defiler("bas", quantite)
    
    # Commandes de lecture d'écran avec de nombreux synonymes
    if any(cmd in texte_lower for cmd in [
        "activer lecture", "active lecture", "activer la lecture", "active la lecture",
        "lecture écran", "lecture d'écran", "narrateur", "active narrateur", "activer narrateur",
        "active le narrateur", "activer le narrateur", "lance narrateur", "lancer narrateur",
        "lance le narrateur", "lancer le narrateur", "démarre narrateur", "démarrer narrateur",
        "démarre le narrateur", "démarrer le narrateur", "lis l'écran", "lire l'écran",
        "lis écran", "lire écran", "lis le contenu", "lire le contenu", "lis contenu", "lire contenu"
    ]):
        return activer_mode_lecture_ecran()
    
    # Commandes de dictée spécifiques avec de nombreux synonymes
    for prefix in ["dicter ", "dicte ", "dicté ", "écrire ", "écris ", "écrit ", "tape ", "taper ", "saisir ", "saisis "]:
        if texte_lower.startswith(prefix):
            texte_a_dicter = texte[len(prefix):]  # Enlever le préfixe
            return dicter_texte(texte_a_dicter)
    
    # Commandes de navigation par application avec de nombreux synonymes
    app_match = None
    for pattern in [
        r"^ouvre (.+)$", r"^ouvrir (.+)$", r"^lance (.+)$", r"^lancer (.+)$", 
        r"^démarre (.+)$", r"^démarrer (.+)$", r"^va sur (.+)$", r"^aller sur (.+)$",
        r"^navigue vers (.+)$", r"^naviguer vers (.+)$", r"^affiche (.+)$", r"^afficher (.+)$"
    ]:
        match = re.match(pattern, texte_lower)
        if match:
            app_name = match.group(1).strip()
            app_match = True
            return basculer_vers_application(app_name)
    
    return None
