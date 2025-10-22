"""
Module de commandes de productivité pour l'assistant Whisp
"""

import pyautogui
import subprocess
import os
import time
import pyperclip
import json
import re
import webbrowser
from datetime import datetime
import ctypes
from ctypes import wintypes

# Fonctions pour la gestion multiécran
def get_window_title():
    """Obtient le titre de la fenêtre active"""
    try:
        user32 = ctypes.WinDLL('user32')
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except:
        return "Fenêtre inconnue"

def organiser_fenetres_multiscreen():
    """Organise les fenêtres sur plusieurs écrans de manière optimale"""
    try:
        # Obtenir le nombre d'écrans
        user32 = ctypes.WinDLL('user32')
        SM_CMONITORS = 80
        nb_ecrans = user32.GetSystemMetrics(SM_CMONITORS)
        
        if nb_ecrans < 2:
            return "Un seul écran détecté, impossible d'organiser en multiécran"
        
        # Obtenir la liste des fenêtres ouvertes
        result = subprocess.run(["tasklist", "/FI", "SESSIONNAME eq Console", "/FO", "CSV"], 
                               capture_output=True, text=True, encoding='cp850')
        
        # Simuler l'organisation des fenêtres
        # Écran 1: Maximiser la fenêtre active
        pyautogui.hotkey('win', 'up')
        time.sleep(0.5)
        
        # Écran 2: Déplacer la fenêtre suivante
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.5)
        
        # Déplacer vers le second écran
        pyautogui.hotkey('win', 'shift', 'right')
        time.sleep(0.5)
        pyautogui.hotkey('win', 'up')  # Maximiser sur le second écran
        
        return f"Fenêtres organisées sur {nb_ecrans} écrans"
    except Exception as e:
        return f"Erreur lors de l'organisation des fenêtres: {str(e)}"

