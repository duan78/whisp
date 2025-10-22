"""
Module de gestion des fenêtres pour l'assistant Whisp
"""

import pyautogui
import subprocess
import time
import re
import os
import platform
from os_detection import get_os_type, is_windows, is_mac, is_linux

# Désactiver le fail-safe de PyAutoGUI qui cause des erreurs
# lors du déplacement de la souris vers les coins de l'écran
pyautogui.FAILSAFE = False

# Pour le débogage
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Importations conditionnelles selon l'OS
if is_windows():
    import keyboard
    import ctypes
    from ctypes import wintypes
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
    except ImportError:
        print("Modules win32 non disponibles. Certaines fonctionnalités seront limitées.")
elif is_mac():
    try:
        import Quartz
        import AppKit
    except ImportError:
        print("Modules Quartz et AppKit non disponibles. Certaines fonctionnalités seront limitées.")
elif is_linux():
    try:
        import Xlib.display
        import Xlib.X
    except ImportError:
        print("Module python-xlib non disponible. Certaines fonctionnalités seront limitées.")

# Importer le dictionnaire des sites populaires depuis browser_commands
try:
    from browser_commands import SITES_POPULAIRES
except ImportError:
    # Définir un dictionnaire vide si l'import échoue
    SITES_POPULAIRES = {}

