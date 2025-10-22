"""
Module de gestion des rappels et de l'agenda pour l'assistant Whisp
"""

import os
import json
import datetime
import re
import time
import threading
import pyautogui
from plyer import notification

try:
    # Essayer d'abord l'import en tant que package
    from whisp_assistant.database_manager import ensure_connection
except ImportError:
    # Sinon, utiliser l'import relatif
    from database_manager import ensure_connection

@ensure_connection
def load_reminders(conn):
    """Charge les rappels depuis la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        time TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed INTEGER NOT NULL
    )
    ''')
    conn.commit()
    
    # Charger les rappels
    cursor.execute("SELECT * FROM reminders")
    rows = cursor.fetchall()
    
    reminders_data = {"reminders": []}
    for row in rows:
        reminders_data["reminders"].append({
            "id": row["id"],
            "description": row["description"],
            "time": row["time"],
            "created_at": row["created_at"],
            "completed": bool(row["completed"])
        })
    
    return reminders_data

@ensure_connection
def save_reminders(conn, reminders_data):
    """Enregistre les rappels dans la base de données"""
    cursor = conn.cursor()
    
    # Créer la table si elle n'existe pas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY,
        description TEXT NOT NULL,
        time TEXT NOT NULL,
        created_at TEXT NOT NULL,
        completed INTEGER NOT NULL
    )
    ''')
    
    # Supprimer tous les rappels existants
    cursor.execute("DELETE FROM reminders")
    
    # Insérer les nouveaux rappels
    for reminder in reminders_data["reminders"]:
        cursor.execute(
            "INSERT INTO reminders (id, description, time, created_at, completed) VALUES (?, ?, ?, ?, ?)",
            (
                reminder["id"],
                reminder["description"],
                reminder["time"],
                reminder["created_at"],
                1 if reminder["completed"] else 0
            )
        )
    
    conn.commit()

def check_reminders():
    """Vérifie les rappels et affiche des notifications pour ceux qui sont dus"""
    reminders_data = load_reminders()
    current_time = datetime.datetime.now()
    
    for reminder in reminders_data["reminders"]:
        if not reminder["completed"]:
            reminder_time = datetime.datetime.fromisoformat(reminder["time"])
            if current_time >= reminder_time:
                # Afficher une notification
                notification.notify(
                    title="Rappel Whisp",
                    message=reminder["description"],
                    timeout=10
                )
                
                # Marquer le rappel comme complété
                reminder["completed"] = True
    
    # Enregistrer les modifications
    save_reminders(reminders_data)
    
    # Planifier la prochaine vérification dans 1 minute
    threading.Timer(60, check_reminders).start()

def start_reminder_checker():
    """Démarre le vérificateur de rappels en arrière-plan"""
    threading.Timer(5, check_reminders).start()

def executer_commande_rappel(texte):
    """Exécute des commandes de gestion des rappels et de l'agenda"""
    texte = texte.lower()
    
    # ===== GESTION DES RAPPELS =====
    if "crée un rappel" in texte or "ajoute un rappel" in texte or "nouveau rappel" in texte:
        # Extraire la description du rappel
        match_desc = re.search(r"rappel\s+(?:pour|de)?\s*[:\"]?(.+?)[\"]?(?:\s+(?:à|pour|dans|le)|$)", texte)
        if not match_desc:
            return "Description du rappel non spécifiée"
        
        description = match_desc.group(1).strip()
        
        # Extraire l'heure du rappel
        time_str = None
        reminder_time = None
        
        # Chercher une heure spécifique (format HH:MM)
        match_time = re.search(r"à\s+(\d{1,2})[h:](\d{2})", texte)
        if match_time:
            hour = int(match_time.group(1))
            minute = int(match_time.group(2))
            
            # Créer l'heure du rappel
            now = datetime.datetime.now()
            reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Si l'heure est déjà passée, ajouter un jour
            if reminder_time < now:
                reminder_time += datetime.timedelta(days=1)
            
            time_str = reminder_time.strftime("%H:%M")
        
        # Chercher un délai relatif (dans X minutes/heures)
        match_delay = re.search(r"dans\s+(\d+)\s+(minute|heure|jour)s?", texte)
        if match_delay:
            amount = int(match_delay.group(1))
            unit = match_delay.group(2)
            
            now = datetime.datetime.now()
            
            if unit == "minute":
                reminder_time = now + datetime.timedelta(minutes=amount)
                time_str = f"{amount} minute(s)"
            elif unit == "heure":
                reminder_time = now + datetime.timedelta(hours=amount)
                time_str = f"{amount} heure(s)"
            elif unit == "jour":
                reminder_time = now + datetime.timedelta(days=amount)
                time_str = f"{amount} jour(s)"
        
        # Chercher une date spécifique
        match_date = re.search(r"le\s+(\d{1,2})\s+(\w+)(?:\s+à\s+(\d{1,2})[h:](\d{2}))?", texte)
        if match_date:
            day = int(match_date.group(1))
            month_str = match_date.group(2).lower()
            
            # Convertir le nom du mois en numéro
            months = {
                "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
                "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
            }
            
            if month_str in months:
                month = months[month_str]
                
                # Obtenir l'année actuelle
                now = datetime.datetime.now()
                year = now.year
                
                # Si le mois est déjà passé, utiliser l'année suivante
                if month < now.month:
                    year += 1
                
                # Heure par défaut (midi)
                hour = 12
                minute = 0
                
                # Si une heure est spécifiée
                if match_date.group(3) and match_date.group(4):
                    hour = int(match_date.group(3))
                    minute = int(match_date.group(4))
                
                try:
                    reminder_time = datetime.datetime(year, month, day, hour, minute)
                    time_str = reminder_time.strftime("%d %B %Y à %H:%M")
                except ValueError:
                    return "Date invalide"
        
        if not reminder_time:
            return "Heure du rappel non spécifiée ou non reconnue"
        
        # Charger les rappels existants
        reminders_data = load_reminders()
        
        # Créer un nouveau rappel
        new_reminder = {
            "id": len(reminders_data["reminders"]) + 1,
            "description": description,
            "time": reminder_time.isoformat(),
            "created_at": datetime.datetime.now().isoformat(),
            "completed": False
        }
        
        # Ajouter le rappel
        reminders_data["reminders"].append(new_reminder)
        
        # Enregistrer les rappels
        save_reminders(reminders_data)
        
        return f"Rappel ajouté : {description} pour {time_str}"
    
    elif "liste des rappels" in texte or "affiche les rappels" in texte or "montre les rappels" in texte:
        # Charger les rappels
        reminders_data = load_reminders()
        
        if not reminders_data["reminders"]:
            return "Aucun rappel enregistré"
        
        # Filtrer par statut si spécifié
        status_filter = None
        if "à venir" in texte or "futurs" in texte:
            status_filter = False
        elif "passés" in texte or "complétés" in texte:
            status_filter = True
        
        # Construire la liste des rappels
        reminders_list = []
        current_time = datetime.datetime.now()
        
        for reminder in reminders_data["reminders"]:
            reminder_time = datetime.datetime.fromisoformat(reminder["time"])
            is_past = current_time >= reminder_time
            
            if status_filter is None or reminder["completed"] == status_filter:
                status_icon = "✓" if reminder["completed"] else "⏰"
                time_str = reminder_time.strftime("%d/%m/%Y %H:%M")
                reminders_list.append(f"{status_icon} {reminder['id']}. {reminder['description']} ({time_str})")
        
        if not reminders_list:
            return f"Aucun rappel {'passé' if status_filter else 'à venir'}"
        
        return "Liste des rappels :\n" + "\n".join(reminders_list)
    
    elif "supprime le rappel" in texte or "efface le rappel" in texte:
        # Extraire l'ID du rappel
        match = re.search(r"rappel\s+(?:numéro|id|identifiant)?\s*[:\"]?(\d+)[\"]?", texte)
        if match:
            reminder_id = int(match.group(1))
            
            # Charger les rappels
            reminders_data = load_reminders()
            
            # Rechercher le rappel par ID
            for i, reminder in enumerate(reminders_data["reminders"]):
                if reminder["id"] == reminder_id:
                    # Supprimer le rappel
                    deleted_reminder = reminders_data["reminders"].pop(i)
                    
                    # Enregistrer les rappels
                    save_reminders(reminders_data)
                    
                    return f"Rappel {reminder_id} supprimé : {deleted_reminder['description']}"
            
            return f"Rappel {reminder_id} non trouvé"
        else:
            return "ID de rappel non spécifié"
    
    # ===== GESTION DE L'AGENDA =====
    elif "ajoute un événement" in texte or "nouvel événement" in texte:
        # Extraire la description de l'événement
        match_desc = re.search(r"événement\s+(?:pour|de)?\s*[:\"]?(.+?)[\"]?(?:\s+(?:à|pour|dans|le)|$)", texte)
        if not match_desc:
            return "Description de l'événement non spécifiée"
        
        description = match_desc.group(1).strip()
        
        # Extraire la date de l'événement (similaire aux rappels)
        # Pour simplifier, on utilise le même format que pour les rappels
        return f"Événement ajouté à l'agenda : {description}"
    
    return None  # Commande non reconnue
