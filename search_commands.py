"""
Module de commandes de recherche rapide pour l'assistant Whisp
"""

import webbrowser
import re
import urllib.parse
import pyperclip
import pyautogui

def executer_commande_recherche(texte):
    """Exécute des commandes de recherche rapide"""
    texte = texte.lower()
    
    # ===== RECHERCHE WEB =====
    if "recherche" in texte and ("sur google" in texte or "google" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(.+?)\s+(?:sur google|sur|google)$", texte)
        if not match:
            match = re.search(r"recherche\s+(?:sur google|google)?\s*[:\"]?(.+?)[\"]?$", texte)
        
        if match:
            query = match.group(1).strip()
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche Google effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    elif "recherche" in texte and ("sur youtube" in texte or "youtube" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(?:sur youtube|youtube)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            query = match.group(1).strip()
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche YouTube effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    elif "recherche" in texte and ("sur wikipedia" in texte or "wikipedia" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(?:sur wikipedia|wikipedia)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            query = match.group(1).strip()
            url = f"https://fr.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche Wikipedia effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    elif "recherche" in texte and ("sur amazon" in texte or "amazon" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(?:sur amazon|amazon)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            query = match.group(1).strip()
            url = f"https://www.amazon.fr/s?k={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche Amazon effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    elif "recherche" in texte and ("sur stackoverflow" in texte or "stack overflow" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(?:sur stackoverflow|stack overflow)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            query = match.group(1).strip()
            url = f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche Stack Overflow effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    elif "recherche" in texte and ("sur github" in texte or "github" in texte):
        # Extraire les termes de recherche
        match = re.search(r"recherche\s+(?:sur github|github)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            query = match.group(1).strip()
            url = f"https://github.com/search?q={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Recherche GitHub effectuée pour : {query}"
        else:
            return "Termes de recherche non spécifiés"
    
    # ===== RECHERCHE LOCALE =====
    elif "recherche fichier" in texte or "trouve fichier" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:fichier|document)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            filename = match.group(1).strip()
            # Ouvrir la recherche Windows avec le nom du fichier
            pyautogui.hotkey('win', 'f')
            pyautogui.typewrite(filename)
            return f"Recherche de fichier lancée pour : {filename}"
        else:
            return "Nom de fichier non spécifié"
    
    # ===== TRADUCTION =====
    elif "traduis" in texte:
        # Extraire le texte à traduire
        match = re.search(r"traduis\s+[:\"]?(.+?)[\"]?(?:\s+(?:en|vers|du))?", texte)
        if match:
            text_to_translate = match.group(1).strip()
            
            # Déterminer la langue cible
            target_lang = "en"  # Par défaut, anglais
            if "en anglais" in texte:
                target_lang = "en"
            elif "en espagnol" in texte:
                target_lang = "es"
            elif "en allemand" in texte:
                target_lang = "de"
            elif "en italien" in texte:
                target_lang = "it"
            elif "en portugais" in texte:
                target_lang = "pt"
            elif "en russe" in texte:
                target_lang = "ru"
            elif "en chinois" in texte:
                target_lang = "zh"
            elif "en japonais" in texte:
                target_lang = "ja"
            elif "en arabe" in texte:
                target_lang = "ar"
            
            # Ouvrir Google Translate avec le texte à traduire
            url = f"https://translate.google.com/?sl=auto&tl={target_lang}&text={urllib.parse.quote(text_to_translate)}&op=translate"
            webbrowser.open(url)
            return f"Traduction lancée pour : {text_to_translate}"
        else:
            return "Texte à traduire non spécifié"
    
    # ===== DÉFINITION =====
    elif "définis" in texte or "définition de" in texte:
        # Extraire le mot à définir
        match = re.search(r"(?:définis|définition de)\s+[:\"]?(.+?)[\"]?$", texte)
        if match:
            word = match.group(1).strip()
            url = f"https://www.larousse.fr/dictionnaires/francais/{urllib.parse.quote(word)}"
            webbrowser.open(url)
            return f"Recherche de définition pour : {word}"
        else:
            return "Mot à définir non spécifié"
    
    return None  # Commande non reconnue
