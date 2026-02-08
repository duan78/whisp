"""
Module de commandes Git pour l'assistant Whisp
"""

import subprocess
import os
import pyautogui
import re
from text_processing import ecrire_texte_avec_accents
from input_validation import InputValidator, ValidationError

validator = InputValidator()


def validate_git_url(url: str) -> bool:
    """Validate that a Git URL is legitimate and safe"""
    # Check for allowed URL patterns
    allowed_patterns = [
        r'^https?://[\w\-\.]+(:\d+)?/[\w\-/\.]+\.git$',  # HTTP(S)
        r'^https?://[\w\-\.]+(:\d+)?/[\w\-/\.]+$',       # HTTP(S) without .git
        r'^git@[\w\-\.]+:[\w\-/\.]+\.git$',              # SSH
        r'^git@[\w\-\.]+:[\w\-/\.]+$',                   # SSH without .git
    ]

    url = url.strip()

    for pattern in allowed_patterns:
        if re.match(pattern, url):
            return True

    return False


def validate_branch_name(name: str) -> bool:
    """Validate Git branch names"""
    if not name:
        return False
    # Git branch name rules: cannot contain .., ~, ^, :, ?, *, [, space, or start/end with /
    if re.search(r'[\.\.\~\^\:\?\*\[ ]|^/|/$', name):
        return False
    return len(name) <= 255


