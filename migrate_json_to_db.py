"""
Script de migration pour transférer les données des fichiers JSON vers la base de données SQLite
"""
import os
import json
import datetime
from database_manager import ensure_connection

# Fichiers JSON à migrer
REMINDERS_FILE = "whisp_reminders.json"
TASKS_FILE = "whisp_tasks.json"

def migrate_reminders():
    """Migre les rappels du fichier JSON vers la base de données"""
    if not os.path.exists(REMINDERS_FILE):
        print(f"Fichier de rappels non trouvé: {REMINDERS_FILE}")
        return False
    
    try:
        # Charger les rappels depuis le fichier JSON
        with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
            reminders_data = json.load(f)
        
        if not reminders_data or "reminders" not in reminders_data:
            print("Aucun rappel à migrer")
            return True
        
        @ensure_connection
        def save_to_db(conn):
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
            
            # Insérer les rappels depuis le fichier JSON
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
            return len(reminders_data["reminders"])
        
        count = save_to_db()
        print(f"Migration des rappels terminée: {count} rappels migrés")
        
        # Renommer le fichier JSON original pour éviter les conflits
        backup_file = f"{REMINDERS_FILE}.bak"
        os.rename(REMINDERS_FILE, backup_file)
        print(f"Fichier original renommé en {backup_file}")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des rappels: {e}")
        return False

def migrate_tasks():
    """Migre les tâches du fichier JSON vers la base de données"""
    if not os.path.exists(TASKS_FILE):
        print(f"Fichier de tâches non trouvé: {TASKS_FILE}")
        return False
    
    try:
        # Charger les tâches depuis le fichier JSON
        with open(TASKS_FILE, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        if not tasks_data or "tasks" not in tasks_data:
            print("Aucune tâche à migrer")
            return True
        
        @ensure_connection
        def save_to_db(conn):
            cursor = conn.cursor()
            
            # Créer la table si elle n'existe pas
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            ''')
            
            # Supprimer toutes les tâches existantes
            cursor.execute("DELETE FROM tasks")
            
            # Insérer les tâches depuis le fichier JSON
            for task in tasks_data["tasks"]:
                cursor.execute(
                    "INSERT INTO tasks (id, description, status, created_at, completed_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        task["id"],
                        task["description"],
                        task["status"],
                        task["created_at"],
                        task["completed_at"]
                    )
                )
            
            conn.commit()
            return len(tasks_data["tasks"])
        
        count = save_to_db()
        print(f"Migration des tâches terminée: {count} tâches migrées")
        
        # Renommer le fichier JSON original pour éviter les conflits
        backup_file = f"{TASKS_FILE}.bak"
        os.rename(TASKS_FILE, backup_file)
        print(f"Fichier original renommé en {backup_file}")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des tâches: {e}")
        return False

def main():
    """Fonction principale pour exécuter la migration"""
    print("Début de la migration des données JSON vers la base de données SQLite...")
    
    reminders_success = migrate_reminders()
    tasks_success = migrate_tasks()
    
    if reminders_success and tasks_success:
        print("Migration terminée avec succès!")
    else:
        print("Migration terminée avec des erreurs.")

if __name__ == "__main__":
    main()