def executer_commande_fenetre(texte):
    """Exécute des commandes de gestion de fenêtres en fonction du texte transcrit"""
    texte = texte.lower()
    os_type = get_os_type()
    
    # ===== VÉRIFICATION PRÉALABLE POUR LES SITES WEB =====
    # Vérification spéciale pour Amazon
    if "va sur amazon" in texte.lower() or "aller sur amazon" in texte.lower():
        print("Commande 'va sur amazon' détectée dans window_manager")
        return "SITE_WEB_CONNU"
    
    # Si la commande est "va sur X" ou "aller sur X", vérifier si X est un site web connu
    if any(pattern in texte for pattern in ["va sur ", "aller sur "]):
        # Extraire le nom du site
        site_name = None
        for pattern in ["va sur (.+)", "aller sur (.+)"]:
            match = re.search(pattern, texte)
            if match:
                site_name = match.group(1).strip().lower()
                break
        
        if site_name:
            print(f"Vérification si '{site_name}' est un site web connu...")
            
            # Vérification directe pour Amazon (cas prioritaire)
            if "amazon" in site_name:
                print(f"Amazon détecté dans window_manager: {site_name}")
                return "SITE_WEB_CONNU"
            
            # Vérifier si le site est dans notre dictionnaire de sites populaires
            for key in SITES_POPULAIRES.keys():
                # Vérification exacte ou si le nom du site est contenu dans la clé ou vice versa
                # Utiliser des comparaisons plus strictes pour éviter les faux positifs
                if key == site_name or (len(key) > 3 and key in site_name) or (len(site_name) > 3 and site_name in key):
                    print(f"Site web trouvé dans SITES_POPULAIRES: {key} pour la commande '{texte}'")
                    # Si c'est un site web connu, laisser browser_commands gérer cette commande
                    return "SITE_WEB_CONNU"
            
            # Vérification supplémentaire pour les sites courants
            common_sites = ["google", "facebook", "youtube", "twitter", "instagram", "linkedin"]
            if any(site in site_name for site in common_sites):
                print(f"Site web courant détecté: {site_name}")
                return "SITE_WEB_CONNU"
                
            print(f"Site web non trouvé dans SITES_POPULAIRES pour: {site_name}")
    
    # ===== NAVIGATION ENTRE APPLICATIONS =====
    # Patterns pour "va sur X", "ouvre X", "bascule vers X", etc.
    patterns_navigation = [
        r"va sur (\w+)",
        r"va à (\w+)",
        r"aller sur (\w+)",
        r"aller à (\w+)",
        r"ouvre (\w+)",
        r"ouvrir (\w+)",
        r"bascule vers (\w+)",
        r"basculer vers (\w+)",
        r"passe à (\w+)",
        r"passer à (\w+)",
        r"affiche (\w+)",
        r"afficher (\w+)",
        r"montre (\w+)",
        r"montrer (\w+)",
        r"active (\w+)",
        r"activer (\w+)"
    ]
    
    for pattern in patterns_navigation:
        match = re.search(pattern, texte)
        if match:
            app_name = match.group(1).strip()
            
            # Traitement spécial pour certaines applications
            app_name_lower = app_name.lower()
            
            # Mappings d'applications courantes (noms communs vers noms de processus)
            app_mappings = {
                "whatsapp": ["whatsapp", "whatsappdesktop", "whatsapp.exe", "whatsapp desktop"],
                "chrome": ["chrome", "googlechrome", "google chrome"],
                "firefox": ["firefox", "mozilla firefox"],
                "edge": ["edge", "msedge", "microsoft edge"],
                "word": ["winword", "microsoft word", "word"],
                "excel": ["excel", "microsoft excel"],
                "powerpoint": ["powerpnt", "powerpoint", "microsoft powerpoint"],
                "outlook": ["outlook", "microsoft outlook"],
                "teams": ["teams", "microsoft teams"],
                "skype": ["skype", "skype for business"],
                "discord": ["discord", "discord.exe"],
                "slack": ["slack", "slack.exe"],
                "zoom": ["zoom", "zoom.exe", "zoom meeting"],
                "vscode": ["code", "visual studio code", "vscode"],
                "explorer": ["explorer", "file explorer", "windows explorer"],
                "notepad": ["notepad", "notepad.exe"],
                "cmd": ["cmd", "command prompt", "cmd.exe"],
                "powershell": ["powershell", "powershell.exe"],
                "terminal": ["terminal", "windows terminal"]
            }
            
            # Vérifier si l'application est dans nos mappings
            target_app_names = []
            for key, values in app_mappings.items():
                if app_name_lower in key or any(app_name_lower in val.lower() for val in values):
                    target_app_names.extend(values)
                    target_app_names.append(key)
            
            # Si aucun mapping trouvé, utiliser le nom original
            if not target_app_names:
                target_app_names = [app_name]
            
            # Vérifier si l'application est ouverte
            apps_ouvertes = obtenir_applications_ouvertes()
            
            # Recherche approximative pour trouver l'application la plus proche
            app_trouvee = None
            
            # D'abord, essayer les noms exacts de notre mapping
            for target in target_app_names:
                for app in apps_ouvertes:
                    if target.lower() == app.lower():
                        app_trouvee = app
                        break
                if app_trouvee:
                    break
            
            # Si pas trouvé, essayer une correspondance partielle
            if not app_trouvee:
                for target in target_app_names:
                    for app in apps_ouvertes:
                        if target.lower() in app.lower() or app.lower() in target.lower():
                            app_trouvee = app
                            break
                    if app_trouvee:
                        break
            
            # Si toujours pas trouvé, essayer avec le nom original
            if not app_trouvee and app_name not in target_app_names:
                for app in apps_ouvertes:
                    if app_name.lower() in app.lower() or app.lower() in app_name.lower():
                        app_trouvee = app
                        break
            
            if app_trouvee:
                # Essayer d'abord par le titre de la fenêtre
                resultat = basculer_vers_fenetre(app_trouvee, par_titre=True, par_process=False)
                if not resultat:
                    # Si ça ne marche pas, essayer par le nom du processus
                    resultat = basculer_vers_fenetre(app_trouvee, par_titre=False, par_process=True)
                
                if resultat:
                    return f"Navigation vers {app_trouvee} réussie"
                else:
                    return f"Impossible de basculer vers {app_trouvee}"
            else:
                # Essayer directement avec les noms de notre mapping
                for target in target_app_names:
                    # Essayer d'abord par le titre
                    resultat = basculer_vers_fenetre(target, par_titre=True, par_process=False)
                    if not resultat:
                        # Si ça ne marche pas, essayer par le nom du processus
                        resultat = basculer_vers_fenetre(target, par_titre=False, par_process=True)
                    
                    if resultat:
                        return f"Navigation vers {target} réussie"
                
                # Si toujours pas réussi, essayer avec le nom original
                resultat = basculer_vers_fenetre(app_name)
                if resultat:
                    return f"Navigation vers {app_name} réussie"
                else:
                    return f"Application ou fenêtre {app_name} non trouvée"
    
    # Commande pour lister les applications ouvertes
    if any(cmd in texte for cmd in ["liste les applications", "lister les applications", 
                                   "quelles applications sont ouvertes", "applications ouvertes",
                                   "montre les applications ouvertes", "affiche les applications ouvertes"]):
        apps = obtenir_applications_ouvertes()
        if apps:
            return f"Applications ouvertes : {', '.join(apps[:15])}{'...' if len(apps) > 15 else ''}"
        else:
            return "Aucune application détectée"
    
    # Commande pour lister toutes les fenêtres ouvertes
    if any(cmd in texte for cmd in ["liste les fenêtres", "lister les fenêtres", 
                                   "quelles fenêtres sont ouvertes", "fenêtres ouvertes",
                                   "montre les fenêtres", "affiche les fenêtres",
                                   "montre toutes les fenêtres", "affiche toutes les fenêtres"]):
        fenetres = obtenir_fenetres_ouvertes()
        if fenetres:
            # Formater la liste des fenêtres
            fenetre_list = []
            for i, fenetre in enumerate(fenetres[:15], 1):
                fenetre_list.append(f"{i}. {fenetre['title']} ({fenetre['process_name']})")
            
            return f"Fenêtres ouvertes :\n" + "\n".join(fenetre_list) + (f"\n... et {len(fenetres) - 15} autres" if len(fenetres) > 15 else "")
        else:
            return "Aucune fenêtre détectée"
    
    # ===== GESTION DES FENÊTRES =====
    if any(cmd in texte for cmd in ["liste les fenêtres", "lister les fenêtres", "montre les fenêtres", 
                                   "montrer les fenêtres", "affiche les fenêtres", "afficher les fenêtres",
                                   "quelles sont les fenêtres", "quelles fenêtres sont ouvertes", 
                                   "fenêtres ouvertes", "applications ouvertes", "programmes ouverts",
                                   "liste des fenêtres", "liste des applications", "liste des programmes",
                                   "montre les applications", "montrer les applications", 
                                   "affiche les applications", "afficher les applications",
                                   "montre les programmes", "montrer les programmes", 
                                   "affiche les programmes", "afficher les programmes"]):
        try:
            if os_type == 'windows':
                # Commande Windows
                result = subprocess.run(["tasklist", "/FI", "SESSIONNAME eq Console", "/FO", "TABLE"], 
                                      capture_output=True, text=True, encoding='cp850')
                return f"Fenêtres actives :\n{result.stdout[:500]}..."  # Limiter la sortie
            elif os_type == 'mac':
                # Commande macOS
                result = subprocess.run(["ps", "-ax", "-o", "comm="], 
                                      capture_output=True, text=True)
                return f"Processus actifs :\n{result.stdout[:500]}..."
            elif os_type == 'linux':
                # Commande Linux
                result = subprocess.run(["ps", "-e", "-o", "comm="], 
                                      capture_output=True, text=True)
                return f"Processus actifs :\n{result.stdout[:500]}..."
            else:
                return "Système d'exploitation non pris en charge pour cette commande"
        except Exception as e:
            return f"Impossible de lister les fenêtres: {str(e)}"
    
    elif any(pattern in texte for pattern in ["active la fenêtre", "activer la fenêtre", "active fenêtre", 
                                            "activer fenêtre", "passe à la fenêtre", "passer à la fenêtre",
                                            "va à la fenêtre", "aller à la fenêtre", "bascule vers", 
                                            "basculer vers", "change de fenêtre", "changer de fenêtre",
                                            "focus sur", "focus sur la fenêtre", "mets le focus sur",
                                            "mettre le focus sur", "affiche la fenêtre", "afficher la fenêtre",
                                            "va sur la fenêtre", "aller sur la fenêtre"]):
        # Extraire le nom de la fenêtre avec différents patterns
        patterns = [
            r"active la fenêtre\s+(.+)", r"activer la fenêtre\s+(.+)", r"active fenêtre\s+(.+)",
            r"activer fenêtre\s+(.+)", r"passe à la fenêtre\s+(.+)", r"passer à la fenêtre\s+(.+)",
            r"va à la fenêtre\s+(.+)", r"aller à la fenêtre\s+(.+)", r"bascule vers\s+(.+)",
            r"basculer vers\s+(.+)", r"change de fenêtre\s+(.+)", r"changer de fenêtre\s+(.+)",
            r"focus sur\s+(.+)", r"focus sur la fenêtre\s+(.+)", r"mets le focus sur\s+(.+)",
            r"mettre le focus sur\s+(.+)", r"affiche la fenêtre\s+(.+)", r"afficher la fenêtre\s+(.+)",
            r"va sur la fenêtre\s+(.+)", r"aller sur la fenêtre\s+(.+)"
        ]
        
        fenetre_nom = None
        for pattern in patterns:
            match = re.search(pattern, texte)
            if match:
                fenetre_nom = match.group(1).strip()
                break
                
        if fenetre_nom:
            # Vérifier si c'est un numéro de fenêtre (après avoir listé les fenêtres)
            if fenetre_nom.isdigit():
                num_fenetre = int(fenetre_nom)
                fenetres = obtenir_fenetres_ouvertes()
                
                if 1 <= num_fenetre <= len(fenetres):
                    fenetre_cible = fenetres[num_fenetre - 1]
                    resultat = basculer_vers_fenetre(fenetre_cible['title'], par_titre=True, par_process=False, exact=True)
                    
                    if resultat:
                        return f"Navigation vers la fenêtre {num_fenetre} ({fenetre_cible['title']}) réussie"
                    else:
                        return f"Impossible de basculer vers la fenêtre {num_fenetre} ({fenetre_cible['title']})"
                else:
                    return f"Numéro de fenêtre invalide. Il y a {len(fenetres)} fenêtres ouvertes."
            
            # Sinon, rechercher par titre ou nom d'application
            resultat = basculer_vers_fenetre(fenetre_nom)
            
            if resultat:
                return f"Navigation vers la fenêtre '{fenetre_nom}' réussie"
            else:
                return f"Impossible de trouver ou d'activer la fenêtre '{fenetre_nom}'"
        else:
            return "Nom de fenêtre non spécifié"
    
    elif any(cmd in texte for cmd in ["arrange les fenêtres", "arranger les fenêtres", "organise les fenêtres", 
                                     "organiser les fenêtres", "dispose les fenêtres", "disposer les fenêtres",
                                     "place les fenêtres", "placer les fenêtres", "positionne les fenêtres", 
                                     "positionner les fenêtres", "aligne les fenêtres", "aligner les fenêtres"]):
        if any(pattern in texte for pattern in ["côte à côte", "côte-à-côte", "côte a côte", "côte-a-côte", 
                                              "l'une à côté de l'autre", "l'une a côté de l'autre", 
                                              "l'une près de l'autre", "l'une contre l'autre",
                                              "deux moitiés", "deux parties", "divise l'écran", "diviser l'écran",
                                              "partage l'écran", "partager l'écran", "split screen"]):
            pyautogui.hotkey('win', 'left')
            time.sleep(0.5)
            pyautogui.hotkey('win', 'right')
            return "Fenêtres arrangées côte à côte"
        elif any(pattern in texte for pattern in ["en cascade", "cascade", "superposées", "superposée", 
                                                "l'une sur l'autre", "l'une au-dessus de l'autre", 
                                                "empilées", "empilée", "en pile", "en tas"]):
            # Pas de raccourci standard pour cela, mais on peut utiliser le menu contextuel
            pyautogui.click(button='right', x=10, y=10)  # Clic droit sur la barre des tâches
            time.sleep(0.5)
            pyautogui.press('c')  # Option "Cascade" dans le menu
            return "Fenêtres arrangées en cascade"
        else:
            return "Type d'arrangement non spécifié"
    
    elif "capture la fenêtre active" in texte:
        pyautogui.hotkey('alt', 'printscreen')
        return "Capture de la fenêtre active dans le presse-papiers"
    
    elif "ferme toutes les fenêtres" in texte:
        pyautogui.hotkey('win', 'd')  # Afficher le bureau
        return "Toutes les fenêtres minimisées"
    
    # ===== COMMANDES DE FENÊTRES SUPPLÉMENTAIRES =====
    elif any(cmd in texte for cmd in ["maximise", "maximise la fenêtre", "agrandis", "agrandis la fenêtre", 
                                     "agrandi", "agrandi la fenêtre", "maximiser", "maximiser la fenêtre"]):
        if os_type == 'windows':
            # Utiliser Win+Up pour maximiser la fenêtre (sans passer en plein écran)
            pyautogui.hotkey('win', 'up')
            return "Fenêtre maximisée"
        elif os_type == 'mac':
            # Sur Mac, utiliser le zoom (bouton vert) ou Command+M
            try:
                # Méthode 1: Cliquer sur le bouton vert (zoom)
                current_x, current_y = pyautogui.position()
                window_pos = pyautogui.getActiveWindow() if hasattr(pyautogui, 'getActiveWindow') else None
                
                if window_pos:
                    # Cliquer sur le bouton vert (approximativement)
                    pyautogui.click(window_pos.left + 20, window_pos.top + 20)
                else:
                    # Alternative: utiliser Command+M pour maximiser
                    pyautogui.hotkey('command', 'm')
                
                # Restaurer la position de la souris
                pyautogui.moveTo(current_x, current_y)
            except:
                pass
            
            return "Fenêtre maximisée"
            
        elif os_type == 'linux':
            # Sur Linux, Alt+F10 est souvent utilisé pour maximiser
            pyautogui.hotkey('alt', 'f10')
            return "Fenêtre maximisée"
        
        return "Fenêtre maximisée"
        
    elif any(cmd in texte for cmd in ["minimise", "minimise la fenêtre", "réduis", "réduis la fenêtre", 
                                     "cache la fenêtre", "masque la fenêtre"]):
        if os_type == 'windows':
            pyautogui.hotkey('win', 'down')
        elif os_type == 'mac':
            # Sur Mac, Command+M
            pyautogui.hotkey('command', 'm')
        elif os_type == 'linux':
            # Sur Linux, Alt+F9 est souvent utilisé
            pyautogui.hotkey('alt', 'f9')
            
        return "Fenêtre minimisée"
        
    elif any(cmd in texte for cmd in ["restaure", "restaure la fenêtre", "taille normale", 
                                     "fenêtre normale", "rétablis", "rétablis la fenêtre"]):
        # Appuyer deux fois sur Win+Down pour restaurer depuis maximisé
        pyautogui.hotkey('win', 'down')
        time.sleep(0.1)
        pyautogui.hotkey('win', 'down')
        return "Fenêtre restaurée à sa taille normale"
        
    elif any(cmd in texte for cmd in ["ancre à gauche", "fenêtre à gauche", "place à gauche", 
                                     "positionne à gauche", "snap gauche", "moitié gauche"]):
        pyautogui.hotkey('win', 'left')
        return "Fenêtre ancrée à gauche"
        
    elif any(cmd in texte for cmd in ["ancre à droite", "fenêtre à droite", "place à droite", 
                                     "positionne à droite", "snap droite", "moitié droite"]):
        pyautogui.hotkey('win', 'right')
        return "Fenêtre ancrée à droite"
        
    elif any(cmd in texte for cmd in ["ancre en haut", "fenêtre en haut", "place en haut", 
                                     "positionne en haut", "snap haut", "moitié supérieure"]):
        pyautogui.hotkey('win', 'up')
        time.sleep(0.1)
        pyautogui.hotkey('win', 'up')  # Deux fois pour quart supérieur
        return "Fenêtre ancrée en haut"
        
    elif any(cmd in texte for cmd in ["ancre en bas", "fenêtre en bas", "place en bas", 
                                     "positionne en bas", "snap bas", "moitié inférieure"]):
        pyautogui.hotkey('win', 'down')
        time.sleep(0.1)
        pyautogui.hotkey('win', 'down')  # Deux fois pour quart inférieur
        return "Fenêtre ancrée en bas"
        
    elif any(cmd in texte for cmd in ["ferme la fenêtre", "ferme cette fenêtre", "ferme l'application", 
                                     "quitte l'application", "ferme le programme", "quitte le programme"]):
        if os_type == 'windows':
            pyautogui.hotkey('alt', 'f4')
        elif os_type == 'mac':
            pyautogui.hotkey('command', 'q')
        elif os_type == 'linux':
            pyautogui.hotkey('alt', 'f4')
            
        return "Fenêtre fermée"
        
    elif any(cmd in texte for cmd in ["affiche le bureau", "montre le bureau", "va au bureau", 
                                     "retourne au bureau", "bureau", "afficher bureau"]):
        if os_type == 'windows':
            pyautogui.hotkey('win', 'd')
        elif os_type == 'mac':
            # Sur Mac, F11 ou Command+F3 ou Command+Mission Control
            pyautogui.hotkey('command', 'f3')
        elif os_type == 'linux':
            # Sur Linux, Ctrl+Alt+D est souvent utilisé
            pyautogui.hotkey('ctrl', 'alt', 'd')
            
        return "Bureau affiché"
        
    elif any(cmd in texte for cmd in ["verrouille l'écran", "verrouille l'ordinateur", "verrouille le pc", 
                                     "verrouille la session", "verrouille windows", "lock"]):
        pyautogui.hotkey('win', 'l')
        return "Écran verrouillé"
        
    elif any(cmd in texte for cmd in ["affiche toutes les fenêtres", "montre toutes les fenêtres", 
                                     "vue d'ensemble", "vue des tâches", "task view", "affichage des tâches"]):
        pyautogui.hotkey('win', 'tab')
        return "Affichage de toutes les fenêtres"
        
    elif any(cmd in texte for cmd in ["bureau suivant", "bureau virtuel suivant", "espace suivant", 
                                     "espace de travail suivant", "desktop suivant"]):
        pyautogui.hotkey('win', 'ctrl', 'right')
        return "Passage au bureau virtuel suivant"
        
    elif any(cmd in texte for cmd in ["bureau précédent", "bureau virtuel précédent", "espace précédent", 
                                     "espace de travail précédent", "desktop précédent"]):
        pyautogui.hotkey('win', 'ctrl', 'left')
        return "Passage au bureau virtuel précédent"
        
    elif any(cmd in texte for cmd in ["nouveau bureau", "nouveau bureau virtuel", "nouvel espace", 
                                     "nouvel espace de travail", "crée un bureau", "crée un espace"]):
        pyautogui.hotkey('win', 'ctrl', 'd')
        return "Nouveau bureau virtuel créé"
        
    elif any(cmd in texte for cmd in ["ferme le bureau", "ferme bureau virtuel", "ferme cet espace", 
                                     "ferme espace de travail", "supprime ce bureau", "supprime cet espace"]):
        pyautogui.hotkey('win', 'ctrl', 'f4')
        return "Bureau virtuel fermé"
    
    # ===== COMMANDES MULTIÉCRAN =====
    elif any(cmd in texte for cmd in ["déplace vers écran", "déplace sur écran", "envoie vers écran", 
                                     "envoie sur écran", "mets sur écran", "place sur écran", 
                                     "déplace la fenêtre vers écran", "déplace la fenêtre sur écran"]):
        # Extraire le numéro d'écran
        match = re.search(r"écran\s+(\d+)", texte)
        if match:
            ecran_cible = int(match.group(1))
            return deplacer_fenetre_vers_ecran(ecran_cible)
        else:
            return "Numéro d'écran non spécifié"
    
    elif any(cmd in texte for cmd in ["étends l'affichage", "étendre l'affichage", "étends sur tous les écrans", 
                                     "étendre sur tous les écrans", "mode étendu", "affichage étendu"]):
        # Ouvrir les paramètres d'affichage Windows
        pyautogui.hotkey('win', 'p')
        time.sleep(0.5)
        # Sélectionner "Étendre"
        for _ in range(3):  # Appuyer sur flèche bas jusqu'à "Étendre"
            pyautogui.press('down')
            time.sleep(0.1)
        pyautogui.press('enter')
        return "Mode d'affichage étendu activé"
    
    elif any(cmd in texte for cmd in ["duplique l'affichage", "dupliquer l'affichage", "duplique sur tous les écrans", 
                                     "dupliquer sur tous les écrans", "mode dupliquer", "affichage dupliqué"]):
        # Ouvrir les paramètres d'affichage Windows
        pyautogui.hotkey('win', 'p')
        time.sleep(0.5)
        # Sélectionner "Dupliquer"
        for _ in range(1):  # Appuyer sur flèche bas jusqu'à "Dupliquer"
            pyautogui.press('down')
            time.sleep(0.1)
        pyautogui.press('enter')
        return "Mode d'affichage dupliqué activé"
    
    elif any(cmd in texte for cmd in ["écran principal uniquement", "écran principal seulement", 
                                     "uniquement écran principal", "seulement écran principal", 
                                     "désactive écrans secondaires", "désactiver écrans secondaires"]):
        # Ouvrir les paramètres d'affichage Windows
        pyautogui.hotkey('win', 'p')
        time.sleep(0.5)
        # Sélectionner "PC Screen only"
        pyautogui.press('enter')  # La première option est "PC Screen only"
        return "Affichage sur écran principal uniquement"
    
    elif any(cmd in texte for cmd in ["écran secondaire uniquement", "écran secondaire seulement", 
                                     "uniquement écran secondaire", "seulement écran secondaire", 
                                     "désactive écran principal", "désactiver écran principal"]):
        # Ouvrir les paramètres d'affichage Windows
        pyautogui.hotkey('win', 'p')
        time.sleep(0.5)
        # Sélectionner "Second Screen only"
        for _ in range(2):  # Appuyer sur flèche bas jusqu'à "Second Screen only"
            pyautogui.press('down')
            time.sleep(0.1)
        pyautogui.press('enter')
        return "Affichage sur écran secondaire uniquement"
    
    elif any(cmd in texte for cmd in ["combien d'écrans", "nombre d'écrans", "écrans connectés", 
                                     "écrans disponibles", "moniteurs connectés", "moniteurs disponibles"]):
        nb_ecrans = get_monitor_count()
        return f"{nb_ecrans} écran{'s' if nb_ecrans > 1 else ''} connecté{'s' if nb_ecrans > 1 else ''}"
    
    elif any(cmd in texte for cmd in ["maximise sur tous les écrans", "plein écran sur tous les écrans", 
                                     "étends la fenêtre sur tous les écrans", "fenêtre sur tous les écrans"]):
        # Cette fonctionnalité nécessite généralement un logiciel tiers
        # Nous pouvons simuler en maximisant sur l'écran actuel
        pyautogui.hotkey('win', 'up')
        return "Fenêtre maximisée (note: l'extension sur tous les écrans peut nécessiter un logiciel spécifique)"
    
    return None  # Commande non reconnue

