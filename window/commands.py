"""Dispatcher principal des commandes de gestion de fenêtres."""

from window._common import *  # noqa: F401,F403  (imports partagés + error_handler + SITES_POPULAIRES)
from window.enumeration import obtenir_applications_ouvertes, obtenir_fenetres_ouvertes
from window.focus import basculer_vers_fenetre
from window.monitors import get_monitor_count, deplacer_fenetre_vers_ecran

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
            except (AttributeError, OSError, pyautogui.FailSafeException) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Error maximizing window on macOS: {e}", ErrorSeverity.LOW)
            
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
