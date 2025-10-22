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

def executer_commande_fichier(texte):
    """Exécute des commandes de gestion de fichiers"""
    texte = texte.lower()
    
    # ===== CRÉATION DE FICHIERS ET DOSSIERS =====
    if "crée un dossier" in texte or "nouveau dossier" in texte:
        # Extraire le nom du dossier
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_name = match.group(1).strip()
            try:
                os.makedirs(folder_name, exist_ok=True)
                return f"Dossier '{folder_name}' créé"
            except:
                return f"Erreur lors de la création du dossier '{folder_name}'"
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
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("")
                return f"Fichier texte '{file_name}' créé"
            except:
                return f"Erreur lors de la création du fichier '{file_name}'"
        else:
            return "Nom de fichier non spécifié"
    
    # ===== OPÉRATIONS SUR LES FICHIERS =====
    elif "copie le fichier" in texte:
        # Extraire le nom du fichier source et destination
        match_source = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s+vers|\s+dans)", texte)
        match_dest = re.search(r"(?:vers|dans)\s+(?:le dossier|le fichier)?\s*[:\"]?(.+?)[\"]?$", texte)
        
        if match_source and match_dest:
            source = match_source.group(1).strip()
            destination = match_dest.group(1).strip()
            
            try:
                shutil.copy2(source, destination)
                return f"Fichier '{source}' copié vers '{destination}'"
            except:
                return f"Erreur lors de la copie du fichier '{source}' vers '{destination}'"
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
                shutil.move(source, destination)
                return f"Fichier '{source}' déplacé vers '{destination}'"
            except:
                return f"Erreur lors du déplacement du fichier '{source}' vers '{destination}'"
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
                os.rename(source, new_name)
                return f"Fichier '{source}' renommé en '{new_name}'"
            except:
                return f"Erreur lors du renommage du fichier '{source}' en '{new_name}'"
        else:
            return "Source ou nouveau nom non spécifié"
    
    elif "supprime le fichier" in texte:
        # Extraire le nom du fichier
        match = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()
            
            try:
                os.remove(file_name)
                return f"Fichier '{file_name}' supprimé"
            except:
                return f"Erreur lors de la suppression du fichier '{file_name}'"
        else:
            return "Nom de fichier non spécifié"
    
    elif "supprime le dossier" in texte:
        # Extraire le nom du dossier
        match = re.search(r"dossier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            folder_name = match.group(1).strip()
            
            try:
                shutil.rmtree(folder_name)
                return f"Dossier '{folder_name}' supprimé"
            except:
                return f"Erreur lors de la suppression du dossier '{folder_name}'"
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
                with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(folder_name):
                        for file in files:
                            zipf.write(os.path.join(root, file))
                
                return f"Dossier '{folder_name}' compressé en '{zip_name}'"
            except:
                return f"Erreur lors de la compression du dossier '{folder_name}'"
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
                with zipfile.ZipFile(file_name, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                return f"Fichier '{file_name}' décompressé dans '{extract_dir}'"
            except:
                return f"Erreur lors de la décompression du fichier '{file_name}'"
        else:
            return "Nom de fichier non spécifié"
    
    # ===== OUVERTURE DE FICHIERS =====
    elif "ouvre le fichier" in texte:
        # Extraire le nom du fichier
        match = re.search(r"fichier\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?$", texte)
        if match:
            file_name = match.group(1).strip()
            
            try:
                os.startfile(file_name)
                return f"Fichier '{file_name}' ouvert"
            except:
                return f"Erreur lors de l'ouverture du fichier '{file_name}'"
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
            files = os.listdir(folder)
            if not files:
                return f"Aucun fichier dans le dossier '{folder}'"
            
            return f"Fichiers dans '{folder}':\n" + "\n".join(files)
        except:
            return f"Erreur lors de la liste des fichiers dans '{folder}'"
    
    return None  # Commande non reconnue