# Fonctions pour la gestion des écrans multiples adaptées à chaque OS
def get_monitor_count():
    """Obtient le nombre d'écrans connectés"""
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Méthode Windows
            user32 = ctypes.WinDLL('user32')
            user32.GetSystemMetrics.restype = ctypes.c_int
            SM_CMONITORS = 80  # Nombre d'écrans
            return user32.GetSystemMetrics(SM_CMONITORS)
        
        elif os_type == 'mac':
            # Méthode macOS
            try:
                import Quartz
                displays = Quartz.CGGetActiveDisplayList(10, None, None)[1]
                return len(displays) if displays else 1
            except (ImportError, AttributeError):
                # Méthode alternative avec subprocess
                result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                      capture_output=True, text=True)
                # Compter les occurrences de "Display Type" dans la sortie
                return result.stdout.count("Display Type") or 1
        
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser xrandr pour obtenir les écrans
                result = subprocess.run(["xrandr", "--listmonitors"], 
                                      capture_output=True, text=True)
                # La première ligne contient le nombre d'écrans (ex: "Monitors: 2")
                first_line = result.stdout.strip().split('\n')[0]
                count = int(first_line.split(':')[1].strip())
                return count
            except:
                # Méthode alternative
                try:
                    import Xlib.display
                    d = Xlib.display.Display()
                    screen_count = d.screen_count()
                    return screen_count
                except:
                    return 1
        
        else:
            return 1
    
    except Exception as e:
        print(f"Erreur lors de la détection du nombre d'écrans: {e}")
        return 1