def executer_commande_git(texte):
    """Exécute des commandes Git en fonction du texte transcrit"""
    try:
        validator.validate_command_input(texte)
    except ValidationError as e:
        return f"Erreur de validation: {str(e)}"

    texte = texte.lower()
    
    # ===== COMMANDES GIT DE BASE =====
    if "git status" in texte:
        try:
            result = subprocess.run(["git", "status"], capture_output=True, text=True)
            return f"Statut Git :\n{result.stdout[:500]}..."  # Limiter la sortie
        except subprocess.SubprocessError:
            return "Erreur lors de l'exécution de git status"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors de l'accès au dépôt Git"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    elif "git init" in texte:
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            return "Dépôt Git initialisé"
        except subprocess.SubprocessError:
            return "Erreur lors de l'initialisation du dépôt Git"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors de l'initialisation du dépôt"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    elif "git clone" in texte:
        # Extraire l'URL du dépôt
        match = re.search(r"git clone\s+(https?://\S+|git@\S+)", texte)
        if match:
            repo_url = match.group(1)
            if not validate_git_url(repo_url):
                return "URL Git non autorisée ou invalide"
            try:
                subprocess.run(["git", "clone", repo_url], check=True, capture_output=True)
                return f"Dépôt cloné depuis {repo_url}"
            except subprocess.SubprocessError as e:
                return f"Erreur lors du clonage: {str(e)}"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du clonage du dépôt"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            return "URL du dépôt non spécifiée"
    
    # ===== COMMANDES DE STAGING ET COMMIT =====
    elif "git add" in texte:
        if "git add tout" in texte or "git add all" in texte:
            try:
                subprocess.run(["git", "add", "."], check=True, capture_output=True)
                return "Tous les fichiers ajoutés au staging"
            except subprocess.SubprocessError:
                return "Erreur lors de l'ajout des fichiers"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'ajout des fichiers"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            # Extraire le nom du fichier
            match = re.search(r"git add\s+(\S+)", texte)
            if match:
                file_name = match.group(1)
                try:
                    subprocess.run(["git", "add", file_name], check=True, capture_output=True)
                    return f"Fichier {file_name} ajouté au staging"
                except subprocess.SubprocessError:
                    return f"Erreur lors de l'ajout de {file_name}"
                except FileNotFoundError:
                    return "Git n'est pas installé sur ce système"
                except PermissionError:
                    return f"Permission refusée lors de l'ajout de {file_name}"
                except OSError as e:
                    return f"Erreur système: {str(e)}"
            else:
                return "Nom de fichier non spécifié"
    
    elif "git commit" in texte:
        # Extraire le message de commit
        match = re.search(r"git commit\s+(?:avec message|message)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            commit_msg = match.group(1).strip()
            try:
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
                return f"Commit effectué avec le message : {commit_msg}"
            except subprocess.SubprocessError:
                return "Erreur lors du commit"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du commit"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            # Si pas de message spécifié, ouvrir l'éditeur de commit
            try:
                subprocess.run(["git", "commit"], check=True, capture_output=True)
                return "Éditeur de commit ouvert"
            except subprocess.SubprocessError:
                return "Erreur lors de l'ouverture de l'éditeur de commit"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'ouverture de l'éditeur de commit"
            except OSError as e:
                return f"Erreur système: {str(e)}"
    
    # ===== COMMANDES DE SYNCHRONISATION =====
    elif "git pull" in texte:
        try:
            result = subprocess.run(["git", "pull"], capture_output=True, text=True, check=True)
            return f"Pull effectué :\n{result.stdout[:500]}..."
        except subprocess.SubprocessError:
            return "Erreur lors du pull"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors du pull"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    elif "git push" in texte:
        try:
            result = subprocess.run(["git", "push"], capture_output=True, text=True, check=True)
            return f"Push effectué :\n{result.stdout[:500]}..."
        except subprocess.SubprocessError:
            return "Erreur lors du push"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors du push"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    # ===== COMMANDES DE BRANCHES =====
    elif "git branch" in texte:
        if "crée" in texte or "nouvelle" in texte or "créer" in texte:
            # Extraire le nom de la branche
            match = re.search(r"branch\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?$", texte)
            if match:
                branch_name = match.group(1).strip()
                if not validate_branch_name(branch_name):
                    return "Nom de branche invalide ou non autorisé"
                try:
                    subprocess.run(["git", "branch", branch_name], check=True, capture_output=True)
                    return f"Branche {branch_name} créée"
                except subprocess.SubprocessError:
                    return f"Erreur lors de la création de la branche {branch_name}"
                except FileNotFoundError:
                    return "Git n'est pas installé sur ce système"
                except PermissionError:
                    return f"Permission refusée lors de la création de la branche {branch_name}"
                except OSError as e:
                    return f"Erreur système: {str(e)}"
            else:
                return "Nom de branche non spécifié"
        elif "liste" in texte or "affiche" in texte:
            try:
                result = subprocess.run(["git", "branch"], capture_output=True, text=True, check=True)
                return f"Branches :\n{result.stdout}"
            except subprocess.SubprocessError:
                return "Erreur lors de l'affichage des branches"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'accès aux branches"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            try:
                result = subprocess.run(["git", "branch"], capture_output=True, text=True, check=True)
                return f"Branches :\n{result.stdout}"
            except subprocess.SubprocessError:
                return "Erreur lors de l'affichage des branches"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'accès aux branches"
            except OSError as e:
                return f"Erreur système: {str(e)}"
    
    elif "git checkout" in texte or "git basculer" in texte or "git changer de branche" in texte:
        # Extraire le nom de la branche
        match = re.search(r"(?:checkout|basculer|changer de branche)\s+(?:vers|sur)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            branch_name = match.group(1).strip()
            if not validate_branch_name(branch_name):
                return "Nom de branche invalide ou non autorisé"
            try:
                subprocess.run(["git", "checkout", branch_name], check=True, capture_output=True)
                return f"Basculé sur la branche {branch_name}"
            except subprocess.SubprocessError:
                return f"Erreur lors du basculement sur {branch_name}"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return f"Permission refusée lors du basculement sur {branch_name}"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            return "Nom de branche non spécifié"
    
    # ===== COMMANDES DE DIFF ET LOG =====
    elif "git diff" in texte:
        try:
            result = subprocess.run(["git", "diff"], capture_output=True, text=True, check=True)
            return f"Différences :\n{result.stdout[:500]}..."
        except subprocess.SubprocessError:
            return "Erreur lors de l'affichage des différences"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors de l'accès aux différences"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    elif "git log" in texte:
        try:
            if "court" in texte or "résumé" in texte:
                result = subprocess.run(["git", "log", "--oneline", "--graph", "--decorate", "-n", "10"],
                                      capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(["git", "log", "-n", "5"], capture_output=True, text=True, check=True)
            return f"Historique des commits :\n{result.stdout[:800]}..."
        except subprocess.SubprocessError:
            return "Erreur lors de l'affichage de l'historique"
        except FileNotFoundError:
            return "Git n'est pas installé sur ce système"
        except PermissionError:
            return "Permission refusée lors de l'accès à l'historique"
        except OSError as e:
            return f"Erreur système: {str(e)}"
    
    # ===== COMMANDES DE STASH =====
    elif "git stash" in texte:
        if "sauvegarder" in texte or "créer" in texte:
            try:
                subprocess.run(["git", "stash", "push"], check=True, capture_output=True)
                return "Modifications mises de côté"
            except subprocess.SubprocessError:
                return "Erreur lors de la mise de côté des modifications"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de la mise de côté des modifications"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        elif "appliquer" in texte:
            try:
                subprocess.run(["git", "stash", "apply"], check=True, capture_output=True)
                return "Modifications réappliquées"
            except subprocess.SubprocessError:
                return "Erreur lors de la réapplication des modifications"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de la réapplication des modifications"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        elif "liste" in texte:
            try:
                result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True, check=True)
                return f"Liste des stash :\n{result.stdout}"
            except subprocess.SubprocessError:
                return "Erreur lors de l'affichage de la liste des stash"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'accès à la liste des stash"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            try:
                subprocess.run(["git", "stash"], check=True, capture_output=True)
                return "Modifications mises de côté"
            except subprocess.SubprocessError:
                return "Erreur lors de la mise de côté des modifications"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de la mise de côté des modifications"
            except OSError as e:
                return f"Erreur système: {str(e)}"
    
    # ===== COMMANDES AVANCÉES =====
    elif "git reset" in texte:
        if "hard" in texte:
            try:
                subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True)
                return "Reset hard effectué"
            except subprocess.SubprocessError:
                return "Erreur lors du reset hard"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du reset hard"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        elif "soft" in texte:
            try:
                subprocess.run(["git", "reset", "--soft", "HEAD~1"], check=True, capture_output=True)
                return "Reset soft effectué (annulation du dernier commit)"
            except subprocess.SubprocessError:
                return "Erreur lors du reset soft"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du reset soft"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            try:
                subprocess.run(["git", "reset"], check=True, capture_output=True)
                return "Reset effectué"
            except subprocess.SubprocessError:
                return "Erreur lors du reset"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du reset"
            except OSError as e:
                return f"Erreur système: {str(e)}"
    
    elif "git merge" in texte:
        # Extraire le nom de la branche
        match = re.search(r"merge\s+(?:avec|de)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            branch_name = match.group(1).strip()
            if not validate_branch_name(branch_name):
                return "Nom de branche invalide ou non autorisé"
            try:
                subprocess.run(["git", "merge", branch_name], check=True, capture_output=True)
                return f"Fusion avec la branche {branch_name} effectuée"
            except subprocess.SubprocessError:
                return f"Erreur lors de la fusion avec {branch_name}"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return f"Permission refusée lors de la fusion avec {branch_name}"
            except OSError as e:
                return f"Erreur système: {str(e)}"
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
                    subprocess.run(["git", "config", "user.name", username], check=True, capture_output=True)
                    return f"Nom d'utilisateur Git configuré : {username}"
                except subprocess.SubprocessError:
                    return "Erreur lors de la configuration du nom d'utilisateur"
                except FileNotFoundError:
                    return "Git n'est pas installé sur ce système"
                except PermissionError:
                    return "Permission refusée lors de la configuration du nom d'utilisateur"
                except OSError as e:
                    return f"Erreur système: {str(e)}"
            else:
                return "Nom d'utilisateur non spécifié"

        elif "email" in texte:
            # Extraire l'email
            match = re.search(r"email\s+(?:à|comme|en)?\s*[:\"]?(.+?)[\"]?$", texte)
            if match:
                email = match.group(1).strip()
                try:
                    subprocess.run(["git", "config", "user.email", email], check=True, capture_output=True)
                    return f"Email Git configuré : {email}"
                except subprocess.SubprocessError:
                    return "Erreur lors de la configuration de l'email"
                except FileNotFoundError:
                    return "Git n'est pas installé sur ce système"
                except PermissionError:
                    return "Permission refusée lors de la configuration de l'email"
                except OSError as e:
                    return f"Erreur système: {str(e)}"
            else:
                return "Email non spécifié"

        elif "affiche" in texte or "montre" in texte:
            try:
                result = subprocess.run(["git", "config", "--list"], capture_output=True, text=True, check=True)
                return f"Configuration Git :\n{result.stdout[:500]}..."
            except subprocess.SubprocessError:
                return "Erreur lors de l'affichage de la configuration"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors de l'accès à la configuration"
            except OSError as e:
                return f"Erreur système: {str(e)}"
    
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
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
                return f"Commit conventionnel effectué : {commit_msg}"
            except subprocess.SubprocessError:
                return "Erreur lors du commit conventionnel"
            except FileNotFoundError:
                return "Git n'est pas installé sur ce système"
            except PermissionError:
                return "Permission refusée lors du commit conventionnel"
            except OSError as e:
                return f"Erreur système: {str(e)}"
        else:
            return "Description du commit non spécifiée"
    
    return None  # Commande non reconnue
