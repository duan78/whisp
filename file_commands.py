"""
Module de gestion des fichiers pour l'assistant Whisp
"""

import os
import shutil
import re
import glob
import datetime
import zipfile
import pyautogui
import pyperclip
import subprocess
from input_validation import InputValidator, ValidationError

validator = InputValidator()

def executer_commande_fichier(texte):
    """Exécute des commandes de gestion de fichiers"""
    try:
        validator.validate_command(texte)
    except ValidationError as e:
        return f"Erreur de validation: {str(e)}"

    texte = texte.lower()

    # ===== CRÉATION DE FICHIERS ET DOSSIERS =====
    if "crée un dossier" in texte or "nouveau dossier" in texte:
        # Extraire le nom du dossier
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_name = match.group(1).strip()
            try:
                # Valider et sécuriser le chemin
                safe_path = validator.validate_file_path(folder_name)
                # Créer le dossier dans un répertoire autorisé
                os.makedirs(safe_path, exist_ok=True)
                return f"Dossier '{safe_path}' créé"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur lors de la création du dossier: {str(e)}"
        else:
            return "Nom de dossier non spécifié"

    elif "crée un fichier texte" in texte or "nouveau fichier texte" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:fichier|texte)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()
            if not file_name.endswith('.txt'):
                file_name += '.txt'

            try:
                # Valider et sécuriser le chemin
                safe_path = validator.validate_file_path(file_name)
                # Créer le fichier dans un répertoire autorisé
                with open(safe_path, 'w', encoding='utf-8') as f:
                    f.write("")
                return f"Fichier texte '{safe_path}' créé"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur lors de la création du fichier: {str(e)}"
        else:
            return "Nom de fichier non spécifié"
    
    # Duplicate section removed - was causing issues
    
    # ===== OPÉRATIONS SUR LES FICHIERS =====
    elif "copie le fichier" in texte:
        # Extraire le nom du fichier source et destination
        match_source = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s+vers|\s+dans)", texte)
        match_dest = re.search(r"(?:vers|dans)\s+(?:le dossier|le fichier)?\s*[:\"]?(.+?)[\"]?$", texte)

        if match_source and match_dest:
            source = match_source.group(1).strip()
            destination = match_dest.group(1).strip()

            try:
                # Valider et sécuriser les chemins
                safe_source = validator.validate_file_path(source)
                safe_dest = validator.validate_file_path(destination)

                # Copier le fichier avec les chemins sécurisés
                shutil.copy2(safe_source, safe_dest)
                return f"Fichier copié de '{safe_source}' vers '{safe_dest}'"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Source ou destination non spécifiée"
    
    elif "déplace le fichier" in texte:
        # Extraire le nom du fichier source et destination
        match_source = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s+vers|\s+dans)", texte)
        match_dest = re.search(r"(?:vers|dans)\s+(?:le dossier|le fichier)?\s*[:\"]?(.+?)[\"]?$", texte)

        if match_source and match_dest:
            source = match_source.group(1).strip()
            destination = match_dest.group(1).strip()

            try:
                # Valider et sécuriser les chemins
                safe_source = validator.validate_file_path(source)
                safe_dest = validator.validate_file_path(destination)

                # Déplacer le fichier avec les chemins sécurisés
                shutil.move(safe_source, safe_dest)
                return f"Fichier déplacé de '{safe_source}' vers '{safe_dest}'"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Source ou destination non spécifiée"
    
    elif "renomme le fichier" in texte:
        # Extraire le nom du fichier source et nouveau nom
        match_source = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s+en)", texte)
        match_new = re.search(r"en\s+[:\"]?(.+?)[\"]?$", texte)

        if match_source and match_new:
            source = match_source.group(1).strip()
            new_name = match_new.group(1).strip()

            try:
                # Valider et sécuriser les chemins
                safe_source = validator.validate_file_path(source)
                safe_dest = validator.validate_file_path(new_name)

                # Renommer le fichier avec les chemins sécurisés
                os.rename(safe_source, safe_dest)
                return f"Fichier renommé de '{safe_source}' en '{safe_dest}'"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Source ou nouveau nom non spécifié"
    
    elif "supprime le fichier" in texte:
        # Extraire le nom du fichier
        match = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()

            try:
                # Valider et sécuriser le chemin
                safe_path = validator.validate_file_path(file_name)

                # Supprimer le fichier avec le chemin sécurisé
                os.remove(safe_path)
                return f"Fichier '{safe_path}' supprimé"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Nom de fichier non spécifié"
    
    elif "supprime le dossier" in texte:
        # Extraire le nom du dossier
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_name = match.group(1).strip()

            try:
                # Valider et sécuriser le chemin
                safe_path = validator.validate_file_path(folder_name)

                # Supprimer le dossier avec le chemin sécurisé
                shutil.rmtree(safe_path)
                return f"Dossier '{safe_path}' supprimé"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Nom de dossier non spécifié"
    
    # ===== COMPRESSION ET DÉCOMPRESSION =====
    elif "compresse le dossier" in texte or "zip le dossier" in texte:
        # Extraire le nom du dossier
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_name = match.group(1).strip()
            zip_name = folder_name + ".zip"

            try:
                # Valider et sécuriser les chemins
                safe_folder = validator.validate_file_path(folder_name)
                safe_zip = validator.validate_file_path(zip_name)

                # Compresser le dossier avec les chemins sécurisés
                with zipfile.ZipFile(safe_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(safe_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, os.path.relpath(file_path, safe_folder))

                return f"Dossier '{safe_folder}' compressé en '{safe_zip}'"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Nom de dossier non spécifié"
    
    elif "décompresse le fichier" in texte or "extrait le zip" in texte:
        # Extraire le nom du fichier
        match = re.search(r"(?:fichier|zip)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()
            if not file_name.endswith('.zip'):
                file_name += '.zip'

            extract_dir = os.path.splitext(file_name)[0]

            try:
                # Valider et sécuriser les chemins
                safe_file = validator.validate_file_path(file_name)
                safe_extract_dir = validator.validate_file_path(extract_dir)

                # Décompresser le fichier avec les chemins sécurisés
                with zipfile.ZipFile(safe_file, 'r') as zipf:
                    zipf.extractall(safe_extract_dir)

                return f"Fichier '{safe_file}' décompressé dans '{safe_extract_dir}'"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Nom de fichier non spécifié"
    
    # ===== OUVERTURE DE FICHIERS =====
    elif "ouvre le fichier" in texte:
        # Extraire le nom du fichier
        match = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()

            try:
                # Valider et sécuriser le chemin
                safe_path = validator.validate_file_path(file_name)

                # Ouvrir le fichier avec le chemin sécurisé
                os.startfile(safe_path)
                return f"Fichier '{safe_path}' ouvert"
            except ValidationError as e:
                return f"Chemin non autorisé: {str(e)}"
            except PermissionError:
                return f"Permission refusée pour cette opération"
            except OSError as e:
                return f"Erreur: {str(e)}"
        else:
            return "Nom de fichier non spécifié"
    
    # ===== LISTE DES FICHIERS =====
    elif "liste les fichiers" in texte or "affiche les fichiers" in texte:
        # Extraire le dossier si spécifié
        match = re.search(r"(?:dans le dossier|du dossier)\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        folder = "."  # Dossier courant par défaut
        if match:
            folder = match.group(1).strip()

        try:
            # Valider et sécuriser le chemin
            safe_folder = validator.validate_file_path(folder)

            # Lister les fichiers avec le chemin sécurisé
            files = os.listdir(safe_folder)
            if not files:
                return f"Aucun fichier dans le dossier '{safe_folder}'"

            return f"Fichiers dans '{safe_folder}':\n" + "\n".join(files)
        except ValidationError as e:
            return f"Chemin non autorisé: {str(e)}"
        except PermissionError:
            return f"Permission refusée pour cette opération"
        except OSError as e:
            return f"Erreur: {str(e)}"
    
    return None  # Commande non reconnue