def deplacer_fenetre_vers_ecran(ecran_cible):
    """Déplace la fenêtre active vers l'écran spécifié"""
    os_type = get_os_type()
    
    try:
        # Obtenir le nombre d'écrans
        nb_ecrans = get_monitor_count()
        
        if nb_ecrans < 2:
            return "Un seul écran détecté"
        
        # Vérifier que l'écran cible est valide
        if ecran_cible < 1 or ecran_cible > nb_ecrans:
            return f"Écran {ecran_cible} non valide. {nb_ecrans} écrans disponibles."
        
        if os_type == 'windows':
            # Méthode Windows
            # Obtenir la fenêtre active
            if is_windows():
                hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            # Méthode plus fiable pour déplacer les fenêtres entre écrans
            if ecran_cible == 1:  # Écran principal
                # Utiliser Win+Shift+Flèche gauche pour déplacer vers l'écran principal
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('left')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
                # Répéter pour s'assurer que la fenêtre est bien sur l'écran principal
                time.sleep(0.5)
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('left')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
            elif ecran_cible == 2:  # Deuxième écran
                # Utiliser Win+Shift+Flèche droite pour déplacer vers l'écran secondaire
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
            elif ecran_cible == 3:  # Troisième écran (si disponible)
                # Déplacer d'abord vers le deuxième écran
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
                # Puis vers le troisième écran
                time.sleep(0.5)
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
            
            # Maximiser la fenêtre sur le nouvel écran (optionnel)
            time.sleep(0.5)
            pyautogui.keyDown('win')
            time.sleep(0.2)
            pyautogui.press('up')
            time.sleep(0.2)
            pyautogui.keyUp('win')
            
        elif os_type == 'mac':
            # Méthode macOS
            # Sur macOS, on peut utiliser AppleScript pour déplacer les fenêtres
            try:
                # Obtenir les dimensions des écrans
                script = '''
                tell application "System Events"
                    set screenBounds to bounds of every desktop
                    return screenBounds
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                
                # Déplacer la fenêtre active vers l'écran cible
                # Note: Cette approche est simplifiée et peut nécessiter des ajustements
                if ecran_cible == 1:
                    script = '''
                    tell application "System Events"
                        set frontWindow to first window of (first process whose frontmost is true)
                        set position of frontWindow to {0, 0}
                    end tell
                    '''
                elif ecran_cible == 2:
                    script = '''
                    tell application "System Events"
                        set frontWindow to first window of (first process whose frontmost is true)
                        set screenWidth to item 3 of bounds of desktop 1
                        set position of frontWindow to {screenWidth + 50, 50}
                    end tell
                    '''
                
                subprocess.run(["osascript", "-e", script], capture_output=True)
            except Exception as e:
                return f"Erreur lors du déplacement de la fenêtre sur macOS: {str(e)}"
            
        elif os_type == 'linux':
            # Méthode Linux
            # Sur Linux, on peut utiliser wmctrl pour déplacer les fenêtres
            try:
                # Obtenir l'ID de la fenêtre active
                result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True)
                window_id = result.stdout.strip()
                
                # Obtenir les informations sur les écrans
                result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True)
                
                # Déplacer la fenêtre vers l'écran cible
                if ecran_cible == 1:
                    # Déplacer vers le premier écran (généralement à la position 0,0)
                    subprocess.run(["wmctrl", "-i", "-r", window_id, "-e", "0,0,0,-1,-1"])
                elif ecran_cible == 2:
                    # Déplacer vers le deuxième écran (position approximative)
                    # Note: Cette approche est simplifiée et peut nécessiter des ajustements
                    subprocess.run(["wmctrl", "-i", "-r", window_id, "-e", "0,1920,0,-1,-1"])
            except Exception as e:
                return f"Erreur lors du déplacement de la fenêtre sur Linux: {str(e)}"
        
        return f"Fenêtre déplacée vers l'écran {ecran_cible}"
    except Exception as e:
        return f"Erreur lors du déplacement de la fenêtre: {str(e)}"

def basculer_vers_fenetre(recherche, par_titre=True, par_process=True, exact=False):
    """
    Bascule vers une fenêtre spécifique en recherchant par titre ou par nom de processus
    
    Args:
        recherche (str): Texte à rechercher dans le titre ou le nom du processus
        par_titre (bool): Rechercher dans le titre de la fenêtre
        par_process (bool): Rechercher dans le nom du processus
        exact (bool): Correspondance exacte ou partielle
        
    Returns:
        bool: True si la fenêtre a été trouvée et activée, False sinon
    """
    os_type = get_os_type()
    recherche_lower = recherche.lower()
    
    # Journalisation pour le débogage
    print(f"Tentative de basculer vers la fenêtre: '{recherche}' (titre: {par_titre}, process: {par_process}, exact: {exact})")
    
    try:
        if os_type == 'windows':
            # Obtenir la liste des fenêtres
            fenetres = obtenir_fenetres_ouvertes()
            
            # Rechercher la fenêtre correspondante
            fenetre_trouvee = None
            
            for fenetre in fenetres:
                match_titre = False
                match_process = False
                
                if par_titre and fenetre['title']:
                    if exact:
                        match_titre = fenetre['title'].lower() == recherche_lower
                    else:
                        match_titre = recherche_lower in fenetre['title'].lower()
                
                if par_process and fenetre['process_name']:
                    if exact:
                        match_process = fenetre['process_name'] == recherche_lower
                    else:
                        match_process = recherche_lower in fenetre['process_name']
                
                if match_titre or match_process:
                    fenetre_trouvee = fenetre
                    break
            
            # Si une fenêtre correspondante est trouvée, l'activer
            if fenetre_trouvee:
                hwnd = fenetre_trouvee['hwnd']
                print(f"Fenêtre trouvée: '{fenetre_trouvee['title']}' ({fenetre_trouvee['process_name']})")
                
                # Importer les modules nécessaires
                import win32gui
                import win32con
                import win32api
                import win32process
                
                # Vérifier si la fenêtre est minimisée
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMINIMIZED:
                    # Restaurer la fenêtre si elle est minimisée
                    print("Restauration de la fenêtre minimisée")
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Méthode 0: Traitement spécial pour certaines applications problématiques
                try:
                    process_name = fenetre_trouvee['process_name'].lower()
                    
                    # Traitement spécial pour WhatsApp et ApplicationFrameHost
                    if "whatsapp" in process_name or "applicationframehost" in process_name:
                        # Utiliser Win+Numéro pour les applications épinglées à la barre des tâches
                        # Cette méthode est la plus fiable pour WhatsApp et les applications UWP
                        try:
                            print("Tentative avec Win+Numéro pour application spéciale")
                            
                            # Définir les constantes pour SendInput
                            KEYEVENTF_KEYDOWN = 0x0000
                            KEYEVENTF_KEYUP = 0x0002
                            VK_LWIN = 0x5B  # Touche Windows gauche
                            
                            # Créer une structure d'entrée clavier
                            class KEYBDINPUT(ctypes.Structure):
                                _fields_ = [
                                    ("wVk", ctypes.c_ushort),
                                    ("wScan", ctypes.c_ushort),
                                    ("dwFlags", ctypes.c_ulong),
                                    ("time", ctypes.c_ulong),
                                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                                ]
                            
                            class INPUT(ctypes.Structure):
                                _fields_ = [
                                    ("type", ctypes.c_ulong),
                                    ("ki", KEYBDINPUT),
                                    ("padding", ctypes.c_ubyte * 8)
                                ]
                            
                            # Essayer les positions 1 à 9 dans la barre des tâches
                            for position in range(1, 10):
                                # Convertir la position en code de touche virtuelle
                                vk_position = 0x30 + position  # 0x31 = 1, 0x32 = 2, etc.
                                
                                # Appuyer sur Win
                                win_down = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(win_down), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Appuyer sur le numéro
                                num_down = INPUT(1, KEYBDINPUT(vk_position, 0, KEYEVENTF_KEYDOWN, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(num_down), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Relâcher le numéro
                                num_up = INPUT(1, KEYBDINPUT(vk_position, 0, KEYEVENTF_KEYUP, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(num_up), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Relâcher Win
                                win_up = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYUP, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(win_up), ctypes.sizeof(INPUT))
                                time.sleep(0.3)
                                
                                # Vérifier si nous sommes sur la bonne fenêtre
                                active_hwnd = win32gui.GetForegroundWindow()
                                if active_hwnd == hwnd:
                                    print(f"Fenêtre activée via Win+{position}")
                                    return True
                                
                                # Si ce n'est pas la bonne fenêtre mais que c'est une fenêtre de la même application
                                active_app, _, _ = get_active_application()
                                if active_app.lower() == process_name:
                                    print(f"Application activée via Win+{position} (fenêtre différente)")
                                    return True
                        except Exception as e:
                            print(f"Erreur Win+Numéro pour application spéciale: {e}")
                except Exception as e:
                    print(f"Erreur traitement spécial: {e}")
                
                # Méthode 1: Utiliser SetForegroundWindow directement avec contournement des restrictions
                try:
                    print("Tentative avec SetForegroundWindow")
                    # Obtenir le PID du processus
                    pid = fenetre_trouvee['pid']
                    
                    # Contourner les restrictions de sécurité de Windows
                    # Définir les constantes nécessaires
                    SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
                    SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
                    SPIF_SENDCHANGE = 0x2
                    
                    # Sauvegarder le timeout actuel
                    timeout_buffer = ctypes.c_ulong()
                    ctypes.windll.user32.SystemParametersInfoW(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, 
                                                             ctypes.byref(timeout_buffer), 0)
                    original_timeout = timeout_buffer.value
                    
                    # Définir le timeout à 0 pour permettre le changement immédiat
                    try:
                        ctypes.windll.user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 
                                                                 ctypes.c_ulong(0), SPIF_SENDCHANGE)
                    except:
                        pass
                    
                    # Autoriser le changement de fenêtre active
                    try:
                        # ASFW_ANY permet à n'importe quelle application de prendre le focus
                        ASFW_ANY = -1
                        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
                        # Puis autoriser spécifiquement notre PID cible
                        ctypes.windll.user32.AllowSetForegroundWindow(pid)
                    except:
                        pass
                    
                    # Mettre la fenêtre au premier plan
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                    # Attacher notre thread au thread de la fenêtre cible
                    foreground_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(
                        ctypes.windll.user32.GetForegroundWindow(), None)
                    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
                    
                    if foreground_thread_id != current_thread_id:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, True)
                            attached = True
                        except:
                            attached = False
                    else:
                        attached = False
                    
                    # Essayer SetForegroundWindow
                    result = win32gui.SetForegroundWindow(hwnd)
                    
                    # Détacher notre thread si nécessaire
                    if attached:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
                        except:
                            pass
                    
                    # Restaurer le timeout original
                    try:
                        ctypes.windll.user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0, 
                                                                 ctypes.c_ulong(original_timeout), SPIF_SENDCHANGE)
                    except:
                        pass
                    
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec SetForegroundWindow")
                        return True
                except Exception as e:
                    print(f"Erreur SetForegroundWindow: {e}")
                
                # Méthode 2: Utiliser SwitchToThisWindow
                try:
                    print("Tentative avec SwitchToThisWindow")
                    # Utiliser SwitchToThisWindow pour activer la fenêtre
                    ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
                    time.sleep(0.1)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec SwitchToThisWindow")
                        return True
                except Exception as e:
                    print(f"Erreur SwitchToThisWindow: {e}")
                
                # Méthode 3: Utiliser BringWindowToTop avec technique avancée
                try:
                    print("Tentative avec BringWindowToTop et technique avancée")
                    
                    # Définir les constantes
                    ASFW_ANY = -1
                    
                    # Obtenir le thread ID de la fenêtre cible et de notre thread
                    target_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
                    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
                    
                    # Attacher notre thread au thread de la fenêtre cible
                    attached = False
                    if target_thread_id != current_thread_id:
                        try:
                            attached = ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
                        except:
                            pass
                    
                    # Autoriser n'importe quelle fenêtre à devenir active
                    try:
                        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
                    except:
                        pass
                    
                    # Mettre la fenêtre au premier plan avec plusieurs techniques
                    try:
                        # S'assurer que la fenêtre est visible
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        
                        # Forcer la fenêtre au premier plan
                        win32gui.BringWindowToTop(hwnd)
                        
                        # Simuler un clic sur la barre de titre (technique alternative)
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        title_x = left + (right - left) // 2
                        title_y = top + 10  # Position approximative de la barre de titre
                        
                        # Sauvegarder la position actuelle de la souris
                        old_pos = win32api.GetCursorPos()
                        
                        # Déplacer la souris et simuler un clic
                        win32api.SetCursorPos((title_x, title_y))
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        
                        # Restaurer la position de la souris
                        win32api.SetCursorPos(old_pos)
                        
                        # Essayer SetForegroundWindow après le clic
                        win32gui.SetForegroundWindow(hwnd)
                    except:
                        pass
                    
                    # Détacher notre thread si nécessaire
                    if attached:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
                        except:
                            pass
                    
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec BringWindowToTop et technique avancée")
                        return True
                except Exception as e:
                    print(f"Erreur BringWindowToTop: {e}")
                
                # Méthode 4: Utiliser PostMessage pour envoyer un message d'activation
                try:
                    print("Tentative avec PostMessage")
                    
                    # Envoyer un message WM_SYSCOMMAND avec SC_RESTORE pour restaurer la fenêtre
                    win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
                    time.sleep(0.1)
                    
                    # Envoyer un message WM_ACTIVATE pour activer la fenêtre
                    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
                    time.sleep(0.1)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec PostMessage")
                        return True
                except Exception as e:
                    print(f"Erreur PostMessage: {e}")
                
                # Méthode 5: Cliquer sur la barre de titre de la fenêtre
                try:
                    print("Tentative avec clic sur la barre de titre")
                    # Obtenir les coordonnées de la fenêtre
                    left, top, width, height = fenetre_trouvee['position']
                    
                    if width > 0 and height > 0:
                        # Sauvegarder la position actuelle de la souris
                        current_x, current_y = pyautogui.position()
                        
                        # Calculer la position de la barre de titre (plus précis que le centre)
                        title_x = left + (width // 2)
                        title_y = top + 15  # Environ 15 pixels depuis le haut
                        
                        # Utiliser SetCursorPos et mouse_event (plus discret que pyautogui)
                        ctypes.windll.user32.SetCursorPos(title_x, title_y)
                        time.sleep(0.1)
                        
                        # Simuler un clic gauche
                        ctypes.windll.user32.mouse_event(
                            0x0002,  # MOUSEEVENTF_LEFTDOWN
                            0, 0, 0, 0
                        )
                        time.sleep(0.05)
                        ctypes.windll.user32.mouse_event(
                            0x0004,  # MOUSEEVENTF_LEFTUP
                            0, 0, 0, 0
                        )
                        
                        time.sleep(0.1)
                        
                        # Restaurer la position de la souris
                        ctypes.windll.user32.SetCursorPos(current_x, current_y)
                        
                        # Vérifier si la fenêtre est maintenant active
                        active_hwnd = win32gui.GetForegroundWindow()
                        if active_hwnd == hwnd:
                            print("Fenêtre activée avec clic sur la barre de titre")
                            return True
                except Exception as e:
                    print(f"Erreur clic sur la barre de titre: {e}")
                
                # Méthode 6: Utiliser Win+T pour naviguer dans la barre des tâches
                try:
                    print("Tentative avec Win+T (navigation barre des tâches)")
                    
                    # Définir les constantes pour SendInput
                    KEYEVENTF_KEYDOWN = 0x0000
                    KEYEVENTF_KEYUP = 0x0002
                    VK_LWIN = 0x5B  # Touche Windows gauche
                    VK_T = 0x54     # Touche T
                    
                    # Créer une structure d'entrée clavier
                    class KEYBDINPUT(ctypes.Structure):
                        _fields_ = [
                            ("wVk", ctypes.c_ushort),
                            ("wScan", ctypes.c_ushort),
                            ("dwFlags", ctypes.c_ulong),
                            ("time", ctypes.c_ulong),
                            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                        ]
                    
                    class INPUT(ctypes.Structure):
                        _fields_ = [
                            ("type", ctypes.c_ulong),
                            ("ki", KEYBDINPUT),
                            ("padding", ctypes.c_ubyte * 8)
                        ]
                    
                    # Appuyer sur Win+T pour activer la barre des tâches
                    win_down = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(win_down), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    t_down = INPUT(1, KEYBDINPUT(VK_T, 0, KEYEVENTF_KEYDOWN, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(t_down), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    t_up = INPUT(1, KEYBDINPUT(VK_T, 0, KEYEVENTF_KEYUP, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(t_up), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    # Relâcher Win
                    win_up = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYUP, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(win_up), ctypes.sizeof(INPUT))
                    
                    # Naviguer dans la barre des tâches (max 10 fois)
                    for _ in range(10):
                        # Appuyer sur Tab pour naviguer
                        pyautogui.press('tab')
                        time.sleep(0.1)
                        
                        # Appuyer sur Entrée pour sélectionner
                        pyautogui.press('enter')
                        time.sleep(0.2)
                        
                        # Vérifier si nous sommes sur la bonne fenêtre
                        active_hwnd = win32gui.GetForegroundWindow()
                        if active_hwnd == hwnd:
                            print("Fenêtre activée via Win+T et navigation")
                            return True
                        
                        # Vérifier si nous sommes sur une fenêtre de la même application
                        active_app, _, _ = get_active_application()
                        if active_app.lower() == fenetre_trouvee['process_name'].lower():
                            print("Application activée via Win+T (fenêtre différente)")
                            return True
                        
                        # Revenir à la barre des tâches
                        pyautogui.hotkey('win', 't')
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Erreur Win+T: {e}")
                
                # Méthode 7: Utiliser Alt+Espace puis R (Restaurer) ou M (Déplacer)
                try:
                    print("Tentative avec Alt+Espace (menu système)")
                    
                    # Appuyer sur Alt+Espace pour ouvrir le menu système
                    pyautogui.hotkey('alt', 'space')
                    time.sleep(0.1)
                    
                    # Appuyer sur R pour Restaurer
                    pyautogui.press('r')
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Espace, R")
                        return True
                    
                    # Si ça n'a pas fonctionné, essayer avec M pour Déplacer
                    pyautogui.hotkey('alt', 'space')
                    time.sleep(0.1)
                    pyautogui.press('m')
                    time.sleep(0.1)
                    
                    # Appuyer sur une flèche puis Entrée pour confirmer
                    pyautogui.press('right')
                    time.sleep(0.1)
                    pyautogui.press('enter')
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Espace, M")
                        return True
                except Exception as e:
                    print(f"Erreur Alt+Espace: {e}")
                
                # Si toutes les méthodes ont échoué mais que nous avons trouvé la fenêtre
                print("Fenêtre trouvée mais impossible de l'activer avec les méthodes directes")
                
                # Dernière tentative: utiliser Alt+Tab une seule fois
                try:
                    print("Tentative avec Alt+Tab simple")
                    # Simuler Alt+Tab une seule fois
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.2)
                    
                    # Vérifier si nous sommes sur la bonne fenêtre ou application
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Tab simple")
                        return True
                    
                    # Vérifier si nous sommes sur une fenêtre de la même application
                    active_app, _, _ = get_active_application()
                    if active_app.lower() == fenetre_trouvee['process_name'].lower():
                        print("Application activée via Alt+Tab simple (fenêtre différente)")
                        return True
                except Exception as e:
                    print(f"Erreur Alt+Tab simple: {e}")
                
                return False
            
            # Si aucune fenêtre n'est trouvée, essayer d'ouvrir l'application
            print(f"Aucune fenêtre trouvée pour '{recherche}', tentative d'ouverture")
            
            # Méthode 1: Utiliser WScript.Shell.AppActivate
            try:
                print(f"Essai de la méthode WScript.Shell.AppActivate pour {recherche}")
                result = subprocess.run(["powershell", "-Command", 
                                       f"(New-Object -ComObject WScript.Shell).AppActivate('{recherche}')"],
                                       capture_output=True, text=True)
                
                # Vérifier si la commande a réussi
                if "True" in result.stdout:
                    print(f"Méthode WScript.Shell.AppActivate réussie pour {recherche}")
                    return True
            except Exception as e:
                print(f"Erreur avec WScript.Shell.AppActivate: {e}")
            
            # Méthode 2: Utiliser la recherche Windows pour ouvrir l'application
            try:
                print(f"Tentative d'ouverture via la recherche Windows pour {recherche}")
                
                # Méthode 1: Utiliser directement la touche Windows (méthode la plus rapide et discrète)
                pyautogui.press('win')
                time.sleep(0.3)
                
                # Taper le nom de l'application
                pyautogui.write(recherche)
                time.sleep(0.5)
                
                # Appuyer sur Entrée pour ouvrir la première suggestion
                pyautogui.press('enter')
                time.sleep(1)
                
                # Vérifier si une nouvelle fenêtre correspondante est maintenant active
                app_name, window_title, exe_path = get_active_application()
                if (recherche_lower in app_name.lower() or 
                    recherche_lower in window_title.lower()):
                    print(f"Application {recherche} ouverte via touche Windows")
                    return True
                
                # Méthode supprimée: Win+R n'est plus utilisé comme demandé
                
                # Méthode 3: Essayer de lancer directement via subprocess (silencieux)
                try:
                    subprocess.Popen(recherche, shell=True)
                    time.sleep(1)
                    
                    # Vérifier si une nouvelle fenêtre correspondante est maintenant active
                    app_name, window_title, exe_path = get_active_application()
                    if (recherche_lower in app_name.lower() or 
                        recherche_lower in window_title.lower()):
                        print(f"Application {recherche} ouverte via subprocess")
                        return True
                except:
                    pass
                
                return False
            except Exception as e:
                print(f"Erreur lors de l'ouverture via la recherche Windows: {e}")
                return False
            
        elif os_type == 'mac':
            # Méthode macOS
            script = f'''
            tell application "{recherche}"
                activate
            end tell
            '''
            try:
                subprocess.run(["osascript", "-e", script], capture_output=True)
                return True
            except:
                return False
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser wmctrl pour activer la fenêtre
                result = subprocess.run(["wmctrl", "-a", recherche], capture_output=True)
                return result.returncode == 0
            except:
                return False
        
        return False
    except:
        return False

def basculer_vers_application(nom_app):
    """
    Bascule vers une application spécifique si elle est ouverte (fonction de compatibilité)
    Utilise la nouvelle fonction basculer_vers_fenetre
    """
    print(f"Appel de basculer_vers_application avec {nom_app}")
    
    # Utiliser la nouvelle fonction plus robuste
    return basculer_vers_fenetre(nom_app, par_titre=True, par_process=True, exact=False)

def obtenir_fenetres_ouvertes():
    """Obtient la liste des fenêtres actuellement ouvertes avec leurs informations"""
    os_type = get_os_type()
    fenetres = []
    
    try:
        if os_type == 'windows':
            # Méthode Windows avec win32gui
            import win32gui
            import win32process
            import psutil
            
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # Ignorer certaines fenêtres système
                    if window_title and not window_title.startswith("Default IME") and not window_title == "Program Manager":
                        try:
                            # Obtenir le PID du processus
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            
                            # Obtenir le nom de l'exécutable
                            try:
                                process = psutil.Process(pid)
                                process_name = process.name()
                                
                                # Nettoyer le nom du processus (enlever l'extension .exe)
                                if process_name.lower().endswith('.exe'):
                                    process_name = process_name[:-4]
                                
                                # Obtenir le chemin complet de l'exécutable
                                try:
                                    exe_path = process.exe()
                                except (psutil.AccessDenied, AttributeError):
                                    exe_path = ""
                                
                                # Obtenir les coordonnées de la fenêtre
                                try:
                                    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                                    width = right - left
                                    height = bottom - top
                                except:
                                    left, top, width, height = 0, 0, 0, 0
                                
                                # Ajouter les informations de la fenêtre
                                results.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': process_name.lower(),
                                    'pid': pid,
                                    'exe_path': exe_path,
                                    'position': (left, top, width, height)
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # Ajouter avec des informations limitées
                                results.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': "unknown",
                                    'pid': pid,
                                    'exe_path': "",
                                    'position': (0, 0, 0, 0)
                                })
                        except:
                            pass
            
            windows_list = []
            win32gui.EnumWindows(enum_windows_callback, windows_list)
            
            # Trier les fenêtres par titre pour faciliter la recherche
            windows_list.sort(key=lambda x: x['title'].lower())
            
            return windows_list
        
        elif os_type == 'mac':
            # Méthode macOS - à implémenter
            return []
            
        elif os_type == 'linux':
            # Méthode Linux - à implémenter
            return []
            
        else:
            return []
            
    except Exception as e:
        print(f"Erreur lors de l'obtention des fenêtres ouvertes: {e}")
        return []

def obtenir_applications_ouvertes():
    """Obtient la liste des applications actuellement ouvertes"""
    os_type = get_os_type()
    applications = []
    
    try:
        if os_type == 'windows':
            # Utiliser la fonction obtenir_fenetres_ouvertes pour obtenir des informations plus détaillées
            fenetres = obtenir_fenetres_ouvertes()
            
            # Extraire les noms d'applications uniques
            app_names = set()
            for fenetre in fenetres:
                if fenetre['process_name'] and fenetre['process_name'] != "unknown":
                    app_names.add(fenetre['process_name'])
            
            applications = list(app_names)
            
            # Si aucune fenêtre n'est trouvée, utiliser la méthode tasklist comme fallback
            if not applications:
                result = subprocess.run(["tasklist", "/FO", "CSV"], capture_output=True, text=True, encoding='cp850')
                
                # Analyser la sortie pour extraire les noms des applications
                for line in result.stdout.splitlines()[1:]:  # Ignorer l'en-tête
                    if '","' in line:
                        parts = line.split('","')
                        if len(parts) >= 1:
                            app_name = parts[0].strip('"')
                            # Nettoyer le nom (enlever l'extension .exe)
                            if app_name.lower().endswith('.exe'):
                                app_name = app_name[:-4]
                            applications.append(app_name)
            
        elif os_type == 'mac':
            # Méthode macOS
            script = '''
            tell application "System Events"
                set appList to name of every process where background only is false
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            # Analyser la sortie
            if result.stdout:
                applications = [app.strip() for app in result.stdout.split(',')]
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser wmctrl pour lister les fenêtres
                result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
                
                # Analyser la sortie
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 4:
                        # Le nom de l'application est généralement après le 3ème champ
                        app_name = ' '.join(parts[3:])
                        applications.append(app_name)
            except:
                # Méthode alternative
                result = subprocess.run(["ps", "-e", "-o", "comm="], capture_output=True, text=True)
                applications = [line.strip() for line in result.stdout.splitlines()]
        
        # Filtrer les doublons et les entrées vides
        applications = list(set([app for app in applications if app]))
        
        return applications
    
    except Exception as e:
        print(f"Erreur lors de l'obtention des applications ouvertes: {e}")
        return []

