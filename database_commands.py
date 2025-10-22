"""
Module de commandes pour les bases de données
"""

import subprocess
import os
import pyautogui
import re
import time
import sqlite3
from text_processing import ecrire_texte_avec_accents

def executer_commande_database(texte):
    """Exécute des commandes liées aux bases de données"""
    texte = texte.lower()
    
    # ===== COMMANDES SQLITE =====
    if "crée base de données sqlite" in texte or "nouvelle base sqlite" in texte:
        # Extraire le nom de la base de données
        match = re.search(r"(?:base de données|base|sqlite)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            db_name = match.group(1).strip()
            if not db_name.endswith('.db'):
                db_name += '.db'
            
            try:
                # Créer une connexion à la base de données (la crée si elle n'existe pas)
                conn = sqlite3.connect(db_name)
                conn.close()
                return f"Base de données SQLite '{db_name}' créée"
            except:
                return f"Erreur lors de la création de la base de données SQLite"
        else:
            return "Nom de base de données non spécifié"
    
    elif "crée table" in texte and "sqlite" in texte:
        # Extraire le nom de la table et de la base de données
        match_table = re.search(r"table\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        match_db = re.search(r"(?:dans|base|sqlite)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        
        if match_table and match_db:
            table_name = match_table.group(1).strip()
            db_name = match_db.group(1).strip()
            if not db_name.endswith('.db'):
                db_name += '.db'
            
            try:
                # Créer une connexion à la base de données
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # Créer une table simple avec un ID et un nom
                cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                conn.commit()
                conn.close()
                
                return f"Table '{table_name}' créée dans la base de données '{db_name}'"
            except Exception as e:
                return f"Erreur lors de la création de la table : {str(e)}"
        else:
            return "Nom de table ou de base de données non spécifié"
    
    elif "exécute requête sqlite" in texte:
        # Extraire la requête et la base de données
        match_query = re.search(r"requête\s+(?:sql)?\s*[:\"]?(.+?)[\"]?(?:\s|dans|$)", texte)
        match_db = re.search(r"(?:dans|base|sqlite)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        
        if match_query and match_db:
            query = match_query.group(1).strip()
            db_name = match_db.group(1).strip()
            if not db_name.endswith('.db'):
                db_name += '.db'
            
            try:
                # Créer une connexion à la base de données
                conn = sqlite3.connect(db_name)
                cursor = conn.cursor()
                
                # Exécuter la requête
                cursor.execute(query)
                
                # Si c'est une requête SELECT, récupérer les résultats
                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    conn.close()
                    
                    # Formater les résultats
                    if results:
                        result_str = "\n".join([str(row) for row in results])
                        return f"Résultats de la requête :\n{result_str}"
                    else:
                        return "La requête n'a retourné aucun résultat"
                else:
                    # Pour les autres types de requêtes (INSERT, UPDATE, DELETE, etc.)
                    conn.commit()
                    conn.close()
                    return f"Requête exécutée avec succès"
            except Exception as e:
                return f"Erreur lors de l'exécution de la requête : {str(e)}"
        else:
            return "Requête ou base de données non spécifiée"
    
    # ===== COMMANDES MYSQL =====
    elif "lance mysql" in texte or "démarre mysql" in texte:
        try:
            # Tenter de démarrer le service MySQL
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "start", "MySQL"])
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mysql", "start"])
            
            return "Service MySQL démarré"
        except:
            return "Erreur lors du démarrage du service MySQL"
    
    elif "arrête mysql" in texte or "stoppe mysql" in texte:
        try:
            # Tenter d'arrêter le service MySQL
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "stop", "MySQL"])
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mysql", "stop"])
            
            return "Service MySQL arrêté"
        except:
            return "Erreur lors de l'arrêt du service MySQL"
    
    elif "exécute script sql" in texte:
        # Extraire le nom du fichier SQL
        match = re.search(r"script\s+(?:sql|nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            sql_file = match.group(1).strip()
            if not sql_file.endswith('.sql'):
                sql_file += '.sql'
            
            # Déterminer le type de base de données
            db_type = "mysql"  # Par défaut
            if "sqlite" in texte:
                db_type = "sqlite"
            elif "postgresql" in texte or "postgres" in texte:
                db_type = "postgresql"
            
            try:
                if db_type == "sqlite":
                    # Extraire le nom de la base de données
                    match_db = re.search(r"(?:dans|base)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_db:
                        db_name = match_db.group(1).strip()
                        if not db_name.endswith('.db'):
                            db_name += '.db'
                        
                        # Lire le contenu du fichier SQL
                        with open(sql_file, 'r', encoding='utf-8') as f:
                            sql_script = f.read()
                        
                        # Exécuter le script
                        conn = sqlite3.connect(db_name)
                        cursor = conn.cursor()
                        cursor.executescript(sql_script)
                        conn.commit()
                        conn.close()
                        
                        return f"Script SQL '{sql_file}' exécuté sur la base SQLite '{db_name}'"
                    else:
                        return "Nom de base de données SQLite non spécifié"
                
                elif db_type == "mysql":
                    # Extraire les informations de connexion
                    user = "root"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()
                    
                    # Exécuter le script avec mysql
                    subprocess.run(["mysql", "-u", user, "-p", f"< {sql_file}"])
                    
                    return f"Script SQL '{sql_file}' exécuté sur MySQL"
                
                elif db_type == "postgresql":
                    # Extraire les informations de connexion
                    user = "postgres"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()
                    
                    # Exécuter le script avec psql
                    subprocess.run(["psql", "-U", user, "-f", sql_file])
                    
                    return f"Script SQL '{sql_file}' exécuté sur PostgreSQL"
            except Exception as e:
                return f"Erreur lors de l'exécution du script SQL : {str(e)}"
        else:
            return "Nom de fichier SQL non spécifié"
    
    # ===== COMMANDES MONGODB =====
    elif "lance mongodb" in texte or "démarre mongodb" in texte:
        try:
            # Tenter de démarrer le service MongoDB
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "start", "MongoDB"])
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mongod", "start"])
            
            return "Service MongoDB démarré"
        except:
            return "Erreur lors du démarrage du service MongoDB"
    
    elif "arrête mongodb" in texte or "stoppe mongodb" in texte:
        try:
            # Tenter d'arrêter le service MongoDB
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "stop", "MongoDB"])
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mongod", "stop"])
            
            return "Service MongoDB arrêté"
        except:
            return "Erreur lors de l'arrêt du service MongoDB"
    
    # ===== COMMANDES DE SAUVEGARDE =====
    elif "sauvegarde base de données" in texte or "exporte base de données" in texte:
        # Déterminer le type de base de données
        db_type = "mysql"  # Par défaut
        if "sqlite" in texte:
            db_type = "sqlite"
        elif "postgresql" in texte or "postgres" in texte:
            db_type = "postgresql"
        elif "mongodb" in texte:
            db_type = "mongodb"
        
        # Extraire le nom de la base de données
        match_db = re.search(r"(?:base de données|base)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match_db:
            db_name = match_db.group(1).strip()
            
            try:
                # Générer un nom de fichier de sauvegarde avec la date
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = f"{db_name}_backup_{timestamp}"
                
                if db_type == "sqlite":
                    if not db_name.endswith('.db'):
                        db_name += '.db'
                    
                    # Copier le fichier de base de données
                    import shutil
                    backup_file += ".db"
                    shutil.copy2(db_name, backup_file)
                    
                    return f"Base de données SQLite '{db_name}' sauvegardée dans '{backup_file}'"
                
                elif db_type == "mysql":
                    backup_file += ".sql"
                    
                    # Extraire les informations de connexion
                    user = "root"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()
                    
                    # Exécuter la sauvegarde avec mysqldump
                    subprocess.run(["mysqldump", "-u", user, "-p", db_name, f"> {backup_file}"])
                    
                    return f"Base de données MySQL '{db_name}' sauvegardée dans '{backup_file}'"
                
                elif db_type == "postgresql":
                    backup_file += ".sql"
                    
                    # Extraire les informations de connexion
                    user = "postgres"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()
                    
                    # Exécuter la sauvegarde avec pg_dump
                    subprocess.run(["pg_dump", "-U", user, "-d", db_name, "-f", backup_file])
                    
                    return f"Base de données PostgreSQL '{db_name}' sauvegardée dans '{backup_file}'"
                
                elif db_type == "mongodb":
                    backup_dir = f"{backup_file}_dir"
                    os.makedirs(backup_dir, exist_ok=True)
                    
                    # Exécuter la sauvegarde avec mongodump
                    subprocess.run(["mongodump", "--db", db_name, "--out", backup_dir])
                    
                    return f"Base de données MongoDB '{db_name}' sauvegardée dans '{backup_dir}'"
            except Exception as e:
                return f"Erreur lors de la sauvegarde de la base de données : {str(e)}"
        else:
            return "Nom de base de données non spécifié"
    
    return None  # Commande non reconnue
