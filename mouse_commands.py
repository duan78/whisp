"""
Module de gestion des commandes souris pour l'assistant Whisp
"""

import pyautogui
import time
import re
from screen_context import localiser_element_ecran, localiser_element_par_attributs
from os_detection import get_os_type, is_windows, is_mac, is_linux

# Importation conditionnelle de mouse selon l'OS
try:
    import mouse
except ImportError:
    # Créer un substitut pour mouse si non disponible
    class MouseSubstitute:
        def click(self, button='left'):
            if button == 'left':
                pyautogui.click()
            elif button == 'right':
                pyautogui.rightClick()
                
        def double_click(self, button='left'):
            if button == 'left':
                pyautogui.doubleClick()
            
        def press(self, button='left'):
            if button == 'left':
                pyautogui.mouseDown()
            elif button == 'right':
                pyautogui.mouseDown(button='right')
            
        def release(self, button='left'):
            if button == 'left':
                pyautogui.mouseUp()
            elif button == 'right':
                pyautogui.mouseUp(button='right')
                
        def get_position(self):
            return pyautogui.position()
    
    mouse = MouseSubstitute()

def executer_commande_souris(texte):
    """Exécute des commandes souris en fonction du texte transcrit"""
    texte = texte.lower()
    os_type = get_os_type()
    
    # ===== COMMANDES DE LOCALISATION ET CLIC SUR ÉLÉMENTS =====
    # Patterns pour détecter les commandes de clic sur des éléments
    patterns_clic_element = [
        r"^clique sur (?:le |la |l'|les )?(.*)",
        r"^clic sur (?:le |la |l'|les )?(.*)",
        r"^clique (?:le |la |l'|les )?(.*)",
        r"^cliquer sur (?:le |la |l'|les )?(.*)",
        r"^appuie sur (?:le |la |l'|les )?(.*)",
        r"^appuyer sur (?:le |la |l'|les )?(.*)",
        r"^sélectionne (?:le |la |l'|les )?(.*)",
        r"^sélectionner (?:le |la |l'|les )?(.*)",
        r"^va sur (?:le |la |l'|les )?(.*)",
        r"^aller sur (?:le |la |l'|les )?(.*)"
    ]
    
    # Vérifier si la commande correspond à un clic sur un élément
    for pattern in patterns_clic_element:
        match = re.search(pattern, texte)
        if match:
            element_description = match.group(1).strip()
            if element_description:
                # Détection améliorée des formes et couleurs
                if any(forme in element_description for forme in ["bouton", "carré", "rectangle", "triangle", "cercle"]) or \
                   any(couleur in element_description for couleur in ["rouge", "bleu", "vert", "jaune", "orange", "violet", "noir", "blanc"]):
                    return cliquer_sur_element_visuel(element_description)
                else:
                    return cliquer_sur_element(element_description)
    
    # Patterns pour détecter les commandes de déplacement sur des éléments
    patterns_deplacer_element = [
        r"déplace (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"déplacer (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"positionne (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"positionner (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"place (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"placer (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"mets (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"mettre (?:la )?souris sur (?:le |la |l'|les )?(.*)",
        r"souris sur (?:le |la |l'|les )?(.*)"
    ]
    
    # Vérifier si la commande correspond à un déplacement sur un élément
    for pattern in patterns_deplacer_element:
        match = re.search(pattern, texte)
        if match:
            element_description = match.group(1).strip()
            if element_description:
                # Détection améliorée des formes et couleurs
                if any(forme in element_description for forme in ["bouton", "carré", "rectangle", "triangle", "cercle"]) or \
                   any(couleur in element_description for couleur in ["rouge", "bleu", "vert", "jaune", "orange", "violet", "noir", "blanc"]):
                    return deplacer_souris_sur_element_visuel(element_description)
                else:
                    return deplacer_souris_sur_element(element_description)
    
    # ===== CONTRÔLE AVANCÉ DE LA SOURIS =====
    if any(cmd in texte for cmd in ["souris en haut à gauche", "déplace souris en haut à gauche", 
                                   "déplacer souris en haut à gauche", "curseur en haut à gauche", 
                                   "déplace curseur en haut à gauche", "déplacer curseur en haut à gauche",
                                   "souris coin supérieur gauche", "curseur coin supérieur gauche",
                                   "place souris en haut à gauche", "placer souris en haut à gauche",
                                   "mets souris en haut à gauche", "mettre souris en haut à gauche",
                                   "va en haut à gauche", "aller en haut à gauche"]):
        pyautogui.moveTo(10, 10)
        return "Souris déplacée en haut à gauche"
        
    elif "souris en haut à droite" in texte:
        width, height = pyautogui.size()
        pyautogui.moveTo(width-10, 10)
        return "Souris déplacée en haut à droite"
        
    elif "souris en bas à gauche" in texte:
        width, height = pyautogui.size()
        pyautogui.moveTo(10, height-10)
        return "Souris déplacée en bas à gauche"
        
    elif "souris en bas à droite" in texte:
        width, height = pyautogui.size()
        pyautogui.moveTo(width-10, height-10)
        return "Souris déplacée en bas à droite"
        
    elif "souris au centre" in texte:
        width, height = pyautogui.size()
        pyautogui.moveTo(width/2, height/2)
        return "Souris déplacée au centre"
    
    elif "déplace souris" in texte:
        # Extraction des coordonnées si spécifiées
        try:
            # Tentative d'extraire des nombres pour les coordonnées
            coords = [int(s) for s in texte.split() if s.isdigit()]
            if len(coords) >= 2:
                pyautogui.moveTo(coords[0], coords[1])
                return f"Souris déplacée aux coordonnées {coords[0]}, {coords[1]}"
            else:
                return "Coordonnées non spécifiées pour le déplacement de la souris"
        except:
            return "Erreur lors du déplacement de la souris"
    
    elif "souris vers la gauche" in texte:
        x, y = pyautogui.position()
        pyautogui.moveTo(x-100, y, duration=0.2)
        return "Souris déplacée vers la gauche"
        
    elif "souris vers la droite" in texte:
        x, y = pyautogui.position()
        pyautogui.moveTo(x+100, y, duration=0.2)
        return "Souris déplacée vers la droite"
        
    elif "souris vers le haut" in texte:
        x, y = pyautogui.position()
        pyautogui.moveTo(x, y-100, duration=0.2)
        return "Souris déplacée vers le haut"
        
    elif "souris vers le bas" in texte:
        x, y = pyautogui.position()
        pyautogui.moveTo(x, y+100, duration=0.2)
        return "Souris déplacée vers le bas"
    
    elif any(cmd in texte for cmd in ["clic gauche", "clique gauche", "clic", "clique", "click", 
                                     "appuie", "appuyer", "clique à gauche", "cliquer à gauche",
                                     "fais un clic", "faire un clic", "fais un clic gauche", 
                                     "faire un clic gauche", "clic simple", "clique simple",
                                     "clic normal", "clique normal", "appuie sur le bouton gauche",
                                     "appuyer sur le bouton gauche", "presse le bouton gauche",
                                     "presser le bouton gauche", "tape un clic", "taper un clic"]):
        mouse.click('left')
        return "Clic gauche effectué"
        
    elif any(cmd in texte for cmd in ["clic droit", "clique droit", "click droit", "clique à droite", 
                                     "cliquer à droite", "fais un clic droit", "faire un clic droit",
                                     "menu contextuel", "ouvre menu contextuel", "ouvrir menu contextuel",
                                     "affiche menu contextuel", "afficher menu contextuel",
                                     "appuie sur le bouton droit", "appuyer sur le bouton droit",
                                     "presse le bouton droit", "presser le bouton droit",
                                     "clic bouton droit", "clique bouton droit"]):
        mouse.click('right')
        return "Clic droit effectué"
        
    elif any(cmd in texte for cmd in ["double clic", "double clique", "double click", "double-clic", 
                                     "double-clique", "double-click", "clique deux fois", "cliquer deux fois",
                                     "fais un double clic", "faire un double clic", "double tape",
                                     "double frappe", "clique double", "cliquer double",
                                     "double clic gauche", "double clique gauche", "double click gauche"]):
        mouse.double_click('left')
        return "Double clic effectué"
        
    elif "maintiens clic" in texte or "appuie souris" in texte:
        mouse.press('left')
        return "Bouton gauche maintenu"
        
    elif "relâche clic" in texte or "relâche souris" in texte:
        mouse.release('left')
        return "Bouton gauche relâché"
    
    elif "glisse jusqu'à" in texte:
        try:
            coords = [int(s) for s in texte.split() if s.isdigit()]
            if len(coords) >= 2:
                current_x, current_y = pyautogui.position()
                mouse.press('left')
                pyautogui.moveTo(coords[0], coords[1], duration=0.5)
                mouse.release('left')
                return f"Glisser-déposer de ({current_x},{current_y}) à ({coords[0]},{coords[1]})"
            else:
                return "Coordonnées non spécifiées pour le glisser-déposer"
        except:
            return "Erreur lors du glisser-déposer"
    
    elif any(cmd in texte for cmd in ["défile vers le bas", "défiler vers le bas", "défilé vers le bas", 
                                     "défilé bas", "défiler bas", "défile bas", "scroll vers le bas", 
                                     "scrolle vers le bas", "scroll down", "scrolle down", "défile en bas",
                                     "défiler en bas", "descends la page", "descendre la page",
                                     "fais défiler vers le bas", "faire défiler vers le bas",
                                     "va plus bas", "aller plus bas", "descends", "descendre",
                                     "page vers le bas", "molette vers le bas", "page down",
                                     "bas de page", "vers le bas", "en bas", "défiler en bas",
                                     "défilé en bas", "défilement bas", "défilement vers le bas"]):
        pyautogui.scroll(-10)
        return "Défilement vers le bas"
        
    elif "défile beaucoup vers le bas" in texte:
        pyautogui.scroll(-50)
        return "Défilement important vers le bas"
        
    elif any(cmd in texte for cmd in ["défile vers le haut", "défiler vers le haut", "défilé vers le haut", 
                                     "défilé haut", "défiler haut", "défile haut", "scroll vers le haut", 
                                     "scrolle vers le haut", "scroll up", "scrolle up", "défile en haut",
                                     "défiler en haut", "monte la page", "monter la page",
                                     "fais défiler vers le haut", "faire défiler vers le haut",
                                     "va plus haut", "aller plus haut", "monte", "monter",
                                     "page vers le haut", "molette vers le haut", "page up",
                                     "haut de page", "vers le haut", "en haut", "défiler en haut",
                                     "défilé en haut", "défilement haut", "défilement vers le haut"]):
        pyautogui.scroll(10)
        return "Défilement vers le haut"
        
    elif "défile beaucoup vers le haut" in texte:
        pyautogui.scroll(50)
        return "Défilement important vers le haut"
    
    elif "quelle est ma position souris" in texte:
        x, y = mouse.get_position()
        return f"Position actuelle de la souris : x={x}, y={y}"
    
    return None  # Commande non reconnue

def deplacer_souris_sur_element_visuel(element_description):
    """
    Déplace la souris sur un élément visuel identifié par ses attributs (forme, couleur)
    """
    print(f"Recherche de l'élément visuel: {element_description}")
    
    # Utiliser la fonction spécialisée de localisation d'élément par attributs
    coordonnees = localiser_element_par_attributs(element_description)
    
    if coordonnees:
        x, y = coordonnees
        # Vérifier si les coordonnées semblent raisonnables
        screen_width, screen_height = pyautogui.size()
        if x <= 0 or x >= screen_width or y <= 0 or y >= screen_height:
            print(f"Coordonnées invalides: ({x}, {y})")
            from tts_module import ajouter_texte_a_lire
            ajouter_texte_a_lire(f"Coordonnées invalides pour {element_description}")
            return f"Coordonnées invalides pour {element_description}"
            
        # Déplacer la souris directement vers les coordonnées avec une animation fluide
        pyautogui.moveTo(x, y, duration=0.05)
        
        # Feedback vocal
        from tts_module import ajouter_texte_a_lire
        ajouter_texte_a_lire(f"Souris déplacée sur {element_description}")
        return f"Souris déplacée sur {element_description} aux coordonnées ({x}, {y})"
    
    from tts_module import ajouter_texte_a_lire
    ajouter_texte_a_lire(f"Impossible de trouver {element_description}")
    return f"Impossible de trouver l'élément visuel: {element_description}"

def deplacer_souris_sur_element(element_description):
    """
    Déplace la souris sur un élément identifié par sa description
    """
    print(f"Recherche de l'élément: {element_description}")
    
    # Utiliser la fonction de localisation d'élément (OCR ou OpenCV)
    coordonnees = localiser_element_ecran(element_description)
    
    if coordonnees:
        x, y = coordonnees
        # Vérifier si les coordonnées semblent raisonnables
        screen_width, screen_height = pyautogui.size()
        if x <= 0 or x >= screen_width or y <= 0 or y >= screen_height:
            print(f"Coordonnées invalides: ({x}, {y})")
            return f"Coordonnées invalides pour {element_description}"
            
        # Déplacer la souris directement vers les coordonnées sans animation (plus rapide)
        pyautogui.moveTo(x, y, duration=0)
            
        # Feedback vocal
        from tts_module import ajouter_texte_a_lire
        ajouter_texte_a_lire(f"Souris déplacée sur {element_description}")
        return f"Souris déplacée sur {element_description} aux coordonnées ({x}, {y})"
    else:
        # Si la localisation échoue, essayer de trouver un élément interactif avec la détection avancée
        try:
            # Capturer l'écran
            screenshot = pyautogui.screenshot()
            
            # Utiliser la fonction de détection d'éléments interactifs
            from screen_context import detecter_elements_interactifs
            elements = detecter_elements_interactifs(screenshot)
            
            if elements:
                # Obtenir les dimensions de l'écran
                screen_width, screen_height = pyautogui.size()
                screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
                
                # Calculer un score pour chaque élément basé sur sa taille, sa position et son score initial
                scored_elements = []
                for x, y, w, h, score in elements:
                    # Distance au centre de l'écran
                    distance = ((x - screen_center_x) ** 2 + (y - screen_center_y) ** 2) ** 0.5
                    # Normaliser la distance
                    normalized_distance = distance / ((screen_width ** 2 + screen_height ** 2) ** 0.5)
                    # Taille de l'élément (préférer les éléments plus grands)
                    size_factor = min(1.0, (w * h) / 10000)
                    # Score final
                    final_score = score * (1 - normalized_distance * 0.5) * (0.5 + size_factor * 0.5)
                    scored_elements.append((x, y, w, h, final_score))
                
                # Sélectionner l'élément avec le meilleur score
                best_element = max(scored_elements, key=lambda e: e[4])
                cX, cY = best_element[0], best_element[1]
                
                # Déplacer la souris vers le centre de l'élément
                pyautogui.moveTo(cX, cY, duration=0.05)
                
                from tts_module import ajouter_texte_a_lire
                ajouter_texte_a_lire(f"Souris déplacée sur un élément interactif")
                return f"Souris déplacée sur un élément interactif aux coordonnées ({cX}, {cY})"
        except Exception as e:
            print(f"Erreur lors de la recherche visuelle: {e}")
        
        from tts_module import ajouter_texte_a_lire
        ajouter_texte_a_lire(f"Impossible de trouver {element_description}")
        return f"Impossible de trouver l'élément: {element_description}"

def cliquer_sur_element_visuel(element_description):
    """
    Clique sur un élément visuel (forme ou couleur spécifique)
    """
    print(f"Recherche et clic sur l'élément visuel: {element_description}")
    
    # Vérifier si la description est vide ou trop courte
    if not element_description or len(element_description) < 2:
        from tts_module import ajouter_texte_a_lire
        ajouter_texte_a_lire("Description de l'élément trop courte ou vide")
        return "Description de l'élément trop courte ou vide"
    
    # Utiliser la fonction de localisation d'élément par attributs visuels
    coordonnees = localiser_element_par_attributs(element_description)
    
    if coordonnees:
        x, y = coordonnees
        
        # Vérifier si les coordonnées semblent raisonnables
        screen_width, screen_height = pyautogui.size()
        if x <= 0 or x >= screen_width or y <= 0 or y >= screen_height:
            print(f"Coordonnées invalides: ({x}, {y})")
            from tts_module import ajouter_texte_a_lire
            ajouter_texte_a_lire(f"Coordonnées invalides pour {element_description}")
            return f"Coordonnées invalides pour {element_description}"
            
        # Déplacer la souris directement vers les coordonnées sans animation
        pyautogui.moveTo(x, y, duration=0)
            
        # Effectuer un clic immédiatement
        mouse.click('left')
            
        # Préparer et jouer le feedback après le clic
        from tts_module import preparer_feedback_court, jouer_feedback_court
        message_feedback = f"Clic effectué sur {element_description}"
        preparer_feedback_court(message_feedback)
        jouer_feedback_court()
        
        return f"Clic effectué sur {element_description} aux coordonnées ({x}, {y})"
    
    from tts_module import ajouter_texte_a_lire
    ajouter_texte_a_lire(f"Impossible de trouver {element_description}")
    return f"Impossible de trouver l'élément visuel: {element_description}"

def cliquer_sur_element(element_description):
    """
    Clique sur un élément identifié par sa description
    """
    print(f"Recherche et clic sur l'élément: {element_description}")
    
    # Vérifier si la description est vide ou trop courte
    if not element_description or len(element_description) < 2:
        from tts_module import ajouter_texte_a_lire
        ajouter_texte_a_lire("Description de l'élément trop courte ou vide")
        return "Description de l'élément trop courte ou vide"
    
    # Essayer plusieurs approches pour trouver l'élément
    tentatives = [
        # 1. Description exacte
        element_description,
        # 2. Mots clés de la description
        ' '.join([mot for mot in element_description.split() if len(mot) > 3]),
        # 3. Premier mot significatif
        next((mot for mot in element_description.split() if len(mot) > 3), element_description.split()[0] if element_description.split() else element_description)
    ]
    
    for i, description in enumerate(tentatives):
        if i > 0 and description == tentatives[i-1] or not description:
            continue
            
        print(f"Tentative {i+1} avec: '{description}'")
        coordonnees = localiser_element_ecran(description)
        
        if coordonnees:
            x, y = coordonnees
            
            # Vérifier si les coordonnées semblent raisonnables
            screen_width, screen_height = pyautogui.size()
            if x <= 0 or x >= screen_width or y <= 0 or y >= screen_height:
                print(f"Coordonnées invalides: ({x}, {y})")
                continue
                
            # Déplacer la souris directement vers les coordonnées sans animation
            pyautogui.moveTo(x, y, duration=0)
                
            # Effectuer un clic immédiatement
            mouse.click('left')
                
            # Préparer et jouer le feedback après le clic
            from tts_module import preparer_feedback_court, jouer_feedback_court
            message_feedback = f"Clic effectué sur {element_description}"
            preparer_feedback_court(message_feedback)
            jouer_feedback_court()
            
            return f"Clic effectué sur {element_description} aux coordonnées ({x}, {y})"
    
    # Si toutes les tentatives échouent, essayer une recherche visuelle avancée
    try:
        # Capturer l'écran
        screenshot = pyautogui.screenshot()
        
        # Utiliser la fonction de détection d'éléments interactifs
        from screen_context import detecter_elements_interactifs
        elements = detecter_elements_interactifs(screenshot)
        
        if elements:
            # Trier les éléments par score (du plus élevé au plus faible)
            elements.sort(key=lambda e: e[4], reverse=True)
            
            # Obtenir les dimensions de l'écran
            screen_width, screen_height = pyautogui.size()
            screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
            
            # Calculer les distances au centre de l'écran
            elements_with_distance = []
            for x, y, w, h, score in elements:
                distance = ((x - screen_center_x) ** 2 + (y - screen_center_y) ** 2) ** 0.5
                # Normaliser la distance par rapport à la diagonale de l'écran
                normalized_distance = distance / ((screen_width ** 2 + screen_height ** 2) ** 0.5)
                # Calculer un score combiné (préférer les éléments avec un score élevé et proches du centre)
                combined_score = score * (1 - normalized_distance * 0.5)
                elements_with_distance.append((x, y, w, h, combined_score))
            
            # Sélectionner l'élément avec le meilleur score combiné
            best_element = max(elements_with_distance, key=lambda e: e[4])
            cX, cY = best_element[0], best_element[1]
            
            # Déplacer la souris directement vers les coordonnées sans animation
            pyautogui.moveTo(cX, cY, duration=0)
            
            # Effectuer un clic immédiatement
            mouse.click('left')
            
            # Préparer et jouer le feedback après le clic
            from tts_module import preparer_feedback_court, jouer_feedback_court
            preparer_feedback_court(f"Tentative de clic sur un élément interactif")
            jouer_feedback_court()
            
            return f"Tentative de clic sur un élément interactif aux coordonnées ({cX}, {cY})"
    except Exception as e:
        print(f"Erreur lors de la recherche visuelle: {e}")
    
    from tts_module import ajouter_texte_a_lire
    ajouter_texte_a_lire(f"Impossible de trouver {element_description}")
    return f"Impossible de trouver l'élément: {element_description}"