def get_active_application():
    """
    Détecte l'application active actuellement
    
    Returns:
        tuple: (nom_application, titre_fenetre)
    """
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Méthode Windows
            import win32gui
            import win32process
            import psutil
            
            # Obtenir le handle de la fenêtre active
            hwnd = win32gui.GetForegroundWindow()
            
            # Obtenir le titre de la fenêtre
            window_title = win32gui.GetWindowText(hwnd)
            
            # Obtenir le PID du processus
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Obtenir le nom de l'exécutable
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                
                # Nettoyer le nom du processus (enlever l'extension .exe)
                if process_name.lower().endswith('.exe'):
                    process_name = process_name[:-4]
                
                # Obtenir le chemin complet de l'exécutable
                try:
                    exe_path = process.exe()
                except (psutil.AccessDenied, AttributeError):
                    exe_path = ""
                
                return (process_name.lower(), window_title, exe_path)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return ("unknown", window_title, "")
                
        elif os_type == 'mac':
            # Méthode macOS
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontWindow to ""
                try
                    tell process frontApp
                        set frontWindow to name of front window
                    end tell
                end try
                return {frontApp, frontWindow}
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.stdout:
                parts = result.stdout.strip().split(', ')
                app_name = parts[0].lower() if parts and len(parts) > 0 else "unknown"
                window_title = parts[1] if parts and len(parts) > 1 else ""
                return (app_name, window_title, "")
            else:
                return ("unknown", "", "")
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser xdotool pour obtenir le nom de la fenêtre active
                window_id = subprocess.run(["xdotool", "getactivewindow"], 
                                         capture_output=True, text=True).stdout.strip()
                
                window_title = subprocess.run(["xdotool", "getwindowname", window_id], 
                                            capture_output=True, text=True).stdout.strip()
                
                # Utiliser wmctrl pour obtenir des informations sur la fenêtre
                wmctrl_output = subprocess.run(["wmctrl", "-l", "-p"], 
                                             capture_output=True, text=True).stdout
                
                # Chercher la ligne correspondant à la fenêtre active
                for line in wmctrl_output.splitlines():
                    if window_id in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            pid = parts[2]
                            # Obtenir le nom du processus à partir du PID
                            process_name = subprocess.run(["ps", "-p", pid, "-o", "comm="], 
                                                        capture_output=True, text=True).stdout.strip()
                            return (process_name.lower(), window_title, "")
                
                return ("unknown", window_title, "")
            except:
                return ("unknown", "", "")
        
        else:
            return ("unknown", "", "")
            
    except Exception as e:
        print(f"Erreur lors de la détection de l'application active: {e}")
        return ("unknown", "")

