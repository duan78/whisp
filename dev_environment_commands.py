"""
Module de commandes pour les environnements de développement (IDE, etc.)
"""

import subprocess
import os
import pyautogui
import re
import time
from text_processing import ecrire_texte_avec_accents

def executer_commande_dev(texte):
    """Exécute des commandes liées aux environnements de développement"""
    texte = texte.lower()
    
    # ===== COMMANDES VS CODE =====
    if "ouvre vs code" in texte or "lance vs code" in texte or "ouvre visual studio code" in texte:
        try:
            subprocess.Popen(["code"])
            return "VS Code ouvert"
        except:
            return "Impossible d'ouvrir VS Code"
    
    elif "ouvre dossier dans vs code" in texte or "ouvre projet dans vs code" in texte:
        # Extraire le chemin du dossier si spécifié
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_path = match.group(1).strip()
            try:
                subprocess.Popen(["code", folder_path])
                return f"Dossier {folder_path} ouvert dans VS Code"
            except:
                return f"Impossible d'ouvrir {folder_path} dans VS Code"
        else:
            # Ouvrir le dossier courant
            try:
                subprocess.Popen(["code", "."])
                return "Dossier courant ouvert dans VS Code"
            except:
                return "Impossible d'ouvrir le dossier courant dans VS Code"
    
    # ===== RACCOURCIS VS CODE =====
    elif "vs code" in texte and "palette de commandes" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'p')
        return "Palette de commandes VS Code ouverte"
        
    elif "vs code" in texte and "terminal intégré" in texte:
        pyautogui.hotkey('ctrl', '`')
        return "Terminal intégré VS Code ouvert/fermé"
        
    elif "vs code" in texte and "explorateur de fichiers" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'e')
        return "Explorateur de fichiers VS Code affiché"
        
    elif "vs code" in texte and "recherche globale" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'f')
        return "Recherche globale VS Code ouverte"
        
    elif "vs code" in texte and "aller au fichier" in texte:
        pyautogui.hotkey('ctrl', 'p')
        return "Navigation rapide vers fichier VS Code ouverte"
        
    elif "vs code" in texte and "extensions" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'x')
        return "Gestionnaire d'extensions VS Code ouvert"
        
    elif "vs code" in texte and "débogueur" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'd')
        return "Débogueur VS Code ouvert"
        
    elif "vs code" in texte and "git" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'g')
        return "Panneau Git VS Code ouvert"
    
    # ===== COMMANDES PYCHARM =====
    elif "ouvre pycharm" in texte or "lance pycharm" in texte:
        try:
            subprocess.Popen(["pycharm"])
            return "PyCharm ouvert"
        except:
            try:
                # Chemin alternatif pour PyCharm
                subprocess.Popen(["C:\\Program Files\\JetBrains\\PyCharm Community Edition\\bin\\pycharm64.exe"])
                return "PyCharm ouvert"
            except:
                return "Impossible d'ouvrir PyCharm"
    
    # ===== RACCOURCIS PYCHARM =====
    elif "pycharm" in texte and "recherche partout" in texte:
        pyautogui.hotkey('shift', 'shift')
        return "Recherche partout PyCharm activée"
        
    elif "pycharm" in texte and "action rapide" in texte:
        pyautogui.hotkey('ctrl', 'shift', 'a')
        return "Recherche d'action PyCharm activée"
        
    elif "pycharm" in texte and "terminal" in texte:
        pyautogui.hotkey('alt', 'f12')
        return "Terminal PyCharm ouvert"
        
    elif "pycharm" in texte and "structure du projet" in texte:
        pyautogui.hotkey('alt', '1')
        return "Structure du projet PyCharm affichée"
    
    # ===== COMMANDES DOCKER =====
    elif "docker status" in texte or "état docker" in texte:
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            return f"Conteneurs Docker en cours d'exécution :\n{result.stdout}"
        except:
            return "Erreur lors de l'exécution de docker ps"
    
    elif "docker images" in texte or "liste des images docker" in texte:
        try:
            result = subprocess.run(["docker", "images"], capture_output=True, text=True)
            return f"Images Docker disponibles :\n{result.stdout}"
        except:
            return "Erreur lors de l'exécution de docker images"
    
    elif "lance conteneur" in texte and "docker" in texte:
        # Extraire le nom de l'image
        match = re.search(r"conteneur\s+(?:avec image|image)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            image_name = match.group(1).strip()
            try:
                subprocess.run(["docker", "run", "-d", image_name])
                return f"Conteneur Docker lancé avec l'image {image_name}"
            except:
                return f"Erreur lors du lancement du conteneur avec l'image {image_name}"
        else:
            return "Nom d'image non spécifié"
    
    # ===== COMMANDES VIRTUALENV =====
    elif "crée environnement virtuel" in texte or "crée venv" in texte:
        # Extraire le nom de l'environnement
        match = re.search(r"(?:environnement virtuel|venv)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            env_name = match.group(1).strip()
            try:
                subprocess.run(["python", "-m", "venv", env_name])
                return f"Environnement virtuel {env_name} créé"
            except:
                return f"Erreur lors de la création de l'environnement virtuel {env_name}"
        else:
            # Nom par défaut
            try:
                subprocess.run(["python", "-m", "venv", "venv"])
                return "Environnement virtuel 'venv' créé"
            except:
                return "Erreur lors de la création de l'environnement virtuel"
    
    elif "active environnement virtuel" in texte or "active venv" in texte:
        # Extraire le nom de l'environnement
        match = re.search(r"(?:environnement virtuel|venv)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        env_name = "venv"
        if match:
            env_name = match.group(1).strip()
        
        # Construire le chemin d'activation
        if os.name == 'nt':  # Windows
            activate_path = os.path.join(env_name, "Scripts", "activate.bat")
            return f"Pour activer l'environnement, exécutez : {activate_path}"
        else:  # Unix/Linux/Mac
            activate_path = os.path.join(env_name, "bin", "activate")
            return f"Pour activer l'environnement, exécutez : source {activate_path}"
    
    # ===== COMMANDES PIP =====
    elif "installe package" in texte or "installe module" in texte or "pip install" in texte:
        # Extraire le nom du package
        match = re.search(r"(?:package|module|pip install)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            package_name = match.group(1).strip()
            try:
                subprocess.run(["pip", "install", package_name])
                return f"Package {package_name} installé"
            except:
                return f"Erreur lors de l'installation du package {package_name}"
        else:
            return "Nom de package non spécifié"
    
    elif "liste des packages" in texte or "pip list" in texte:
        try:
            result = subprocess.run(["pip", "list"], capture_output=True, text=True)
            return f"Packages installés :\n{result.stdout[:500]}..."
        except:
            return "Erreur lors de l'affichage des packages installés"
    
    # ===== COMMANDES NPM =====
    elif "npm install" in texte or "installe package npm" in texte:
        # Extraire le nom du package
        match = re.search(r"(?:npm install|package npm)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            package_name = match.group(1).strip()
            try:
                subprocess.run(["npm", "install", package_name])
                return f"Package npm {package_name} installé"
            except:
                return f"Erreur lors de l'installation du package npm {package_name}"
        else:
            # Installation globale des dépendances
            try:
                subprocess.run(["npm", "install"])
                return "Dépendances npm installées"
            except:
                return "Erreur lors de l'installation des dépendances npm"
    
    elif "npm start" in texte or "démarre application npm" in texte:
        try:
            subprocess.Popen(["npm", "start"])
            return "Application npm démarrée"
        except:
            return "Erreur lors du démarrage de l'application npm"
    
    # ===== COMMANDES PYTHON =====
    elif "exécute script python" in texte or "lance script python" in texte:
        # Extraire le nom du script
        match = re.search(r"(?:script python|python)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            script_name = match.group(1).strip()
            try:
                subprocess.Popen(["python", script_name])
                return f"Script Python {script_name} exécuté"
            except:
                return f"Erreur lors de l'exécution du script Python {script_name}"
        else:
            return "Nom de script non spécifié"
    
    # ===== COMMANDES TESTS =====
    elif "lance les tests" in texte or "exécute les tests" in texte:
        if "pytest" in texte:
            try:
                result = subprocess.run(["pytest"], capture_output=True, text=True)
                return f"Tests pytest exécutés :\n{result.stdout[:500]}..."
            except:
                return "Erreur lors de l'exécution des tests pytest"
        elif "unittest" in texte:
            try:
                result = subprocess.run(["python", "-m", "unittest", "discover"], capture_output=True, text=True)
                return f"Tests unittest exécutés :\n{result.stdout[:500]}..."
            except:
                return "Erreur lors de l'exécution des tests unittest"
        else:
            # Par défaut, essayer pytest
            try:
                result = subprocess.run(["pytest"], capture_output=True, text=True)
                return f"Tests exécutés :\n{result.stdout[:500]}..."
            except:
                try:
                    result = subprocess.run(["python", "-m", "unittest", "discover"], capture_output=True, text=True)
                    return f"Tests exécutés :\n{result.stdout[:500]}..."
                except:
                    return "Erreur lors de l'exécution des tests"
    
    # ===== COMMANDES FORMATAGE DE CODE =====
    elif "formate le code" in texte:
        if "black" in texte:
            # Extraire le chemin du fichier ou dossier
            match = re.search(r"(?:fichier|dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
            if match:
                path = match.group(1).strip()
                try:
                    subprocess.run(["black", path])
                    return f"Code formaté avec Black : {path}"
                except:
                    return f"Erreur lors du formatage avec Black : {path}"
            else:
                # Formater le dossier courant
                try:
                    subprocess.run(["black", "."])
                    return "Code du dossier courant formaté avec Black"
                except:
                    return "Erreur lors du formatage avec Black"
        elif "autopep8" in texte:
            # Extraire le chemin du fichier
            match = re.search(r"(?:fichier|dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
            if match:
                path = match.group(1).strip()
                try:
                    subprocess.run(["autopep8", "--in-place", "--aggressive", "--aggressive", path])
                    return f"Code formaté avec autopep8 : {path}"
                except:
                    return f"Erreur lors du formatage avec autopep8 : {path}"
            else:
                return "Chemin du fichier non spécifié pour autopep8"
        else:
            # Par défaut, essayer black
            try:
                subprocess.run(["black", "."])
                return "Code du dossier courant formaté avec Black"
            except:
                return "Outil de formatage non disponible. Installez Black ou autopep8."
    
    # ===== COMMANDES LINTING =====
    elif "vérifie le code" in texte or "lint le code" in texte:
        if "flake8" in texte:
            # Extraire le chemin du fichier ou dossier
            match = re.search(r"(?:fichier|dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
            if match:
                path = match.group(1).strip()
                try:
                    result = subprocess.run(["flake8", path], capture_output=True, text=True)
                    if result.stdout:
                        return f"Problèmes détectés par flake8 :\n{result.stdout[:500]}..."
                    else:
                        return "Aucun problème détecté par flake8"
                except:
                    return f"Erreur lors de la vérification avec flake8 : {path}"
            else:
                # Vérifier le dossier courant
                try:
                    result = subprocess.run(["flake8"], capture_output=True, text=True)
                    if result.stdout:
                        return f"Problèmes détectés par flake8 :\n{result.stdout[:500]}..."
                    else:
                        return "Aucun problème détecté par flake8"
                except:
                    return "Erreur lors de la vérification avec flake8"
        elif "pylint" in texte:
            # Extraire le chemin du fichier
            match = re.search(r"(?:fichier|dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
            if match:
                path = match.group(1).strip()
                try:
                    result = subprocess.run(["pylint", path], capture_output=True, text=True)
                    return f"Résultats pylint :\n{result.stdout[:500]}..."
                except:
                    return f"Erreur lors de la vérification avec pylint : {path}"
            else:
                return "Chemin du fichier non spécifié pour pylint"
        else:
            # Par défaut, essayer flake8
            try:
                result = subprocess.run(["flake8"], capture_output=True, text=True)
                if result.stdout:
                    return f"Problèmes détectés :\n{result.stdout[:500]}..."
                else:
                    return "Aucun problème détecté"
            except:
                return "Outil de linting non disponible. Installez flake8 ou pylint."
    
    return None  # Commande non reconnue
