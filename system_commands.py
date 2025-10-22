"""
Module de gestion des commandes système pour l'assistant Whisp
"""

import os
import datetime
import platform
import subprocess
import pyautogui
from config import set_running

def executer_commande_systeme(texte):
    """Exécute des commandes système en fonction du texte transcrit"""
    texte = texte.lower()
    
    # ===== GESTION DU SYSTÈME =====
    if any(cmd in texte for cmd in ["quelle heure est-il", "quelle heure est il", "quelle est l'heure", 
                                   "donne-moi l'heure", "donne moi l'heure", "dis-moi l'heure", 
                                   "dis moi l'heure", "heure actuelle", "heure courante",
                                   "affiche l'heure", "afficher l'heure", "montre l'heure", 
                                   "montrer l'heure", "il est quelle heure", "c'est quelle heure",
                                   "l'heure s'il te plaît", "l'heure s'il vous plaît"]):
        heure = datetime.datetime.now().strftime("%H:%M")
        return f"Il est {heure}"
        
    elif any(cmd in texte for cmd in ["quel jour sommes-nous", "quel jour sommes nous", "quelle est la date", 
                                     "quelle date sommes-nous", "quelle date sommes nous", 
                                     "donne-moi la date", "donne moi la date", "dis-moi la date", 
                                     "dis moi la date", "date actuelle", "date courante", "date du jour",
                                     "affiche la date", "afficher la date", "montre la date", 
                                     "montrer la date", "on est quel jour", "c'est quel jour",
                                     "la date s'il te plaît", "la date s'il vous plaît",
                                     "quel jour on est", "quel jour est-on"]):
        jour = datetime.datetime.now().strftime("%A %d %B %Y")
        return f"Nous sommes le {jour}"
    
    elif "mets en veille" in texte:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Mise en veille de l'ordinateur"
    
    elif "infos système" in texte or "informations système" in texte:
        cpu = platform.processor()
        os_info = platform.platform()
        return f"CPU: {cpu}, OS: {os_info}"
    
    elif "prends une capture d'écran" in texte:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pyautogui.screenshot(f'capture_{timestamp}.png')
        return f"Capture d'écran enregistrée sous capture_{timestamp}.png"
    
    elif any(cmd in texte for cmd in ["ouvre le bloc-notes", "ouvrir le bloc-notes", "lance le bloc-notes", 
                                     "lancer le bloc-notes", "démarre le bloc-notes", "démarrer le bloc-notes",
                                     "ouvre bloc-notes", "ouvrir bloc-notes", "lance bloc-notes", 
                                     "lancer bloc-notes", "démarre bloc-notes", "démarrer bloc-notes",
                                     "ouvre notepad", "ouvrir notepad", "lance notepad", "lancer notepad",
                                     "démarre notepad", "démarrer notepad", "éditeur de texte",
                                     "ouvre l'éditeur de texte", "ouvrir l'éditeur de texte"]):
        subprocess.Popen('notepad')
        return "Bloc-notes ouvert"
        
    elif any(cmd in texte for cmd in ["ouvre la calculatrice", "ouvrir la calculatrice", "lance la calculatrice", 
                                     "lancer la calculatrice", "démarre la calculatrice", "démarrer la calculatrice",
                                     "ouvre calculatrice", "ouvrir calculatrice", "lance calculatrice", 
                                     "lancer calculatrice", "démarre calculatrice", "démarrer calculatrice",
                                     "ouvre calc", "ouvrir calc", "lance calc", "lancer calc",
                                     "démarre calc", "démarrer calc", "fais un calcul", "faire un calcul"]):
        subprocess.Popen('calc')
        return "Calculatrice ouverte"
    
    elif any(cmd in texte for cmd in ["lance l'explorateur", "lancer l'explorateur", "ouvre l'explorateur", 
                                     "ouvrir l'explorateur", "démarre l'explorateur", "démarrer l'explorateur",
                                     "ouvre mes documents", "ouvrir mes documents", "lance mes documents", 
                                     "lancer mes documents", "démarre mes documents", "démarrer mes documents",
                                     "ouvre explorateur", "ouvrir explorateur", "lance explorateur", 
                                     "lancer explorateur", "démarre explorateur", "démarrer explorateur",
                                     "ouvre fichiers", "ouvrir fichiers", "lance fichiers", "lancer fichiers",
                                     "démarre fichiers", "démarrer fichiers", "gestionnaire de fichiers",
                                     "ouvre le gestionnaire de fichiers", "ouvrir le gestionnaire de fichiers"]):
        subprocess.Popen('explorer')
        return "Explorateur de fichiers ouvert"
    
    elif any(cmd in texte for cmd in ["quitte l'assistant", "quitter l'assistant", "arrête toi", "arrête-toi", 
                                     "arrêter", "au revoir", "ferme l'assistant", "fermer l'assistant",
                                     "ferme le programme", "fermer le programme", "termine l'assistant", 
                                     "terminer l'assistant", "termine le programme", "terminer le programme",
                                     "stop", "stoppe", "stopper", "fin", "fini", "finir", "bye", "ciao",
                                     "à plus tard", "à bientôt", "à la prochaine", "éteins-toi", "éteindre",
                                     "désactive-toi", "désactiver", "quitte", "quitter"]):
        set_running(False)
        return "Assistant vocal arrêté. Au revoir !"
    
    elif "aide" in texte or "quelles sont les commandes" in texte:
        if "développeur" in texte or "dev" in texte:
            return """Commandes de développement disponibles :
            
            - Git : 
              'git status', 'git init', 'git clone [url]', 'git add [fichier/tout]', 
              'git commit avec message [message]', 'git pull', 'git push', 
              'git branch [nom]', 'git checkout [branche]', 'git diff', 'git log', 
              'git stash', 'git reset', 'git merge [branche]', 'crée commit conventionnel'
              
            - Environnements de développement :
              'ouvre vs code', 'ouvre dossier dans vs code', 'vs code palette de commandes',
              'vs code terminal intégré', 'vs code explorateur de fichiers', 'vs code recherche globale',
              'ouvre pycharm', 'pycharm recherche partout', 'pycharm action rapide',
              'docker status', 'docker images', 'lance conteneur docker [image]',
              'crée environnement virtuel [nom]', 'active environnement virtuel [nom]'
              
            - Packages et dépendances :
              'installe package [nom]', 'liste des packages', 'npm install [package]',
              'npm start', 'exécute script python [nom]', 'lance les tests'
              
            - Formatage et vérification de code :
              'formate le code avec black', 'vérifie le code avec flake8'
              
            - Gestion de projet :
              'crée structure de projet [type] [nom]', 'génère documentation',
              'ajoute tâche [description]', 'liste des tâches', 'termine tâche [id]',
              'planifie sprint [nom]'
              
            - Développement web :
              'lance serveur http', 'lance serveur flask', 'lance serveur django',
              'crée composant react [nom]', 'crée page html [nom]', 'crée style css [nom]',
              'crée script javascript [nom]', 'crée api rest [nom]', 'valide html/css'
              
            - Bases de données :
              'crée base de données sqlite [nom]', 'crée table [nom] dans [base]',
              'exécute requête sqlite [requête] dans [base]', 'lance/arrête mysql/mongodb',
              'exécute script sql [fichier]', 'sauvegarde base de données [nom]'"""
        elif "productivité" in texte:
            return """Commandes de productivité disponibles :
            
            - Gestion des rappels :
              'crée un rappel [description] à [heure]', 'crée un rappel [description] dans [X minutes/heures]',
              'crée un rappel [description] le [jour] [mois]', 'liste des rappels', 'supprime le rappel [id]'
              
            - Prise de notes :
              'note rapide: [contenu]', 'ajoute à mes notes: [contenu]', 'affiche mes notes',
              'affiche mes notes d'aujourd'hui'
              
            - Recherche rapide :
              'recherche sur google [termes]', 'recherche sur youtube [termes]', 'recherche sur wikipedia [termes]',
              'recherche sur amazon [termes]', 'recherche sur stackoverflow [termes]', 'recherche sur github [termes]',
              'recherche fichier [nom]', 'traduis [texte] en [langue]', 'définis [mot]'
              
            - Gestion des fichiers :
              'crée un dossier [nom]', 'crée un fichier texte [nom]', 'copie le fichier [source] vers [destination]',
              'déplace le fichier [source] vers [destination]', 'renomme le fichier [source] en [nouveau nom]',
              'supprime le fichier/dossier [nom]', 'compresse le dossier [nom]', 'décompresse le fichier [nom]',
              'ouvre le fichier [nom]', 'liste les fichiers [dossier]'
              
            - Gestion du temps :
              'démarre un pomodoro de [X] minutes', 'démarre une pause de [X] minutes',
              'quelle est la date', 'démarre un minuteur de [X] minutes/heures'
              
            - Raccourcis personnalisés :
              'crée un raccourci [nom] pour [commande]', 'exécute le raccourci [nom]'
              
            - Focus et concentration :
              'active le mode concentration', 'désactive le mode concentration'"""
        else:
            return """Commandes disponibles :
            - Dictée : 'écris/tape/saisis/note' pour commencer la dictée, 'fin de dictée' pour terminer
            - Navigation : souris en haut à gauche/droite/centre, etc.
            - Déplacements relatifs : souris vers la gauche/droite/haut/bas
            - Clics : clic gauche/droit, double clic, maintiens/relâche clic
            - Navigateur : nouvel onglet, ferme l'onglet, onglet suivant/précédent
            - Défilement : défile vers le haut/bas
            - Applications : ouvre le navigateur/bloc-notes/calculatrice/explorateur
            - Système : capture d'écran, copier/coller, sélectionne tout
            - Clavier : entrer, espace, retour, flèches, etc.
            - Productivité : ouvre word/excel/powerpoint, formatage de texte, gestion de documents
            - Fenêtres : change de fenêtre, minimise/maximise, arrange les fenêtres
            - Réunions : active/désactive micro/caméra, partage d'écran
            
            Pour plus d'informations, dites :
            - 'aide développeur' pour les commandes de développement
            - 'aide productivité' pour les commandes de productivité avancées"""
    
    return None  # Commande non reconnue