def is_browser_active():
    """
    Vérifie si le navigateur est l'application active
    
    Returns:
        bool: True si un navigateur est actif, False sinon
    """
    app_name, _, _ = get_active_application()
    
    browsers = [
        "chrome", "googlechrome", "google chrome",
        "firefox", "mozilla firefox", 
        "edge", "msedge", "microsoft edge",
        "safari", 
        "opera",
        "brave",
        "vivaldi"
    ]
    
    return any(browser in app_name for browser in browsers)

def get_active_browser():
    """
    Détecte le navigateur actif
    
    Returns:
        str: Nom du navigateur actif ou None
    """
    app_name, _, _ = get_active_application()
    
    if "chrome" in app_name:
        return "chrome"
    elif "firefox" in app_name:
        return "firefox"
    elif "edge" in app_name:
        return "edge"
    elif "safari" in app_name:
        return "safari"
    elif "opera" in app_name:
        return "opera"
    elif "brave" in app_name:
        return "brave"
    elif "vivaldi" in app_name:
        return "vivaldi"
    else:
        return None

def get_active_browser_tab_info():
    """
    Tente de détecter l'URL et le titre de l'onglet actif du navigateur
    
    Returns:
        tuple: (url, title) ou (None, None) si impossible à détecter
    """
    browser = get_active_browser()
    if not browser:
        return (None, None)
    
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Pour Chrome/Edge sur Windows
            if browser in ["chrome", "edge", "brave"]:
                # Obtenir le titre de la fenêtre qui contient généralement le titre de la page
                _, window_title, _ = get_active_application()
                
                # Le titre de la fenêtre est généralement "Titre de la page - Navigateur"
                page_title = window_title.split(" - ")[0] if " - " in window_title else window_title
                
                # Impossible d'obtenir l'URL directement sans extension de navigateur
                return (None, page_title)
                
            # Pour Firefox sur Windows
            elif browser == "firefox":
                _, window_title, _ = get_active_application()
                page_title = window_title.split(" — ")[0] if " — " in window_title else window_title
                return (None, page_title)
                
        elif os_type == 'mac':
            # Pour Safari sur macOS
            if browser == "safari":
                script = '''
                tell application "Safari"
                    set currentTab to current tab of front window
                    set tabURL to URL of currentTab
                    set tabTitle to name of currentTab
                    return {tabURL, tabTitle}
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                if result.stdout:
                    parts = result.stdout.strip().split(', ')
                    url = parts[0] if parts and len(parts) > 0 else None
                    title = parts[1] if parts and len(parts) > 1 else None
                    return (url, title)
            
            # Pour Chrome sur macOS
            elif browser == "chrome":
                script = '''
                tell application "Google Chrome"
                    set currentTab to active tab of front window
                    set tabURL to URL of currentTab
                    set tabTitle to title of currentTab
                    return {tabURL, tabTitle}
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                if result.stdout:
                    parts = result.stdout.strip().split(', ')
                    url = parts[0] if parts and len(parts) > 0 else None
                    title = parts[1] if parts and len(parts) > 1 else None
                    return (url, title)
                    
            # Pour Firefox sur macOS
            elif browser == "firefox":
                # Firefox est plus difficile à automatiser avec AppleScript
                _, window_title, _ = get_active_application()
                page_title = window_title.split(" — ")[0] if " — " in window_title else window_title
                return (None, page_title)
                
        # Pour Linux, on peut seulement obtenir le titre de la fenêtre
        elif os_type == 'linux':
            _, window_title, _ = get_active_application()
            
            # Différents navigateurs utilisent différents séparateurs
            if " - " in window_title:  # Chrome, Edge
                page_title = window_title.split(" - ")[0]
            elif " — " in window_title:  # Firefox
                page_title = window_title.split(" — ")[0]
            else:
                page_title = window_title
                
            return (None, page_title)
            
        # Par défaut, retourner None, None
        return (None, None)
        
    except Exception as e:
        print(f"Erreur lors de la détection de l'onglet actif: {e}")
        return (None, None)

