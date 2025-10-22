"""
Module de gestion des commandes clavier pour l'assistant Whisp
"""

import pyautogui
import time
import platform
from shortcuts_database import obtenir_raccourci
from os_detection import get_os_type, adapt_shortcut
from window_manager import detect_application_context
from text_processing import nettoyer_commande

def executer_commande_clavier(texte):
    """Exécute des commandes clavier en fonction du texte transcrit"""
    # Nettoyer le texte en enlevant le point final s'il existe
    texte_original = texte
    texte = nettoyer_commande(texte)
    
    # Afficher le texte reçu pour le débogage
    print(f"Commande clavier reçue: '{texte_original}' (nettoyée: '{texte}')")
    
    # Détecter le contexte de l'application active
    context = detect_application_context()
    app_name = context["app_name"]
    window_title = context["window_title"]
    
    print(f"Contexte détecté: Application={app_name}, Fenêtre={window_title}")
    if context["is_browser"]:
        print(f"Navigateur: {context['browser_name']}, Onglet: {context['tab_title']}")
    
    os_type = get_os_type()
    
    # ===== COMMANDES CLAVIER DIRECTES =====
    # Touches de base
    if any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["entrer", "entrée", "valider", "enter", "valide", 
                                   "appuie sur entrée", "appuyer sur entrée", "appuie sur entrer", 
                                   "appuyer sur entrer", "presse entrée", "presser entrée", 
                                   "presse entrer", "presser entrer", "touche entrée", 
                                   "touche entrer", "tape entrée", "taper entrée", 
                                   "tape entrer", "taper entrer", "confirme", "confirmer",
                                   "envoyer", "envoie", "envoyez", "envoyé"]):
        pyautogui.press('enter')
        return "Touche Entrée pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["espace", "space", "barre d'espace", "barre espace",
                                     "appuie sur espace", "appuyer sur espace", "presse espace", 
                                     "presser espace", "touche espace", "tape espace", "taper espace"]):
        pyautogui.press('space')
        return "Touche Espace pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["retour", "retour arrière", "backspace", "efface", "effacer",
                                     "supprime caractère", "supprimer caractère", "supprime le caractère", 
                                     "supprimer le caractère", "efface caractère", "effacer caractère",
                                     "efface le caractère", "effacer le caractère", "recule", "reculer",
                                     "appuie sur retour", "appuyer sur retour", "presse retour", "presser retour",
                                     "touche retour", "tape retour", "taper retour"]):
        pyautogui.press('backspace')
        return "Touche Retour arrière pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["supprimer", "supprime", "delete", "del", "efface devant", 
                                     "effacer devant", "supprime devant", "supprimer devant",
                                     "appuie sur supprimer", "appuyer sur supprimer", "presse supprimer", 
                                     "presser supprimer", "touche supprimer", "tape supprimer", 
                                     "taper supprimer", "touche delete", "touche del"]):
        pyautogui.press('delete')
        return "Touche Supprimer pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["échap", "escape", "échapper", "échappe", "esc",
                                     "appuie sur échap", "appuyer sur échap", "presse échap", 
                                     "presser échap", "touche échap", "tape échap", "taper échap",
                                     "annule", "annuler", "quitte", "quitter", "ferme", "fermer"]):
        pyautogui.press('escape')
        return "Touche Échap pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["tabulation", "tab", "indentation", "indenter", "indente",
                                     "appuie sur tab", "appuyer sur tab", "presse tab", "presser tab", 
                                     "touche tab", "tape tab", "taper tab", "appuie sur tabulation", 
                                     "appuyer sur tabulation", "presse tabulation", "presser tabulation", 
                                     "touche tabulation", "tape tabulation", "taper tabulation"]):
        pyautogui.press('tab')
        return "Touche Tabulation pressée"
    
    # Touches de navigation
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["haut", "flèche haut", "flèche vers le haut", "monte", "monter",
                                     "appuie sur flèche haut", "appuyer sur flèche haut", "presse flèche haut", 
                                     "presser flèche haut", "touche flèche haut", "tape flèche haut", 
                                     "taper flèche haut", "va vers le haut", "aller vers le haut",
                                     "déplace vers le haut", "déplacer vers le haut", "curseur vers le haut",
                                     "ligne précédente", "ligne du dessus"]):
        pyautogui.press('up')
        return "Flèche haut pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["bas", "flèche bas", "flèche vers le bas", "descend", "descendre",
                                     "appuie sur flèche bas", "appuyer sur flèche bas", "presse flèche bas", 
                                     "presser flèche bas", "touche flèche bas", "tape flèche bas", 
                                     "taper flèche bas", "va vers le bas", "aller vers le bas",
                                     "déplace vers le bas", "déplacer vers le bas", "curseur vers le bas",
                                     "ligne suivante", "ligne du dessous"]):
        pyautogui.press('down')
        return "Flèche bas pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["gauche", "flèche gauche", "flèche vers la gauche", "recule", "reculer",
                                     "appuie sur flèche gauche", "appuyer sur flèche gauche", "presse flèche gauche", 
                                     "presser flèche gauche", "touche flèche gauche", "tape flèche gauche", 
                                     "taper flèche gauche", "va vers la gauche", "aller vers la gauche",
                                     "déplace vers la gauche", "déplacer vers la gauche", "curseur vers la gauche",
                                     "caractère précédent", "caractère de gauche"]):
        pyautogui.press('left')
        return "Flèche gauche pressée"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["droite", "flèche droite", "flèche vers la droite", "avance", "avancer",
                                     "appuie sur flèche droite", "appuyer sur flèche droite", "presse flèche droite", 
                                     "presser flèche droite", "touche flèche droite", "tape flèche droite", 
                                     "taper flèche droite", "va vers la droite", "aller vers la droite",
                                     "déplace vers la droite", "déplacer vers la droite", "curseur vers la droite",
                                     "caractère suivant", "caractère de droite"]):
        pyautogui.press('right')
        return "Flèche droite pressée"
        
    elif texte == "début" or texte == "home":
        pyautogui.press('home')
        return "Touche Début pressée"
        
    elif texte == "fin" or texte == "end":
        pyautogui.press('end')
        return "Touche Fin pressée"
        
    elif texte == "page haut" or texte == "page up":
        pyautogui.press('pageup')
        return "Touche Page précédente pressée"
        
    elif texte == "page bas" or texte == "page down":
        pyautogui.press('pagedown')
        return "Touche Page suivante pressée"
    
    # Touches de fonction
    elif texte.startswith("f") and len(texte) <= 3:
        # Pour supporter F1 à F12
        try:
            num = int(texte[1:])
            if 1 <= num <= 12:
                pyautogui.press(f'f{num}')
                return f"Touche F{num} pressée"
        except ValueError:
            pass
    
    # Touches de modification adaptées à l'OS
    elif texte == "majuscule" or texte == "shift":
        # Appui temporaire sur Shift
        pyautogui.keyDown('shift')
        time.sleep(0.2)
        pyautogui.keyUp('shift')
        return "Touche Majuscule pressée brièvement"
        
    elif texte == "contrôle" or texte == "control" or texte == "ctrl":
        # Appui temporaire sur Ctrl/Command selon l'OS
        modifier = 'ctrl'
        if os_type == 'mac':
            modifier = 'command'
        pyautogui.keyDown(modifier)
        time.sleep(0.2)
        pyautogui.keyUp(modifier)
        return f"Touche {'Commande' if os_type == 'mac' else 'Contrôle'} pressée brièvement"
        
    elif texte == "alt" or (os_type == 'mac' and texte == "option"):
        # Appui temporaire sur Alt/Option selon l'OS
        modifier = 'alt' if os_type != 'mac' else 'option'
        pyautogui.keyDown(modifier)
        time.sleep(0.2)
        pyautogui.keyUp(modifier)
        return f"Touche {'Option' if os_type == 'mac' else 'Alt'} pressée brièvement"
        
    elif (os_type == 'mac' and texte == "commande") or texte == "windows" or texte == "win" or texte == "meta":
        # Appui temporaire sur Win/Command/Meta selon l'OS
        modifier = 'win'
        if os_type == 'mac':
            modifier = 'command'
        elif os_type == 'linux':
            modifier = 'meta'
        pyautogui.keyDown(modifier)
        time.sleep(0.2)
        pyautogui.keyUp(modifier)
        return f"Touche {'Commande' if os_type == 'mac' else 'Windows' if os_type == 'windows' else 'Meta'} pressée brièvement"
    
    # Combinaisons de touches courantes adaptées à l'OS
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["copier", "copie", "copy", "ctrl c", "control c", "cmd c", "command c",
                                     "copie le texte", "copier le texte", "copie la sélection", 
                                     "copier la sélection", "copie ça", "copier ça",
                                     "copie cette sélection", "copier cette sélection",
                                     "mets en mémoire", "mettre en mémoire", "place dans le presse-papier",
                                     "placer dans le presse-papier", "mémorise", "mémoriser"]):
        shortcut = obtenir_raccourci("global", "copier")
        pyautogui.hotkey(*shortcut)
        return f"Copier ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["coller", "colle", "paste", "ctrl v", "control v", "cmd v", "command v",
                                     "colle le texte", "coller le texte", "insère le texte", 
                                     "insérer le texte", "insère le contenu", "insérer le contenu",
                                     "insère le presse-papier", "insérer le presse-papier",
                                     "place le texte", "placer le texte", "mets le texte", 
                                     "mettre le texte", "insère", "insérer"]):
        shortcut = obtenir_raccourci("global", "coller")
        pyautogui.hotkey(*shortcut)
        return f"Coller ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["couper", "coupe", "cut", "ctrl x", "control x", "cmd x", "command x",
                                     "coupe le texte", "couper le texte", "coupe la sélection", 
                                     "couper la sélection", "coupe ça", "couper ça",
                                     "coupe cette sélection", "couper cette sélection",
                                     "déplace le texte", "déplacer le texte", "enlève et copie",
                                     "enlever et copier", "retire et copie", "retirer et copier"]):
        shortcut = obtenir_raccourci("global", "couper")
        pyautogui.hotkey(*shortcut)
        return f"Couper ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["sélectionner tout", "tout sélectionner", "sélectionne tout", 
                                     "tout sélectionne", "select all", "ctrl a", "control a", "cmd a", "command a",
                                     "sélectionne le tout", "sélectionner le tout", "sélectionne l'ensemble", 
                                     "sélectionner l'ensemble", "sélectionne la totalité", 
                                     "sélectionner la totalité", "sélectionne document", 
                                     "sélectionner document", "sélectionne texte entier", 
                                     "sélectionner texte entier", "sélectionnez tout", "tous sélectionnés"]):
        # Utiliser directement Ctrl+A ou Cmd+A au lieu de passer par la base de données de raccourcis
        # qui pourrait ne pas fonctionner correctement
        if get_os_type() == 'mac':
            pyautogui.hotkey('command', 'a')
            return "Tout sélectionner (Cmd+A)"
        else:
            pyautogui.hotkey('ctrl', 'a')
            return "Tout sélectionner (Ctrl+A)"
        
    elif texte == "annuler":
        shortcut = obtenir_raccourci("global", "annuler")
        pyautogui.hotkey(*shortcut)
        return f"Annuler ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif texte == "rétablir":
        shortcut = obtenir_raccourci("global", "rétablir")
        pyautogui.hotkey(*shortcut)
        return f"Rétablir ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif texte == "enregistrer":
        shortcut = obtenir_raccourci("global", "enregistrer")
        pyautogui.hotkey(*shortcut)
        return f"Enregistrer ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif texte == "imprimer":
        shortcut = obtenir_raccourci("global", "imprimer")
        pyautogui.hotkey(*shortcut)
        return f"Imprimer ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif texte == "rechercher":
        shortcut = obtenir_raccourci("global", "rechercher")
        pyautogui.hotkey(*shortcut)
        return f"Rechercher ({' + '.join(s.capitalize() for s in shortcut)})"
        
    elif texte == "nouvelle ligne":
        pyautogui.press('enter')
        return "Nouvelle ligne (Entrée)"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["onglet suivant", "tab suivant", "prochain onglet", 
                                     "onglet d'après", "onglet de droite", "change d'onglet", 
                                     "passe à l'onglet suivant", "va à l'onglet suivant"]):
        # Obtenir le raccourci adapté à l'OS
        if os_type == 'mac':
            # Sur Mac, souvent Cmd+Option+Flèche droite
            pyautogui.keyDown('command')
            pyautogui.keyDown('option')
            time.sleep(0.1)
            pyautogui.press('right')
            time.sleep(0.1)
            pyautogui.keyUp('option')
            pyautogui.keyUp('command')
            return "Onglet suivant (Cmd+Option+Flèche droite)"
        else:
            # Sur Windows/Linux, généralement Ctrl+Tab
            pyautogui.keyDown('ctrl')
            time.sleep(0.1)
            pyautogui.press('tab')
            time.sleep(0.1)
            pyautogui.keyUp('ctrl')
            return "Onglet suivant (Ctrl+Tab)"
        
    elif any(nettoyer_commande(cmd) == nettoyer_commande(texte) for cmd in ["onglet précédent", "tab précédent", "onglet d'avant", 
                                     "onglet de gauche", "retourne à l'onglet précédent", 
                                     "va à l'onglet précédent", "onglet précédent"]):
        # Obtenir le raccourci adapté à l'OS
        if os_type == 'mac':
            # Sur Mac, souvent Cmd+Option+Flèche gauche
            pyautogui.keyDown('command')
            pyautogui.keyDown('option')
            time.sleep(0.1)
            pyautogui.press('left')
            time.sleep(0.1)
            pyautogui.keyUp('option')
            pyautogui.keyUp('command')
            return "Onglet précédent (Cmd+Option+Flèche gauche)"
        else:
            # Sur Windows/Linux, généralement Ctrl+Shift+Tab
            pyautogui.keyDown('ctrl')
            pyautogui.keyDown('shift')
            time.sleep(0.1)
            pyautogui.press('tab')
            time.sleep(0.1)
            pyautogui.keyUp('shift')
            pyautogui.keyUp('ctrl')
            return "Onglet précédent (Ctrl+Maj+Tab)"
            
    # Commandes pour les applications de visioconférence (Google Meet, Zoom, Teams)
    elif any(cmd in texte for cmd in ["micro", "couper le son", "activer le son", "désactiver le son", 
                                     "couper micro", "activer micro", "désactiver micro", 
                                     "couper le micro", "activer le micro", "désactiver le micro",
                                     "mute", "unmute", "muet", "activer le microphone", "désactiver le microphone"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "activer/désactiver micro")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Micro {'désactivé' if 'couper' in texte or 'désactiver' in texte else 'activé'} dans {app}"
        else:
            return f"Raccourci pour le micro non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["caméra", "couper la vidéo", "activer la vidéo", "désactiver la vidéo", 
                                     "couper caméra", "activer caméra", "désactiver caméra", 
                                     "couper la caméra", "activer la caméra", "désactiver la caméra",
                                     "vidéo off", "vidéo on", "activer la webcam", "désactiver la webcam"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "activer/désactiver caméra")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Caméra {'désactivée' if 'couper' in texte or 'désactiver' in texte else 'activée'} dans {app}"
        else:
            return f"Raccourci pour la caméra non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["lever la main", "lève la main", "main levée", 
                                     "lever main", "lève main", "raise hand"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "lever la main")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Main levée dans {app}"
        else:
            return f"Raccourci pour lever la main non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["partager écran", "partage écran", "partager mon écran", 
                                     "partage d'écran", "partager l'écran", "share screen"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "partager écran")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Partage d'écran dans {app}"
        else:
            return f"Raccourci pour partager l'écran non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["afficher participants", "voir participants", "liste participants", 
                                     "montrer participants", "afficher les participants", 
                                     "voir les participants", "montrer les participants"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "afficher participants")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Participants affichés dans {app}"
        else:
            return f"Raccourci pour afficher les participants non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["afficher conversation", "voir conversation", "ouvrir conversation", 
                                     "montrer conversation", "afficher le chat", "voir le chat", 
                                     "ouvrir le chat", "montrer le chat", "afficher tchat", 
                                     "voir tchat", "ouvrir tchat", "montrer tchat"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "afficher conversation")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Conversation affichée dans {app}"
        else:
            return f"Raccourci pour afficher la conversation non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["quitter réunion", "quitter la réunion", "sortir de la réunion", 
                                     "terminer réunion", "terminer la réunion", "fin de réunion", 
                                     "fin réunion", "raccrocher", "end meeting", "leave meeting"]):
        # Détecter l'application de visioconférence en fonction du contexte
        app = None
        
        # Vérifier d'abord le contexte de l'application active
        if context["is_meet"]:
            app = "google meet"
        elif context["is_zoom"]:
            app = "zoom"
        elif context["is_teams"]:
            app = "teams"
        # Si aucune application de visioconférence n'est détectée dans le contexte,
        # utiliser les mots-clés dans la commande
        elif "zoom" in texte:
            app = "zoom"
        elif "teams" in texte or "team" in texte:
            app = "teams"
        elif "meet" in texte or "google" in texte:
            app = "google meet"
        else:
            # Par défaut, utiliser Google Meet
            app = "google meet"
            
        shortcut = obtenir_raccourci(app, "quitter réunion")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Réunion quittée dans {app}"
        else:
            return f"Raccourci pour quitter la réunion non trouvé pour {app}"
    
    # Commande pour aller à un onglet spécifique par numéro
    elif texte.startswith("onglet numéro ") or texte.startswith("tab numéro "):
        # Extraire le numéro de l'onglet
        try:
            # Récupérer le dernier mot qui devrait être le numéro
            numero = texte.split()[-1]
            # Convertir en entier
            numero_onglet = int(numero)
            
            # Vérifier que le numéro est entre 1 et 9
            if 1 <= numero_onglet <= 9:
                # Adapter le raccourci en fonction de l'OS
                if os_type == 'mac':
                    modifier = 'command'
                else:
                    modifier = 'ctrl'
                
                # Méthode alternative plus fiable pour les raccourcis Ctrl/Cmd+numéro
                # Simuler l'appui direct sur les touches avec un délai plus long
                pyautogui.keyDown(modifier)
                time.sleep(0.3)  # Délai plus long pour s'assurer que la touche est bien détectée
                
                # Utiliser write au lieu de press pour le numéro
                pyautogui.write(str(numero_onglet))
                
                time.sleep(0.3)  # Délai plus long avant de relâcher
                pyautogui.keyUp(modifier)
                
                # Petit délai supplémentaire pour laisser le temps au système de traiter
                time.sleep(0.2)
                
                modifier_name = 'Cmd' if os_type == 'mac' else 'Ctrl'
                return f"Onglet numéro {numero_onglet} ({modifier_name}+{numero_onglet})"
            else:
                return "Numéro d'onglet non valide (doit être entre 1 et 9)"
        except ValueError:
            return "Numéro d'onglet non reconnu"
    
    # Ponctuation et caractères spéciaux
    elif texte == "point":
        pyautogui.press('.')
        return "Point (.)"
        
    elif texte == "virgule":
        pyautogui.press(',')
        return "Virgule (,)"
        
    elif texte == "point d'interrogation":
        # Pour le point d'interrogation, souvent nécessite shift+?
        pyautogui.write('?')
        return "Point d'interrogation (?)"
        
    elif texte == "point d'exclamation":
        pyautogui.write('!')
        return "Point d'exclamation (!)"
        
    elif texte == "tiret":
        pyautogui.press('-')
        return "Tiret (-)"
        
    elif texte == "tiret du bas" or texte == "underscore":
        pyautogui.write('_')
        return "Tiret du bas (_)"
        
    elif texte == "parenthèse ouverte":
        pyautogui.write('(')
        return "Parenthèse ouverte"
        
    elif texte == "parenthèse fermée":
        pyautogui.write(')')
        return "Parenthèse fermée"
    
    elif "appuie sur entrée" in texte or "appuie sur entrer" in texte:
        pyautogui.press('enter')
        return "Touche Entrée pressée"
        
    elif "appuie sur espace" in texte:
        pyautogui.press('space')
        return "Touche Espace pressée"
        
    elif "appuie sur échap" in texte:
        pyautogui.press('escape')
        return "Touche Échap pressée"
        
    elif "touche" in texte and "flèche" in texte:
        if "haut" in texte:
            pyautogui.press('up')
            return "Flèche haut pressée"
        elif "bas" in texte:
            pyautogui.press('down')
            return "Flèche bas pressée"
        elif "gauche" in texte:
            pyautogui.press('left')
            return "Flèche gauche pressée"
        elif "droite" in texte:
            pyautogui.press('right')
            return "Flèche droite pressée"
    
    # Commandes spécifiques à Google Meet
    elif any(cmd in texte for cmd in ["activer sous-titres", "afficher sous-titres", "sous-titres on", 
                                     "activer les sous-titres", "afficher les sous-titres"]):
        # Vérifier si Google Meet est actif
        app = "google meet"
        if not context["is_meet"] and not "meet" in texte and not "google" in texte:
            return "Cette commande fonctionne uniquement dans Google Meet. Veuillez d'abord ouvrir Google Meet."
            
        shortcut = obtenir_raccourci(app, "activer sous-titres")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Sous-titres activés dans {app}"
        else:
            return f"Raccourci pour activer les sous-titres non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["désactiver sous-titres", "masquer sous-titres", "sous-titres off", 
                                     "désactiver les sous-titres", "masquer les sous-titres"]):
        # Vérifier si Google Meet est actif
        app = "google meet"
        if not context["is_meet"] and not "meet" in texte and not "google" in texte:
            return "Cette commande fonctionne uniquement dans Google Meet. Veuillez d'abord ouvrir Google Meet."
            
        shortcut = obtenir_raccourci(app, "activer sous-titres")  # Même raccourci pour activer/désactiver
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Sous-titres désactivés dans {app}"
        else:
            return f"Raccourci pour désactiver les sous-titres non trouvé pour {app}"
            
    elif any(cmd in texte for cmd in ["épingler participant", "épingler vidéo", "épingler", 
                                     "détacher participant", "détacher vidéo", "détacher"]):
        # Vérifier si Google Meet est actif
        app = "google meet"
        if not context["is_meet"] and not "meet" in texte and not "google" in texte:
            return "Cette commande fonctionne uniquement dans Google Meet. Veuillez d'abord ouvrir Google Meet."
            
        shortcut = obtenir_raccourci(app, "épingler/détacher")
        if shortcut:
            pyautogui.hotkey(*shortcut)
            return f"Participant épinglé/détaché dans {app}"
        else:
            return f"Raccourci pour épingler/détacher non trouvé pour {app}"
    
    # ===== COMMANDES AVANCÉES AVEC LA BASE DE DONNÉES DE RACCOURCIS =====
    elif "raccourci" in texte:
        # Format attendu: "raccourci [application] [commande]"
        # Exemple: "raccourci word gras" ou "raccourci excel somme automatique"
        parties = texte.split("raccourci", 1)[1].strip().split(" ", 1)
        
        if len(parties) >= 2:
            application = parties[0].strip()
            commande = parties[1].strip()
            
            # Si l'application n'est pas spécifiée explicitement, essayer de la détecter
            if application == "cette" or application == "l'" or application == "l'application" or application == "ici":
                # Utiliser l'application détectée
                if context["is_browser"]:
                    if context["is_meet"]:
                        application = "google meet"
                    elif context["is_zoom"]:
                        application = "zoom"
                    elif context["is_teams"]:
                        application = "teams"
                    else:
                        application = context["browser_name"] if context["browser_name"] else "navigateur"
                elif context["is_office"]:
                    # Détecter quelle application Office
                    if "word" in app_name:
                        application = "word"
                    elif "excel" in app_name:
                        application = "excel"
                    elif "powerpoint" in app_name:
                        application = "powerpoint"
                    elif "outlook" in app_name:
                        application = "outlook"
                    else:
                        application = "office"
                elif context["is_code_editor"]:
                    if "code" in app_name or "vscode" in app_name:
                        application = "vscode"
                    else:
                        application = "éditeur"
                else:
                    application = app_name
            
            raccourci = obtenir_raccourci(application, commande)
            if raccourci:
                if isinstance(raccourci, tuple):
                    pyautogui.hotkey(*raccourci)
                    return f"Raccourci '{commande}' exécuté pour {application} ({' + '.join(s.capitalize() for s in raccourci)})"
                else:
                    pyautogui.press(raccourci)
                    return f"Raccourci '{commande}' exécuté pour {application} ({raccourci.capitalize()})"
            else:
                return f"Raccourci non trouvé pour '{commande}' dans {application} sur {os_type.capitalize()}"
        else:
            return "Format incorrect. Utilisez: raccourci [application] [commande]"
    
    return None  # Commande non reconnue
