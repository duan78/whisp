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
from input_validation import InputValidator, ValidationError

validator = InputValidator()


def validate_table_name(name: str) -> bool:
    """Validate SQL table names to prevent SQL injection"""
    if not name:
        return False
    # Table names must: start with letter or _, contain only letters/numbers/_$, max 128 chars
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False
    if len(name) > 128:
        return False
    # Reserved keywords check
    reserved = {'select', 'insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate'}
    if name.lower() in reserved:
        return False
    return True


def validate_db_name(name: str) -> bool:
    """Validate database file names"""
    if not name:
        return False
    # Allow alphanumeric, underscore, hyphen, and .db extension
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', name):
        return False
    if '..' in name:  # Prevent path traversal
        return False
    return True


def validate_sql_query(query: str) -> bool:
    """Basic validation for SQL queries"""
    if not query:
        return False
    query_upper = query.strip().upper()
    # Block dangerous operations
    dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'GRANT', 'REVOKE']
    for danger in dangerous:
        if danger in query_upper:
            return False
    return True

def executer_commande_database(texte):
    """Exécute des commandes liées aux bases de données"""
    try:
        # Validate the command before processing
        texte = validator.validate_command(texte)
        texte = texte.lower()
    except ValidationError as e:
        return f"Commande non autorisée: {str(e)}"
    
    # ===== COMMANDES SQLITE =====
    if "crée base de données sqlite" in texte or "nouvelle base sqlite" in texte:
        # Extraire le nom de la base de données
        match = re.search(r"(?:base de données|base|sqlite)\s+(?:nommée|appelée)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
        if match:
            db_name = match.group(1).strip()
            if not db_name.endswith('.db'):
                db_name += '.db'

            # Validate database name
            if not validate_db_name(db_name):
                return "Nom de base de données invalide"

            try:
                # Créer une connexion à la base de données (la crée si elle n'existe pas)
                with sqlite3.connect(db_name) as conn:
                    pass
                return f"Base de données SQLite '{db_name}' créée"
            except (sqlite3.Error, PermissionError) as e:
                return f"Erreur lors de la création de la base de données SQLite : {str(e)}"
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

            # Validate inputs
            if not validate_table_name(table_name):
                return "Nom de table invalide"
            if not validate_db_name(db_name):
                return "Nom de base de données invalide"

            try:
                # Créer une connexion à la base de données avec context manager
                with sqlite3.connect(db_name) as conn:
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

                return f"Table '{table_name}' créée dans la base de données '{db_name}'"
            except sqlite3.OperationalError as e:
                return f"Erreur opérationnelle sur la base de données : {str(e)}"
            except sqlite3.Error as e:
                return f"Erreur lors de la création de la table : {str(e)}"
            except PermissionError:
                return "Permission refusée pour accéder à la base de données"
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

            # Validate inputs
            if not validate_db_name(db_name):
                return "Nom de base de données invalide"

            # Allow SELECT queries and safe INSERT/UPDATE queries
            query_upper = query.strip().upper()
            if not (query_upper.startswith("SELECT") or
                    query_upper.startswith("INSERT") or
                    query_upper.startswith("UPDATE")):
                return "Seules les requêtes SELECT, INSERT et UPDATE sont autorisées"

            try:
                # Créer une connexion à la base de données avec context manager
                with sqlite3.connect(db_name) as conn:
                    cursor = conn.cursor()

                    # Exécuter la requête
                    cursor.execute(query)

                    # Si c'est une requête SELECT, récupérer les résultats
                    if query_upper.startswith("SELECT"):
                        results = cursor.fetchall()

                        # Formater les résultats
                        if results:
                            result_str = "\n".join([str(row) for row in results])
                            return f"Résultats de la requête :\n{result_str}"
                        else:
                            return "La requête n'a retourné aucun résultat"
                    else:
                        # Pour les autres types de requêtes (INSERT, UPDATE, etc.)
                        conn.commit()
                        return f"Requête exécutée avec succès"
            except sqlite3.OperationalError as e:
                return f"Erreur opérationnelle sur la base de données : {str(e)}"
            except sqlite3.DatabaseError as e:
                return f"Erreur dans la requête SQL : {str(e)}"
            except sqlite3.Error as e:
                return f"Erreur lors de l'exécution de la requête : {str(e)}"
            except PermissionError:
                return "Permission refusée pour accéder à la base de données"
        else:
            return "Requête ou base de données non spécifiée"
    
    # ===== COMMANDES MYSQL =====
    elif "lance mysql" in texte or "démarre mysql" in texte:
        try:
            # Tenter de démarrer le service MySQL
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "start", "MySQL"], check=True,
                             capture_output=True, text=True)
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mysql", "start"], check=True,
                             capture_output=True, text=True)

            return "Service MySQL démarré"
        except subprocess.CalledProcessError as e:
            return f"Erreur lors du démarrage du service MySQL : {e.stderr}"
        except FileNotFoundError:
            return "Commande système non trouvée"
        except Exception as e:
            return f"Erreur lors du démarrage du service MySQL : {str(e)}"
    
    elif "arrête mysql" in texte or "stoppe mysql" in texte:
        try:
            # Tenter d'arrêter le service MySQL
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "stop", "MySQL"], check=True,
                             capture_output=True, text=True)
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mysql", "stop"], check=True,
                             capture_output=True, text=True)

            return "Service MySQL arrêté"
        except subprocess.CalledProcessError as e:
            return f"Erreur lors de l'arrêt du service MySQL : {e.stderr}"
        except FileNotFoundError:
            return "Commande système non trouvée"
        except Exception as e:
            return f"Erreur lors de l'arrêt du service MySQL : {str(e)}"
    
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

                        # Validate inputs
                        if not validate_db_name(db_name):
                            return "Nom de base de données invalide"

                        # Validate SQL file path to prevent directory traversal
                        if '..' in sql_file or sql_file.startswith('/'):
                            return "Chemin de fichier SQL non autorisé"

                        try:
                            # Lire le contenu du fichier SQL
                            with open(sql_file, 'r', encoding='utf-8') as f:
                                sql_script = f.read()
                        except FileNotFoundError:
                            return f"Fichier SQL '{sql_file}' non trouvé"
                        except PermissionError:
                            return f"Permission refusée pour lire le fichier '{sql_file}'"

                        # Exécuter le script avec context manager
                        try:
                            with sqlite3.connect(db_name) as conn:
                                cursor = conn.cursor()
                                cursor.executescript(sql_script)
                                conn.commit()

                            return f"Script SQL '{sql_file}' exécuté sur la base SQLite '{db_name}'"
                        except sqlite3.OperationalError as e:
                            return f"Erreur opérationnelle sur la base de données : {str(e)}"
                        except sqlite3.Error as e:
                            return f"Erreur lors de l'exécution du script : {str(e)}"
                    else:
                        return "Nom de base de données SQLite non spécifié"

                elif db_type == "mysql":
                    # Extraire les informations de connexion
                    user = "root"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()

                    # Exécuter le script avec mysql
                    try:
                        result = subprocess.run(["mysql", "-u", user, "-p"],
                                              shell=True, capture_output=True, text=True)
                        if result.returncode != 0:
                            return f"Erreur MySQL : {result.stderr}"
                        return f"Script SQL '{sql_file}' exécuté sur MySQL"
                    except subprocess.CalledProcessError as e:
                        return f"Erreur lors de l'exécution du script MySQL : {e.stderr}"
                    except FileNotFoundError:
                        return "Commande mysql non trouvée"

                elif db_type == "postgresql":
                    # Extraire les informations de connexion
                    user = "postgres"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()

                    # Exécuter le script avec psql
                    try:
                        result = subprocess.run(["psql", "-U", user, "-f", sql_file],
                                              capture_output=True, text=True)
                        if result.returncode != 0:
                            return f"Erreur PostgreSQL : {result.stderr}"
                        return f"Script SQL '{sql_file}' exécuté sur PostgreSQL"
                    except subprocess.CalledProcessError as e:
                        return f"Erreur lors de l'exécution du script PostgreSQL : {e.stderr}"
                    except FileNotFoundError:
                        return "Commande psql non trouvée"
            except Exception as e:
                return f"Erreur lors de l'exécution du script SQL : {str(e)}"
        else:
            return "Nom de fichier SQL non spécifié"
    
    # ===== COMMANDES MONGODB =====
    elif "lance mongodb" in texte or "démarre mongodb" in texte:
        try:
            # Tenter de démarrer le service MongoDB
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "start", "MongoDB"], check=True,
                             capture_output=True, text=True)
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mongod", "start"], check=True,
                             capture_output=True, text=True)

            return "Service MongoDB démarré"
        except subprocess.CalledProcessError as e:
            return f"Erreur lors du démarrage du service MongoDB : {e.stderr}"
        except FileNotFoundError:
            return "Commande système non trouvée"
        except Exception as e:
            return f"Erreur lors du démarrage du service MongoDB : {str(e)}"
    
    elif "arrête mongodb" in texte or "stoppe mongodb" in texte:
        try:
            # Tenter d'arrêter le service MongoDB
            if os.name == 'nt':  # Windows
                subprocess.run(["net", "stop", "MongoDB"], check=True,
                             capture_output=True, text=True)
            else:  # Unix/Linux
                subprocess.run(["sudo", "service", "mongod", "stop"], check=True,
                             capture_output=True, text=True)

            return "Service MongoDB arrêté"
        except subprocess.CalledProcessError as e:
            return f"Erreur lors de l'arrêt du service MongoDB : {e.stderr}"
        except FileNotFoundError:
            return "Commande système non trouvée"
        except Exception as e:
            return f"Erreur lors de l'arrêt du service MongoDB : {str(e)}"
    
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

                    # Validate database name
                    if not validate_db_name(db_name):
                        return "Nom de base de données invalide"

                    # Copier le fichier de base de données
                    import shutil
                    backup_file += ".db"

                    try:
                        shutil.copy2(db_name, backup_file)
                        return f"Base de données SQLite '{db_name}' sauvegardée dans '{backup_file}'"
                    except FileNotFoundError:
                        return f"Base de données '{db_name}' non trouvée"
                    except PermissionError:
                        return "Permission refusée pour copier la base de données"

                elif db_type == "mysql":
                    backup_file += ".sql"

                    # Extraire les informations de connexion
                    user = "root"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()

                    # Exécuter la sauvegarde avec mysqldump
                    try:
                        result = subprocess.run(["mysqldump", "-u", user, "-p", db_name],
                                              shell=True, capture_output=True, text=True)
                        if result.returncode != 0:
                            return f"Erreur MySQL : {result.stderr}"

                        # Write to backup file
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            f.write(result.stdout)

                        return f"Base de données MySQL '{db_name}' sauvegardée dans '{backup_file}'"
                    except subprocess.CalledProcessError as e:
                        return f"Erreur lors de la sauvegarde MySQL : {e.stderr}"
                    except FileNotFoundError:
                        return "Commande mysqldump non trouvée"

                elif db_type == "postgresql":
                    backup_file += ".sql"

                    # Extraire les informations de connexion
                    user = "postgres"  # Par défaut
                    match_user = re.search(r"utilisateur\s+(?:nommé|appelé)?\s*[:\"]?(.+?)[\"]?(?:\s|$)", texte)
                    if match_user:
                        user = match_user.group(1).strip()

                    # Exécuter la sauvegarde avec pg_dump
                    try:
                        result = subprocess.run(["pg_dump", "-U", user, "-d", db_name, "-f", backup_file],
                                              capture_output=True, text=True)
                        if result.returncode != 0:
                            return f"Erreur PostgreSQL : {result.stderr}"
                        return f"Base de données PostgreSQL '{db_name}' sauvegardée dans '{backup_file}'"
                    except subprocess.CalledProcessError as e:
                        return f"Erreur lors de la sauvegarde PostgreSQL : {e.stderr}"
                    except FileNotFoundError:
                        return "Commande pg_dump non trouvée"

                elif db_type == "mongodb":
                    backup_dir = f"{backup_file}_dir"
                    os.makedirs(backup_dir, exist_ok=True)

                    # Exécuter la sauvegarde avec mongodump
                    try:
                        result = subprocess.run(["mongodump", "--db", db_name, "--out", backup_dir],
                                              capture_output=True, text=True)
                        if result.returncode != 0:
                            return f"Erreur MongoDB : {result.stderr}"
                        return f"Base de données MongoDB '{db_name}' sauvegardée dans '{backup_dir}'"
                    except subprocess.CalledProcessError as e:
                        return f"Erreur lors de la sauvegarde MongoDB : {e.stderr}"
                    except FileNotFoundError:
                        return "Commande mongodump non trouvée"
            except Exception as e:
                return f"Erreur lors de la sauvegarde de la base de données : {str(e)}"
        else:
            return "Nom de base de données non spécifié"
    
    return None  # Commande non reconnue