def detect_application_context():
    """
    Détecte le contexte de l'application active pour adapter les commandes
    
    Returns:
        dict: Informations sur le contexte de l'application
    """
    app_name, window_title, exe_path = get_active_application()
    
    context = {
        "app_name": app_name,
        "window_title": window_title,
        "exe_path": exe_path,
        "is_browser": False,
        "browser_name": None,
        "tab_url": None,
        "tab_title": None,
        "is_meet": False,
        "is_zoom": False,
        "is_teams": False,
        "is_office": False,
        "is_code_editor": False
    }
    
    # Vérifier si c'est un navigateur
    if is_browser_active():
        context["is_browser"] = True
        context["browser_name"] = get_active_browser()
        
        # Obtenir les informations sur l'onglet actif
        tab_url, tab_title = get_active_browser_tab_info()
        context["tab_url"] = tab_url
        context["tab_title"] = tab_title
        
        # Détecter les applications web courantes
        if window_title:
            window_title_lower = window_title.lower()
            
            # Google Meet
            if "meet.google.com" in window_title_lower or "google meet" in window_title_lower:
                context["is_meet"] = True
                
            # Zoom dans le navigateur
            elif "zoom" in window_title_lower and ("meeting" in window_title_lower or "réunion" in window_title_lower):
                context["is_zoom"] = True
                
            # Microsoft Teams dans le navigateur
            elif "teams" in window_title_lower and ("microsoft" in window_title_lower or "meeting" in window_title_lower):
                context["is_teams"] = True
    
    # Applications natives
    else:
        # Microsoft Office
        if any(app in app_name for app in ["word", "excel", "powerpoint", "outlook", "onenote"]):
            context["is_office"] = True
            
        # Éditeurs de code
        elif any(app in app_name for app in ["code", "vscode", "visualstudio", "pycharm", "intellij", 
                                           "eclipse", "atom", "sublime", "notepad++", "vim", "emacs"]):
            context["is_code_editor"] = True
            
        # Applications de visioconférence natives
        elif "zoom" in app_name:
            context["is_zoom"] = True
        elif "teams" in app_name:
            context["is_teams"] = True
    
    return context