def executer_commande_productivite(texte):
    """Exécute des commandes de productivité en fonction du texte transcrit"""
    texte = texte.lower()
    
    # ===== GESTION DES APPLICATIONS DE PRODUCTIVITÉ =====
    if "ouvre word" in texte or "lance word" in texte:
        try:
            subprocess.Popen(["start", "winword"], shell=True)
            return "Microsoft Word ouvert"
        except:
            return "Impossible d'ouvrir Microsoft Word"
            
    elif "ouvre excel" in texte or "lance excel" in texte:
        try:
            subprocess.Popen(["start", "excel"], shell=True)
            return "Microsoft Excel ouvert"
        except:
            return "Impossible d'ouvrir Microsoft Excel"
            
    elif "ouvre powerpoint" in texte or "lance powerpoint" in texte:
        try:
            subprocess.Popen(["start", "powerpnt"], shell=True)
            return "Microsoft PowerPoint ouvert"
        except:
            return "Impossible d'ouvrir Microsoft PowerPoint"
            
    elif "ouvre outlook" in texte or "lance outlook" in texte:
        try:
            subprocess.Popen(["start", "outlook"], shell=True)
            return "Microsoft Outlook ouvert"
        except:
            return "Impossible d'ouvrir Microsoft Outlook"
    
    # ===== COMMANDES DE FORMATAGE DE TEXTE =====
    elif "mets en gras" in texte:
        pyautogui.hotkey('ctrl', 'b')
        return "Texte mis en gras"
        
    elif "mets en italique" in texte:
        pyautogui.hotkey('ctrl', 'i')
        return "Texte mis en italique"
        
    elif "souligne" in texte and ("texte" in texte or "mot" in texte):
        pyautogui.hotkey('ctrl', 'u')
        return "Texte souligné"
        
    elif "aligne à gauche" in texte:
        pyautogui.hotkey('ctrl', 'l')
        return "Texte aligné à gauche"
        
    elif "centre le texte" in texte or "aligne au centre" in texte:
        pyautogui.hotkey('ctrl', 'e')
        return "Texte centré"
        
    elif "aligne à droite" in texte:
        pyautogui.hotkey('ctrl', 'r')
        return "Texte aligné à droite"
        
    elif "justifie" in texte and "texte" in texte:
        pyautogui.hotkey('ctrl', 'j')
        return "Texte justifié"
    
    # ===== COMMANDES DE GESTION DE DOCUMENTS =====
    elif "nouveau document" in texte:
        pyautogui.hotkey('ctrl', 'n')
        return "Nouveau document créé"
        
    elif "ouvre un document" in texte:
        pyautogui.hotkey('ctrl', 'o')
        return "Boîte de dialogue d'ouverture affichée"
        
    elif "enregistre le document" in texte or "sauvegarde le document" in texte:
        pyautogui.hotkey('ctrl', 's')
        return "Document enregistré"
        
    elif "enregistre sous" in texte:
        pyautogui.hotkey('f12')
        return "Boîte de dialogue d'enregistrement sous affichée"
        
    elif "imprime le document" in texte:
        pyautogui.hotkey('ctrl', 'p')
        return "Boîte de dialogue d'impression affichée"
        
    elif "ferme le document" in texte:
        pyautogui.hotkey('ctrl', 'w')
        return "Document fermé"
    
    # ===== COMMANDES DE PRÉSENTATION =====
    elif "lance la présentation" in texte or "démarre le diaporama" in texte:
        pyautogui.press('f5')
        return "Présentation lancée"
        
    elif "diapositive suivante" in texte:
        pyautogui.press('right')
        return "Diapositive suivante"
        
    elif "diapositive précédente" in texte:
        pyautogui.press('left')
        return "Diapositive précédente"
        
    elif "termine la présentation" in texte or "quitte le diaporama" in texte:
        pyautogui.press('escape')
        return "Présentation terminée"
    
    # ===== COMMANDES DE GESTION DU TEMPS =====
    elif "démarre un minuteur" in texte or "lance un chronomètre" in texte:
        # Extraire la durée si spécifiée
        duree = None
        mots = texte.split()
        for i, mot in enumerate(mots):
            if mot.isdigit() and i < len(mots) - 1:
                duree = int(mot)
                unite = mots[i+1]
                if "minute" in unite:
                    duree *= 60
                elif "heure" in unite:
                    duree *= 3600
                break
        
        if duree:
            # Utiliser une notification simple après le délai
            temps_fin = datetime.now().strftime("%H:%M:%S")
            return f"Minuteur de {duree} secondes démarré. Il se terminera à {temps_fin}"
        else:
            return "Durée du minuteur non spécifiée ou non reconnue"
    
    elif "quelle est la date" in texte:
        date = datetime.now().strftime("%A %d %B %Y")
        return f"Nous sommes le {date}"
    
    # ===== COMMANDES DE GESTION DES FENÊTRES =====
    elif "change de fenêtre" in texte or "fenêtre suivante" in texte:
        pyautogui.hotkey('alt', 'tab')
        return "Changement de fenêtre"
        
    elif "minimise la fenêtre" in texte:
        pyautogui.hotkey('win', 'down')
        return "Fenêtre minimisée"
        
    elif "maximise la fenêtre" in texte:
        pyautogui.hotkey('win', 'up')
        return "Fenêtre maximisée"
        
    elif "affiche le bureau" in texte or "montre le bureau" in texte:
        pyautogui.hotkey('win', 'd')
        return "Bureau affiché"
    
    # ===== COMMANDES DE RÉUNION =====
    elif "active le micro" in texte or "allume le micro" in texte:
        # Raccourcis pour différentes applications de visioconférence
        if "google meet" in texte or "meet" in texte:
            pyautogui.hotkey('ctrl', 'd')
        else:
            # Raccourci courant pour d'autres applications
            pyautogui.hotkey('alt', 'a')
        return "Micro activé"
        
    elif "désactive le micro" in texte or "coupe le micro" in texte:
        # Raccourcis pour différentes applications de visioconférence
        if "google meet" in texte or "meet" in texte:
            pyautogui.hotkey('ctrl', 'd')
        else:
            # Raccourci courant pour d'autres applications
            pyautogui.hotkey('alt', 'a')
        return "Micro désactivé"
        
    elif "active la caméra" in texte or "allume la caméra" in texte:
        # Raccourcis pour différentes applications de visioconférence
        if "google meet" in texte or "meet" in texte:
            pyautogui.hotkey('ctrl', 'e')
        else:
            # Raccourci courant pour d'autres applications
            pyautogui.hotkey('alt', 'v')
        return "Caméra activée"
        
    elif "désactive la caméra" in texte or "éteins la caméra" in texte:
        # Raccourcis pour différentes applications de visioconférence
        if "google meet" in texte or "meet" in texte:
            pyautogui.hotkey('ctrl', 'e')
        else:
            # Raccourci courant pour d'autres applications
            pyautogui.hotkey('alt', 'v')
        return "Caméra désactivée"
        
    elif "partage mon écran" in texte:
        # Détection de l'application de réunion
        if "google meet" in texte or "meet" in texte:
            # Google Meet utilise une séquence spécifique
            # Accéder au bouton Présenter avec Maj+Tab
            pyautogui.hotkey('shift', 'tab')
            time.sleep(0.5)
            # Appuyer sur Entrée pour ouvrir le menu de présentation
            pyautogui.press('enter')
            time.sleep(1)
            # Sélectionner "Votre écran entier"
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            # Sélectionner l'écran et confirmer
            pyautogui.press('enter')
            return "Partage d'écran Google Meet activé"
        elif "zoom" in texte:
            pyautogui.hotkey('alt', 's')  # Raccourci Zoom
            return "Partage d'écran Zoom activé"
        elif "teams" in texte:
            pyautogui.hotkey('ctrl', 'shift', 'e')  # Raccourci Teams
            return "Partage d'écran Teams activé"
        else:
            # Essayer la séquence de Google Meet par défaut
            # Accéder au bouton Présenter avec Maj+Tab
            pyautogui.hotkey('shift', 'tab')
            time.sleep(0.5)
            # Appuyer sur Entrée pour ouvrir le menu de présentation
            pyautogui.press('enter')
            time.sleep(1)
            # Sélectionner "Votre écran entier"
            pyautogui.press('tab')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)
            # Sélectionner l'écran et confirmer
            pyautogui.press('enter')
            return "Partage d'écran activé"
        
    elif "arrête le partage" in texte:
        if "google meet" in texte or "meet" in texte:
            pyautogui.hotkey('ctrl', 'alt', 's')  # Raccourci pour arrêter la présentation dans Google Meet
        elif "zoom" in texte:
            pyautogui.hotkey('alt', 's')  # Même raccourci dans Zoom
        elif "teams" in texte:
            pyautogui.hotkey('ctrl', 'shift', 'e')  # Même raccourci dans Teams
        else:
            # Essayer plusieurs raccourcis courants
            pyautogui.hotkey('ctrl', 'alt', 's')
            time.sleep(0.5)
            # Échap fonctionne souvent pour annuler le partage
            pyautogui.press('escape')
        return "Partage d'écran désactivé"
    
    # ===== COMMANDES DE PRISE DE NOTES AVANCÉES =====
    elif "note rapide" in texte:
        # Extraire le contenu de la note
        if ":" in texte:
            contenu = texte.split(":", 1)[1].strip()
        else:
            parties = texte.split("note rapide", 1)
            if len(parties) > 1:
                contenu = parties[1].strip()
            else:
                contenu = ""
        
        if contenu:
            # Créer un fichier de notes avec horodatage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Créer le dossier notes s'il n'existe pas
            os.makedirs("notes", exist_ok=True)
            
            # Déterminer le nom du fichier
            nom_fichier = f"notes/note_{timestamp}.txt"
            
            try:
                with open(nom_fichier, "w", encoding="utf-8") as f:
                    f.write(contenu)
                return f"Note enregistrée dans {nom_fichier}"
            except:
                return "Erreur lors de l'enregistrement de la note"
        else:
            return "Contenu de la note non spécifié"
    
    elif "ajoute à mes notes" in texte:
        # Extraire le contenu à ajouter
        if ":" in texte:
            contenu = texte.split(":", 1)[1].strip()
        else:
            parties = texte.split("ajoute à mes notes", 1)
            if len(parties) > 1:
                contenu = parties[1].strip()
            else:
                contenu = ""
        
        if contenu:
            # Créer le dossier notes s'il n'existe pas
            os.makedirs("notes", exist_ok=True)
            
            # Utiliser un fichier de notes du jour
            today = datetime.now().strftime("%Y-%m-%d")
            nom_fichier = f"notes/notes_{today}.txt"
            
            try:
                # Ajouter au fichier existant ou le créer
                with open(nom_fichier, "a", encoding="utf-8") as f:
                    f.write(f"\n[{datetime.now().strftime('%H:%M:%S')}] {contenu}\n")
                return f"Note ajoutée à {nom_fichier}"
            except:
                return "Erreur lors de l'ajout à la note"
        else:
            return "Contenu de la note non spécifié"
    
    elif "affiche mes notes" in texte or "montre mes notes" in texte:
        # Créer le dossier notes s'il n'existe pas
        os.makedirs("notes", exist_ok=True)
        
        # Déterminer quelle note afficher
        if "aujourd'hui" in texte or "du jour" in texte:
            today = datetime.now().strftime("%Y-%m-%d")
            nom_fichier = f"notes/notes_{today}.txt"
            
            if os.path.exists(nom_fichier):
                try:
                    # Ouvrir le fichier de notes
                    os.startfile(nom_fichier)
                    return f"Notes du jour ouvertes : {nom_fichier}"
                except:
                    return f"Erreur lors de l'ouverture des notes du jour"
            else:
                return "Aucune note pour aujourd'hui"
        else:
            # Afficher toutes les notes
            try:
                # Ouvrir le dossier de notes
                os.startfile("notes")
                return "Dossier de notes ouvert"
            except:
                return "Erreur lors de l'ouverture du dossier de notes"
    
    # ===== COMMANDES DE GESTION DU TEMPS AMÉLIORÉES =====
    elif "démarre un pomodoro" in texte:
        # Extraire la durée si spécifiée
        duree = 25  # Durée par défaut en minutes
        match = re.search(r"de\s+(\d+)\s+minutes", texte)
        if match:
            duree = int(match.group(1))
        
        # Calculer l'heure de fin
        now = datetime.now()
        end_time = now + datetime.timedelta(minutes=duree)
        end_time_str = end_time.strftime("%H:%M")
        
        # Afficher un message
        return f"Pomodoro de {duree} minutes démarré. Fin à {end_time_str}. Concentrez-vous sur votre tâche !"
        
    # ===== COMMANDES DE PRODUCTIVITÉ MULTIÉCRAN =====
    elif any(cmd in texte for cmd in ["organise les fenêtres sur tous les écrans", "organise en multiécran", 
                                     "répartis les fenêtres sur les écrans", "distribue les fenêtres", 
                                     "optimise l'affichage multiécran", "arrange les fenêtres sur tous les écrans"]):
        return organiser_fenetres_multiscreen()
        
    elif any(cmd in texte for cmd in ["déplace vers l'écran principal", "mets sur l'écran principal", 
                                     "envoie sur l'écran principal", "fenêtre sur écran principal"]):
        # Déplacer la fenêtre active vers l'écran principal avec une méthode plus fiable
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
        
        return "Fenêtre déplacée vers l'écran principal"
        
    elif any(cmd in texte for cmd in ["déplace vers l'écran secondaire", "mets sur l'écran secondaire", 
                                     "envoie sur l'écran secondaire", "fenêtre sur écran secondaire"]):
        # Déplacer la fenêtre active vers l'écran secondaire avec une méthode plus fiable
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
        
        return "Fenêtre déplacée vers l'écran secondaire"
        
    elif any(cmd in texte for cmd in ["capture l'écran principal", "screenshot écran principal", 
                                     "prends une capture de l'écran principal"]):
        # Capture d'écran de l'écran principal uniquement
        # Déplacer d'abord la fenêtre vers l'écran principal
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.keyDown('shift')
        time.sleep(0.2)
        pyautogui.press('left')
        time.sleep(0.2)
        pyautogui.keyUp('shift')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        time.sleep(0.5)
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.press('printscreen')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        return "Capture de l'écran principal enregistrée"
        
    elif any(cmd in texte for cmd in ["capture l'écran secondaire", "screenshot écran secondaire", 
                                     "prends une capture de l'écran secondaire"]):
        # Capture d'écran de l'écran secondaire
        # Déplacer d'abord la fenêtre vers l'écran secondaire
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.keyDown('shift')
        time.sleep(0.2)
        pyautogui.press('right')
        time.sleep(0.2)
        pyautogui.keyUp('shift')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        time.sleep(0.5)
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.press('printscreen')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        return "Capture de l'écran secondaire enregistrée"
        
    elif any(cmd in texte for cmd in ["mode présentateur", "active le mode présentateur", 
                                     "configure pour présentation", "prépare pour présentation"]):
        # Configurer pour une présentation (écran principal pour présentateur, secondaire pour audience)
        # Ouvrir les paramètres d'affichage Windows
        pyautogui.hotkey('win', 'p')
        time.sleep(0.5)
        # Sélectionner "Étendre"
        for _ in range(3):  # Appuyer sur flèche bas jusqu'à "Étendre"
            pyautogui.press('down')
            time.sleep(0.1)
        pyautogui.press('enter')
        time.sleep(1)
        
        # Ouvrir les paramètres d'affichage avancés
        subprocess.Popen("control desk.cpl", shell=True)
        
        return "Mode présentateur activé (affichage étendu). Configurez les écrans dans les paramètres qui s'ouvrent."
        
    elif any(cmd in texte for cmd in ["affiche différentes applications sur chaque écran", 
                                     "applications différentes sur chaque écran", 
                                     "répartis les applications", "une application par écran"]):
        # Obtenir le nombre d'écrans
        user32 = ctypes.WinDLL('user32')
        SM_CMONITORS = 80
        nb_ecrans = user32.GetSystemMetrics(SM_CMONITORS)
        
        if nb_ecrans < 2:
            return "Un seul écran détecté"
        
        # Maximiser la fenêtre active sur l'écran actuel
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.press('up')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        time.sleep(0.5)
        
        # Passer à la fenêtre suivante
        pyautogui.keyDown('alt')
        time.sleep(0.2)
        pyautogui.press('tab')
        time.sleep(0.2)
        pyautogui.keyUp('alt')
        time.sleep(0.5)
        
        # Déplacer vers un autre écran et maximiser
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.keyDown('shift')
        time.sleep(0.2)
        pyautogui.press('right')
        time.sleep(0.2)
        pyautogui.keyUp('shift')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        time.sleep(0.5)
        pyautogui.keyDown('win')
        time.sleep(0.2)
        pyautogui.press('up')
        time.sleep(0.2)
        pyautogui.keyUp('win')
        
        return "Applications réparties sur différents écrans"
    
    elif "démarre une pause" in texte:
        # Extraire la durée si spécifiée
        duree = 5  # Durée par défaut en minutes
        match = re.search(r"de\s+(\d+)\s+minutes", texte)
        if match:
            duree = int(match.group(1))
        
        # Calculer l'heure de fin
        now = datetime.now()
        end_time = now + datetime.timedelta(minutes=duree)
        end_time_str = end_time.strftime("%H:%M")
        
        # Afficher un message
        return f"Pause de {duree} minutes démarrée. Fin à {end_time_str}. Profitez de votre pause !"
    
    # ===== COMMANDES DE RACCOURCIS PERSONNALISÉS =====
    elif "crée un raccourci" in texte or "nouveau raccourci" in texte:
        # Extraire le nom et la commande du raccourci
        match_name = re.search(r"raccourci\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s+pour|\s+qui|\s+avec)", texte)
        match_cmd = re.search(r"(?:pour|qui|avec)\s+[:\"]?(.+?)[\"]?$", texte)
        
        if match_name and match_cmd:
            shortcut_name = match_name.group(1).strip()
            shortcut_cmd = match_cmd.group(1).strip()
            
            # Créer le fichier de raccourcis s'il n'existe pas
            shortcuts_file = "whisp_shortcuts.json"
            shortcuts = {}
            
            if os.path.exists(shortcuts_file):
                try:
                    with open(shortcuts_file, 'r', encoding='utf-8') as f:
                        shortcuts = json.load(f)
                except:
                    pass
            
            # Ajouter le nouveau raccourci
            shortcuts[shortcut_name] = shortcut_cmd
            
            try:
                with open(shortcuts_file, 'w', encoding='utf-8') as f:
                    json.dump(shortcuts, f, ensure_ascii=False, indent=2)
                return f"Raccourci '{shortcut_name}' créé pour la commande : {shortcut_cmd}"
            except:
                return "Erreur lors de la création du raccourci"
        else:
            return "Nom ou commande du raccourci non spécifié"
    
    elif "exécute le raccourci" in texte or "lance le raccourci" in texte:
        # Extraire le nom du raccourci
        match = re.search(r"raccourci\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        
        if match:
            shortcut_name = match.group(1).strip()
            
            # Charger les raccourcis
            shortcuts_file = "whisp_shortcuts.json"
            
            if os.path.exists(shortcuts_file):
                try:
                    with open(shortcuts_file, 'r', encoding='utf-8') as f:
                        shortcuts = json.load(f)
                    
                    if shortcut_name in shortcuts:
                        shortcut_cmd = shortcuts[shortcut_name]
                        
                        # Exécuter la commande
                        if shortcut_cmd.startswith("http"):
                            # Si c'est une URL, l'ouvrir dans le navigateur
                            webbrowser.open(shortcut_cmd)
                            return f"Raccourci '{shortcut_name}' exécuté : URL ouverte"
                        else:
                            # Sinon, essayer de l'exécuter comme une commande système
                            subprocess.Popen(shortcut_cmd, shell=True)
                            return f"Raccourci '{shortcut_name}' exécuté"
                    else:
                        return f"Raccourci '{shortcut_name}' non trouvé"
                except:
                    return "Erreur lors de l'exécution du raccourci"
            else:
                return "Aucun raccourci défini"
        else:
            return "Nom du raccourci non spécifié"
    
    # ===== COMMANDES DE FOCUS ET CONCENTRATION =====
    elif "mode concentration" in texte or "mode focus" in texte:
        if "active" in texte or "démarre" in texte:
            # Fermer les applications de distraction
            try:
                # Fermer le navigateur
                os.system("taskkill /f /im chrome.exe")
                os.system("taskkill /f /im firefox.exe")
                os.system("taskkill /f /im msedge.exe")
                
                # Fermer les applications de messagerie
                os.system("taskkill /f /im slack.exe")
                os.system("taskkill /f /im teams.exe")
                os.system("taskkill /f /im outlook.exe")
                
                return "Mode concentration activé. Applications de distraction fermées."
            except:
                return "Erreur lors de l'activation du mode concentration"
        elif "désactive" in texte or "arrête" in texte:
            return "Mode concentration désactivé"
    
    return None  # Commande non reconnue
