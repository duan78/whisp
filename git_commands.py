"""
Module de commandes Git pour l'assistant Whisp
"""

import subprocess
import os
import pyautogui
import re
from text_processing import ecrire_texte_avec_accents

def executer_commande_git(texte):
    """Exécute des commandes Git en fonction du texte transcrit"""
    texte = texte.lower()
    
    # ===== COMMANDES GIT DE BASE =====
    if "git status" in texte:
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True)
            return f"Statut Git :\n{result.stdout[:500]}..."  # Limiter la sortie
        except:
            return "Erreur lors de l'exécution de git status"
    
    elif "git init" in texte:
        try:
            subprocess.run(["git", "init"])
            return "Dépôt Git initialisé"
        except:
            return "Erreur lors de l'initialisation du dépôt Git"
    
    elif "git clone" in texte:
        # Extraire l'URL du dépôt
        match = re.search(r"git clone\s+(https?://\S+|git@\S+)", texte)
        if match:
            repo_url = match.group(1)
            try:
                subprocess.run(["git", "clone", repo_url])
                return f"Dépôt cloné depuis {repo_url}"
            except:
                return f"Erreur lors du clonage depuis {repo_url}"
        else:
            return "URL du dépôt non spécifiée"
    
    # ===== COMMANDES DE STAGING ET COMMIT =====
    elif "git add" in texte:
        if "git add tout" in texte or "git add all" in texte:
            try:
                subprocess.run(["git", "add", "."])
                return "Tous les fichiers ajoutés au staging"
            except:
                return "Erreur lors de l'ajout des fichiers"
        else:
            # Extraire le nom du fichier
            match = re.search(r"git add\s+(\S+)", texte)
            if match:
                file_name = match.group(1)
                try:
                    subprocess.run(["git", "add", file_name])
                    return f"Fichier {file_name} ajouté au staging"
                except:
                    return f"Erreur lors de l'ajout de {file_name}"
            else:
                return "Nom de fichier non spécifié"
    
    elif "git commit" in texte:
        # Extraire le message de commit
        match = re.search(r"git commit\s+(?:avec message|message)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            commit_msg = match.group(1).strip()
            try:
                subprocess.run(["git", "commit", "-m", commit_msg])
                return f"Commit effectué avec le message : {commit_msg}"
            except:
                return "Erreur lors du commit"
        else:
            # Si pas de message spécifié, ouvrir l'éditeur de commit
            try:
                subprocess.run(["git", "commit"])
                return "Éditeur de commit ouvert"
            except:
                return "Erreur lors de l'ouverture de l'éditeur de commit"
    
    # ===== COMMANDES DE SYNCHRONISATION =====
    elif "git pull" in texte:
        try:
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)
            return f"Pull effectué :\n{result.stdout[:500]}..."
        except:
            return "Erreur lors du pull"
    
    elif "git push" in texte:
        try:
            result = subprocess.run(["git", "push"], capture_output=True, text=True)
            return f"Push effectué :\n{result.stdout[:500]}..."
        except:
            return "Erreur lors du push"
    
    # ===== COMMANDES DE BRANCHES =====
    elif "git branch" in texte:
        if "crée" in texte or "nouvelle" in texte or "créer" in texte:
            # Extraire le nom de la branche
            match = re.search(r"branch\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?$", texte)
            if match:
                branch_name = match.group(1).strip()
                try:
                    subprocess.run(["git", "branch", branch_name])
                    return f"Branche {branch_name} créée"
                except:
                    return f"Erreur lors de la création de la branche {branch_name}"
            else:
                return "Nom de branche non spécifié"
        elif "liste" in texte or "affiche" in texte:
            try:
                result = subprocess.run(["git", "branch"], capture_output=True, text=True)
                return f"Branches :\n{result.stdout}"
            except:
                return "Erreur lors de l'affichage des branches"
        else:
            try:
                result = subprocess.run(["git", "branch"], capture_output=True, text=True)
                return f"Branches :\n{result.stdout}"
            except:
                return "Erreur lors de l'affichage des branches"
    
    elif "git checkout" in texte or "git basculer" in texte or "git changer de branche" in texte:
        # Extraire le nom de la branche
        match = re.search(r"(?:checkout|basculer|changer de branche)\s+(?:vers|sur)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            branch_name = match.group(1).strip()
            try:
                subprocess.run(["git", "checkout", branch_name])
                return f"Basculé sur la branche {branch_name}"
            except:
                return f"Erreur lors du basculement sur {branch_name}"
        else:
            return "Nom de branche non spécifié"
    
    # ===== COMMANDES DE DIFF ET LOG =====
    elif "git diff" in texte:
        try:
            result = subprocess.run(["git", "diff"], capture_output=True, text=True)
            return f"Différences :\n{result.stdout[:500]}..."
        except:
            return "Erreur lors de l'affichage des différences"
    
    elif "git log" in texte:
        try:
            if "court" in texte or "résumé" in texte:
                result = subprocess.run(["git", "log", "--oneline", "--graph", "--decorate", "-n", "10"], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(["git", "log", "-n", "5"], capture_output=True, text=True)
            return f"Historique des commits :\n{result.stdout[:800]}..."
        except:
            return "Erreur lors de l'affichage de l'historique"
    
    # ===== COMMANDES DE STASH =====
    elif "git stash" in texte:
        if "sauvegarder" in texte or "créer" in texte:
            try:
                subprocess.run(["git", "stash", "push"])
                return "Modifications mises de côté"
            except:
                return "Erreur lors de la mise de côté des modifications"
        elif "appliquer" in texte:
            try:
                subprocess.run(["git", "stash", "apply"])
                return "Modifications réappliquées"
            except:
                return "Erreur lors de la réapplication des modifications"
        elif "liste" in texte:
            try:
                result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
                return f"Liste des stash :\n{result.stdout}"
            except:
                return "Erreur lors de l'affichage de la liste des stash"
        else:
            try:
                subprocess.run(["git", "stash"])
                return "Modifications mises de côté"
            except:
                return "Erreur lors de la mise de côté des modifications"
    
    # ===== COMMANDES AVANCÉES =====
    elif "git reset" in texte:
        if "hard" in texte:
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD"])
                return "Reset hard effectué"
            except:
                return "Erreur lors du reset hard"
        elif "soft" in texte:
            try:
                subprocess.run(["git", "reset", "--soft", "HEAD~1"])
                return "Reset soft effectué (annulation du dernier commit)"
            except:
                return "Erreur lors du reset soft"
        else:
            try:
                subprocess.run(["git", "reset"])
                return "Reset effectué"
            except:
                return "Erreur lors du reset"
    
    elif "git merge" in texte:
        # Extraire le nom de la branche
        match = re.search(r"merge\s+(?:avec|de)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            branch_name = match.group(1).strip()
            try:
                subprocess.run(["git", "merge", branch_name])
                return f"Fusion avec la branche {branch_name} effectuée"
            except:
                return f"Erreur lors de la fusion avec {branch_name}"
        else:
            return "Nom de branche non spécifié"
    
    # ===== COMMANDES DE CONFIGURATION =====
    elif "git config" in texte:
        if "nom utilisateur" in texte or "username" in texte:
            # Extraire le nom d'utilisateur
            match = re.search(r"(?:nom utilisateur|username)\s+(?:à|comme|en)?\s*[:\"]?(.+?)[\"]?$", texte)
            if match:
                username = match.group(1).strip()
                try:
                    subprocess.run(["git", "config", "user.name", username])
                    return f"Nom d'utilisateur Git configuré : {username}"
                except:
                    return "Erreur lors de la configuration du nom d'utilisateur"
            else:
                return "Nom d'utilisateur non spécifié"
        
        elif "email" in texte:
            # Extraire l'email
            match = re.search(r"email\s+(?:à|comme|en)?\s*[:\"]?(.+?)[\"]?$", texte)
            if match:
                email = match.group(1).strip()
                try:
                    subprocess.run(["git", "config", "user.email", email])
                    return f"Email Git configuré : {email}"
                except:
                    return "Erreur lors de la configuration de l'email"
            else:
                return "Email non spécifié"
        
        elif "affiche" in texte or "montre" in texte:
            try:
                result = subprocess.run(["git", "config", "--list"], capture_output=True, text=True)
                return f"Configuration Git :\n{result.stdout[:500]}..."
            except:
                return "Erreur lors de l'affichage de la configuration"
    
    # ===== COMMANDES PERSONNALISÉES =====
    elif "crée commit conventionnel" in texte or "commit conventionnel" in texte:
        # Format: type(scope): description
        types = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
        
        # Déterminer le type
        type_commit = "feat"  # Par défaut
        for t in types:
            if t in texte:
                type_commit = t
                break
        
        # Extraire le scope si présent
        scope = ""
        match_scope = re.search(r"scope\s+(?:est|:|comme)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match_scope:
            scope = f"({match_scope.group(1).strip()})"
        
        # Extraire la description
        match_desc = re.search(r"(?:description|message)\s+(?:est|:|comme)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match_desc:
            description = match_desc.group(1).strip()
            commit_msg = f"{type_commit}{scope}: {description}"
            
            try:
                subprocess.run(["git", "commit", "-m", commit_msg])
                return f"Commit conventionnel effectué : {commit_msg}"
            except:
                return "Erreur lors du commit conventionnel"
        else:
            return "Description du commit non spécifiée"
    
    return None  # Commande non reconnue
