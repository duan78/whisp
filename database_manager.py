"""
Module de gestion de la base de données SQLite pour l'assistant Whisp
"""
import os
import sqlite3
import json
import datetime
from functools import wraps

# Chemin vers le fichier de base de données
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whisp_data.db")

def ensure_connection(func):
    """Décorateur pour s'assurer qu'une connexion à la base de données est établie"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            return func(conn, *args, **kwargs)
        except sqlite3.Error as e:
            print(f"Erreur SQLite: {e}")
            raise
        finally:
            if conn:
                conn.close()
    return wrapper

def initialize_database():
    """Initialise la base de données avec les tables nécessaires"""
    try:
        # Créer le répertoire parent si nécessaire
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Table pour les alias de commandes
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_aliases (
            id INTEGER PRIMARY KEY,
            command TEXT NOT NULL,
            alias TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Table pour les configurations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # Table pour les préférences utilisateur
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        # Table pour les rappels
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed INTEGER NOT NULL
        )
        ''')
        
        # Table pour les tâches
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
        ''')
        
        # Table pour les raccourcis clavier
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shortcuts (
            id INTEGER PRIMARY KEY,
            os_type TEXT NOT NULL,
            application TEXT NOT NULL,
            command TEXT NOT NULL,
            shortcut TEXT NOT NULL,
            UNIQUE(os_type, application, command)
        )
        ''')
        
        # Table pour les raccourcis vocaux personnalisés
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_shortcuts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            voice_command TEXT NOT NULL UNIQUE,
            action_type TEXT NOT NULL,
            action_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0
        )
        ''')
        
        # Table pour les logs de l'interface web
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS web_logs (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL
        )
        ''')
        
        # Table pour les métriques STT
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stt_metrics (
            engine TEXT NOT NULL,
            metric_key TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (engine, metric_key)
        )
        ''')
        
        # Table pour l'historique des métriques STT
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stt_metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            engine TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            requests INTEGER NOT NULL,
            success INTEGER NOT NULL,
            errors INTEGER NOT NULL,
            avg_latency REAL NOT NULL,
            avg_audio_duration REAL NOT NULL,
            word_count INTEGER NOT NULL,
            char_count INTEGER NOT NULL
        )
        ''')
        
        # Table pour les logs d'erreurs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            traceback TEXT,
            context TEXT
        )
        ''')
        
        # Table pour le cache TTS
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tts_cache (
            hash_key TEXT PRIMARY KEY,
            engine TEXT NOT NULL,
            text_content TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Base de données initialisée: {DB_PATH}")
        return True
    except sqlite3.Error as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

@ensure_connection
def save_command_aliases(conn, aliases_dict):
    """
    Sauvegarde les alias de commandes dans la base de données
    
    Args:
        conn: Connexion à la base de données
        aliases_dict: Dictionnaire des alias par commande
    """
    cursor = conn.cursor()
    
    # Supprimer tous les alias existants
    cursor.execute("DELETE FROM command_aliases")
    
    # Insérer les nouveaux alias
    for command, alias_list in aliases_dict.items():
        for alias in alias_list:
            cursor.execute(
                "INSERT INTO command_aliases (command, alias) VALUES (?, ?)",
                (command, alias)
            )
    
    conn.commit()

@ensure_connection
def load_command_aliases(conn):
    """
    Charge les alias de commandes depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        
    Returns:
        dict: Dictionnaire des alias par commande
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT command, alias FROM command_aliases")
        rows = cursor.fetchall()
        
        aliases_dict = {}
        for row in rows:
            command = row['command']
            alias = row['alias']
            
            if command in aliases_dict:
                aliases_dict[command].append(alias)
            else:
                aliases_dict[command] = [alias]
        
        print(f"Chargement des alias depuis la base de données: {len(aliases_dict)} commandes, {sum(len(aliases) for aliases in aliases_dict.values())} alias")
        return aliases_dict
    except Exception as e:
        print(f"Erreur lors du chargement des alias depuis la base de données: {e}")
        return {}

@ensure_connection
def add_command_alias(conn, command, alias):
    """
    Ajoute un nouvel alias pour une commande
    
    Args:
        conn: Connexion à la base de données
        command: La commande normalisée
        alias: Le nouvel alias à ajouter
        
    Returns:
        bool: True si l'ajout a réussi, False sinon
    """
    try:
        # Vérifier d'abord si l'alias existe déjà pour la même commande
        cursor = conn.cursor()
        cursor.execute(
            "SELECT command FROM command_aliases WHERE alias = ?",
            (alias,)
        )
        row = cursor.fetchone()
        
        if row and row['command'] == command:
            # L'alias existe déjà pour cette commande, considéré comme un succès
            return True
            
        if row:
            # L'alias existe pour une autre commande
            return False
            
        # Ajouter le nouvel alias
        cursor.execute(
            "INSERT INTO command_aliases (command, alias) VALUES (?, ?)",
            (command, alias)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # L'alias existe déjà
        return False
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'alias dans la base de données: {e}")
        return False

@ensure_connection
def remove_command_alias(conn, alias):
    """
    Supprime un alias
    
    Args:
        conn: Connexion à la base de données
        alias: L'alias à supprimer
        
    Returns:
        bool: True si la suppression a réussi, False sinon
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM command_aliases WHERE alias = ?", (alias,))
    conn.commit()
    return cursor.rowcount > 0

@ensure_connection
def save_config(conn, config_dict):
    """
    Sauvegarde les configurations dans la base de données
    
    Args:
        conn: Connexion à la base de données
        config_dict: Dictionnaire des configurations
    """
    cursor = conn.cursor()
    
    # Mettre à jour ou insérer chaque configuration
    for key, value in config_dict.items():
        # Convertir les valeurs non-string en JSON
        if not isinstance(value, str):
            value = json.dumps(value)
            
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()

@ensure_connection
def load_config(conn, key=None):
    """
    Charge les configurations depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        key: Clé spécifique à charger (None pour tout charger)
        
    Returns:
        dict ou str: Dictionnaire des configurations ou valeur spécifique
    """
    cursor = conn.cursor()
    
    if key is not None:
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            value = row['value']
            # Essayer de convertir en JSON si possible
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    else:
        cursor.execute("SELECT key, value FROM config")
        rows = cursor.fetchall()
        
        config_dict = {}
        for row in rows:
            key = row['key']
            value = row['value']
            
            # Essayer de convertir en JSON si possible
            try:
                config_dict[key] = json.loads(value)
            except json.JSONDecodeError:
                config_dict[key] = value
        
        return config_dict

@ensure_connection
def save_user_preference(conn, key, value):
    """
    Sauvegarde une préférence utilisateur
    
    Args:
        conn: Connexion à la base de données
        key: Clé de la préférence
        value: Valeur de la préférence
    """
    # Convertir les valeurs non-string en JSON
    if not isinstance(value, str):
        value = json.dumps(value)
        
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()

@ensure_connection
def load_user_preferences(conn, key=None):
    """
    Charge les préférences utilisateur
    
    Args:
        conn: Connexion à la base de données
        key: Clé spécifique à charger (None pour tout charger)
        
    Returns:
        dict ou str: Dictionnaire des préférences ou valeur spécifique
    """
    cursor = conn.cursor()
    
    if key is not None:
        cursor.execute("SELECT value FROM user_preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            value = row['value']
            # Essayer de convertir en JSON si possible
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    else:
        cursor.execute("SELECT key, value FROM user_preferences")
        rows = cursor.fetchall()
        
        prefs_dict = {}
        for row in rows:
            key = row['key']
            value = row['value']
            
            # Essayer de convertir en JSON si possible
            try:
                prefs_dict[key] = json.loads(value)
            except json.JSONDecodeError:
                prefs_dict[key] = value
        
        return prefs_dict

@ensure_connection
def save_web_log(conn, timestamp, message, type):
    """
    Sauvegarde un log de l'interface web dans la base de données
    
    Args:
        conn: Connexion à la base de données
        timestamp: Horodatage du log
        message: Message du log
        type: Type de log (info, command, response, error, warning)
    """
    cursor = conn.cursor()
    
    # Insérer le log
    cursor.execute(
        "INSERT INTO web_logs (timestamp, message, type) VALUES (?, ?, ?)",
        (timestamp, message, type)
    )
    
    # Limiter le nombre de logs dans la base de données (garder les 1000 plus récents)
    cursor.execute('''
    DELETE FROM web_logs 
    WHERE id NOT IN (
        SELECT id FROM web_logs 
        ORDER BY id DESC 
        LIMIT 1000
    )
    ''')
    
    conn.commit()

@ensure_connection
def get_web_logs(conn, limit=50, type=None):
    """
    Récupère les logs de l'interface web depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        limit: Nombre maximum de logs à récupérer
        type: Type de log à filtrer (None pour tous les types)
        
    Returns:
        list: Liste des logs
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='web_logs'
    ''')
    
    if not cursor.fetchone():
        return []
    
    # Construire la requête en fonction des paramètres
    query = "SELECT timestamp, message, type FROM web_logs"
    params = []
    
    if type:
        query += " WHERE type = ?"
        params.append(type)
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    # Exécuter la requête
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir les résultats en liste de dictionnaires
    logs = []
    for row in rows:
        logs.append({
            "timestamp": row[0],
            "message": row[1],
            "type": row[2]
        })
    
    return logs

@ensure_connection
def save_stt_metric(conn, engine, metric_key, metric_value):
    """
    Sauvegarde une métrique STT dans la base de données
    
    Args:
        conn: Connexion à la base de données
        engine: Moteur STT (speechrecognition, whisper, vosk, whisper_ct2)
        metric_key: Clé de la métrique
        metric_value: Valeur de la métrique
    """
    cursor = conn.cursor()
    
    # Convertir la valeur en chaîne JSON si nécessaire
    if isinstance(metric_value, (list, dict)):
        import json
        metric_value = json.dumps(metric_value)
    else:
        metric_value = str(metric_value)
    
    # Insérer ou mettre à jour la métrique
    cursor.execute(
        "INSERT OR REPLACE INTO stt_metrics (engine, metric_key, metric_value, updated_at) VALUES (?, ?, ?, ?)",
        (engine, metric_key, metric_value, datetime.datetime.now().isoformat())
    )
    
    conn.commit()

@ensure_connection
def get_stt_metrics(conn, engine=None):
    """
    Récupère les métriques STT depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        engine: Moteur STT spécifique à récupérer (None pour tous)
        
    Returns:
        dict: Dictionnaire des métriques par moteur
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='stt_metrics'
    ''')
    
    if not cursor.fetchone():
        return {}
    
    # Construire la requête en fonction des paramètres
    query = "SELECT engine, metric_key, metric_value FROM stt_metrics"
    params = []
    
    if engine:
        query += " WHERE engine = ?"
        params.append(engine)
    
    # Exécuter la requête
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir les résultats en dictionnaire
    metrics = {}
    for row in rows:
        engine_name = row[0]
        key = row[1]
        value = row[2]
        
        if engine_name not in metrics:
            metrics[engine_name] = {}
        
        # Convertir la valeur selon son type
        try:
            import json
            if key in ["latencies", "audio_durations"]:
                metrics[engine_name][key] = json.loads(value)
            elif key in ["requests", "success", "errors", "word_count", "char_count"]:
                metrics[engine_name][key] = int(value)
            elif key in ["avg_latency", "min_latency", "max_latency", "last_latency", 
                        "avg_audio_duration", "last_audio_duration", "words_per_minute", "cost"]:
                metrics[engine_name][key] = float(value)
            else:
                metrics[engine_name][key] = value
        except:
            metrics[engine_name][key] = value
    
    return metrics

@ensure_connection
def save_stt_metrics_history(conn, engine, requests, success, errors, avg_latency, avg_audio_duration, word_count, char_count):
    """
    Sauvegarde un point d'historique des métriques STT
    
    Args:
        conn: Connexion à la base de données
        engine: Moteur STT
        requests: Nombre total de requêtes
        success: Nombre de succès
        errors: Nombre d'erreurs
        avg_latency: Latence moyenne
        avg_audio_duration: Durée audio moyenne
        word_count: Nombre total de mots
        char_count: Nombre total de caractères
    """
    cursor = conn.cursor()
    
    # Insérer un nouveau point d'historique
    cursor.execute(
        """INSERT INTO stt_metrics_history 
           (engine, timestamp, requests, success, errors, avg_latency, avg_audio_duration, word_count, char_count) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (engine, datetime.datetime.now().isoformat(), requests, success, errors, 
         avg_latency, avg_audio_duration, word_count, char_count)
    )
    
    # Limiter le nombre d'entrées d'historique (garder les 100 plus récentes par moteur)
    cursor.execute(
        """DELETE FROM stt_metrics_history 
           WHERE engine = ? AND id NOT IN (
               SELECT id FROM stt_metrics_history 
               WHERE engine = ? 
               ORDER BY timestamp DESC 
               LIMIT 100
           )""",
        (engine, engine)
    )
    
    conn.commit()

@ensure_connection
def get_stt_metrics_history(conn, engine=None, limit=50):
    """
    Récupère l'historique des métriques STT
    
    Args:
        conn: Connexion à la base de données
        engine: Moteur STT spécifique (None pour tous)
        limit: Nombre maximum d'entrées à récupérer
        
    Returns:
        list: Liste des points d'historique
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='stt_metrics_history'
    ''')
    
    if not cursor.fetchone():
        return []
    
    # Construire la requête en fonction des paramètres
    query = "SELECT id, engine, timestamp, requests, success, errors, avg_latency, avg_audio_duration, word_count, char_count FROM stt_metrics_history"
    params = []
    
    if engine:
        query += " WHERE engine = ?"
        params.append(engine)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    # Exécuter la requête
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir les résultats en liste de dictionnaires
    history = []
    for row in rows:
        history.append({
            "id": row[0],
            "engine": row[1],
            "timestamp": row[2],
            "requests": row[3],
            "success": row[4],
            "errors": row[5],
            "avg_latency": row[6],
            "avg_audio_duration": row[7],
            "word_count": row[8],
            "char_count": row[9]
        })
    
    return history

@ensure_connection
def reset_stt_metrics_db(conn):
    """
    Réinitialise toutes les métriques STT dans la base de données
    
    Args:
        conn: Connexion à la base de données
        
    Returns:
        bool: True si la réinitialisation a réussi
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stt_metrics")
    cursor.execute("DELETE FROM stt_metrics_history")
    conn.commit()
    return True

@ensure_connection
def save_error_log(conn, error_id, timestamp, category, severity, message, traceback=None, context=None):
    """
    Sauvegarde un log d'erreur dans la base de données
    
    Args:
        conn: Connexion à la base de données
        error_id: Identifiant unique de l'erreur
        timestamp: Horodatage de l'erreur
        category: Catégorie de l'erreur
        severity: Niveau de gravité
        message: Message d'erreur
        traceback: Traceback de l'erreur
        context: Contexte de l'erreur
    """
    cursor = conn.cursor()
    
    # Convertir le contexte en JSON si nécessaire
    if context and isinstance(context, dict):
        import json
        context = json.dumps(context)
    
    # Insérer l'erreur
    cursor.execute(
        "INSERT OR REPLACE INTO error_logs (id, timestamp, category, severity, message, traceback, context) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (error_id, timestamp, category, severity, message, traceback, context)
    )
    
    conn.commit()

@ensure_connection
def get_error_logs(conn, limit=50, category=None, min_severity=None):
    """
    Récupère les logs d'erreurs depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        limit: Nombre maximum d'erreurs à récupérer
        category: Catégorie d'erreur à filtrer
        min_severity: Niveau de gravité minimum
        
    Returns:
        list: Liste des erreurs
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='error_logs'
    ''')
    
    if not cursor.fetchone():
        return []
    
    # Construire la requête en fonction des paramètres
    query = "SELECT id, timestamp, category, severity, message, traceback, context FROM error_logs"
    params = []
    conditions = []
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    if min_severity:
        conditions.append("severity = ?")
        params.append(min_severity)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    # Exécuter la requête
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir les résultats en liste de dictionnaires
    errors = []
    for row in rows:
        # Convertir le contexte JSON en dictionnaire
        context = None
        if row[6]:
            try:
                import json
                context = json.loads(row[6])
            except:
                context = row[6]
        
        errors.append({
            "id": row[0],
            "timestamp": row[1],
            "category": row[2],
            "severity": row[3],
            "message": row[4],
            "traceback": row[5],
            "context": context
        })
    
    return errors

@ensure_connection
def save_tts_cache(conn, hash_key, engine, text_content, file_path):
    """
    Sauvegarde une entrée dans le cache TTS
    
    Args:
        conn: Connexion à la base de données
        hash_key: Clé de hachage du texte
        engine: Moteur TTS utilisé
        text_content: Contenu du texte
        file_path: Chemin vers le fichier audio
    """
    cursor = conn.cursor()
    
    # Insérer ou mettre à jour l'entrée de cache
    cursor.execute(
        "INSERT OR REPLACE INTO tts_cache (hash_key, engine, text_content, file_path, created_at) VALUES (?, ?, ?, ?, ?)",
        (hash_key, engine, text_content, file_path, datetime.datetime.now().isoformat())
    )
    
    # Limiter la taille du cache (garder les 100 entrées les plus récentes par moteur)
    cursor.execute(
        "DELETE FROM tts_cache WHERE engine = ? AND hash_key NOT IN (SELECT hash_key FROM tts_cache WHERE engine = ? ORDER BY created_at DESC LIMIT 100)",
        (engine, engine)
    )
    
    conn.commit()

@ensure_connection
def get_tts_cache(conn, hash_key, engine):
    """
    Récupère une entrée du cache TTS
    
    Args:
        conn: Connexion à la base de données
        hash_key: Clé de hachage du texte
        engine: Moteur TTS utilisé
        
    Returns:
        str: Chemin vers le fichier audio ou None
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='tts_cache'
    ''')
    
    if not cursor.fetchone():
        return None
    
    # Récupérer l'entrée de cache
    cursor.execute(
        "SELECT file_path FROM tts_cache WHERE hash_key = ? AND engine = ?",
        (hash_key, engine)
    )
    
    row = cursor.fetchone()
    if row and os.path.exists(row[0]):
        return row[0]
    
    return None

@ensure_connection
def save_custom_shortcut(conn, name, voice_command, action_type, action_data):
    """
    Sauvegarde un raccourci vocal personnalisé
    
    Args:
        conn: Connexion à la base de données
        name: Nom descriptif du raccourci
        voice_command: Commande vocale pour déclencher le raccourci
        action_type: Type d'action (keyboard, mouse, app, script, etc.)
        action_data: Données de l'action (JSON ou texte)
        
    Returns:
        int: ID du raccourci créé ou None en cas d'erreur
    """
    try:
        cursor = conn.cursor()
        
        # Convertir action_data en JSON si c'est un dictionnaire
        if isinstance(action_data, dict):
            import json
            action_data = json.dumps(action_data)
        
        # Insérer le raccourci
        cursor.execute(
            """INSERT INTO custom_shortcuts 
               (name, voice_command, action_type, action_data, created_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (name, voice_command.lower(), action_type, action_data, datetime.datetime.now().isoformat())
        )
        
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # La commande vocale existe déjà
        return None
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du raccourci personnalisé: {e}")
        return None

@ensure_connection
def get_custom_shortcuts(conn, action_type=None):
    """
    Récupère les raccourcis vocaux personnalisés
    
    Args:
        conn: Connexion à la base de données
        action_type: Type d'action à filtrer (None pour tous)
        
    Returns:
        list: Liste des raccourcis personnalisés
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='custom_shortcuts'
    ''')
    
    if not cursor.fetchone():
        return []
    
    # Construire la requête en fonction des paramètres
    query = """SELECT id, name, voice_command, action_type, action_data, 
                      created_at, last_used, usage_count 
               FROM custom_shortcuts"""
    params = []
    
    if action_type:
        query += " WHERE action_type = ?"
        params.append(action_type)
    
    query += " ORDER BY name"
    
    # Exécuter la requête
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convertir les résultats en liste de dictionnaires
    shortcuts = []
    for row in rows:
        # Convertir action_data en dictionnaire si c'est du JSON
        action_data = row[4]
        try:
            import json
            action_data = json.loads(action_data)
        except:
            pass
        
        shortcuts.append({
            "id": row[0],
            "name": row[1],
            "voice_command": row[2],
            "action_type": row[3],
            "action_data": action_data,
            "created_at": row[5],
            "last_used": row[6],
            "usage_count": row[7] or 0
        })
    
    return shortcuts

@ensure_connection
def get_custom_shortcut_by_command(conn, voice_command):
    """
    Récupère un raccourci personnalisé par sa commande vocale
    
    Args:
        conn: Connexion à la base de données
        voice_command: Commande vocale à rechercher
        
    Returns:
        dict: Raccourci personnalisé ou None
    """
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute('''
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='custom_shortcuts'
    ''')
    
    if not cursor.fetchone():
        return None
    
    # Rechercher le raccourci
    cursor.execute(
        """SELECT id, name, voice_command, action_type, action_data, 
                  created_at, last_used, usage_count 
           FROM custom_shortcuts 
           WHERE voice_command = ?""",
        (voice_command.lower(),)
    )
    
    row = cursor.fetchone()
    if not row:
        return None
    
    # Convertir action_data en dictionnaire si c'est du JSON
    action_data = row[4]
    try:
        import json
        action_data = json.loads(action_data)
    except:
        pass
    
    return {
        "id": row[0],
        "name": row[1],
        "voice_command": row[2],
        "action_type": row[3],
        "action_data": action_data,
        "created_at": row[5],
        "last_used": row[6],
        "usage_count": row[7] or 0
    }

@ensure_connection
def update_custom_shortcut(conn, shortcut_id, name=None, voice_command=None, action_type=None, action_data=None):
    """
    Met à jour un raccourci personnalisé
    
    Args:
        conn: Connexion à la base de données
        shortcut_id: ID du raccourci à mettre à jour
        name: Nouveau nom (None pour ne pas changer)
        voice_command: Nouvelle commande vocale (None pour ne pas changer)
        action_type: Nouveau type d'action (None pour ne pas changer)
        action_data: Nouvelles données d'action (None pour ne pas changer)
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    try:
        cursor = conn.cursor()
        
        # Construire la requête de mise à jour
        query_parts = []
        params = []
        
        if name is not None:
            query_parts.append("name = ?")
            params.append(name)
        
        if voice_command is not None:
            query_parts.append("voice_command = ?")
            params.append(voice_command.lower())
        
        if action_type is not None:
            query_parts.append("action_type = ?")
            params.append(action_type)
        
        if action_data is not None:
            # Convertir action_data en JSON si c'est un dictionnaire
            if isinstance(action_data, dict):
                import json
                action_data = json.dumps(action_data)
            
            query_parts.append("action_data = ?")
            params.append(action_data)
        
        # Si aucun champ à mettre à jour, retourner True
        if not query_parts:
            return True
        
        # Ajouter l'ID à la fin des paramètres
        params.append(shortcut_id)
        
        # Exécuter la requête
        cursor.execute(
            f"UPDATE custom_shortcuts SET {', '.join(query_parts)} WHERE id = ?",
            params
        )
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        # La commande vocale existe déjà
        return False
    except Exception as e:
        print(f"Erreur lors de la mise à jour du raccourci personnalisé: {e}")
        return False

@ensure_connection
def delete_custom_shortcut(conn, shortcut_id):
    """
    Supprime un raccourci personnalisé
    
    Args:
        conn: Connexion à la base de données
        shortcut_id: ID du raccourci à supprimer
        
    Returns:
        bool: True si la suppression a réussi
    """
    cursor = conn.cursor()
    
    # Supprimer le raccourci
    cursor.execute("DELETE FROM custom_shortcuts WHERE id = ?", (shortcut_id,))
    
    conn.commit()
    return cursor.rowcount > 0

@ensure_connection
def update_custom_shortcut_usage(conn, shortcut_id):
    """
    Met à jour les statistiques d'utilisation d'un raccourci personnalisé
    
    Args:
        conn: Connexion à la base de données
        shortcut_id: ID du raccourci utilisé
        
    Returns:
        bool: True si la mise à jour a réussi
    """
    cursor = conn.cursor()
    
    # Mettre à jour la date de dernière utilisation et le compteur
    cursor.execute(
        """UPDATE custom_shortcuts 
           SET last_used = ?, usage_count = usage_count + 1 
           WHERE id = ?""",
        (datetime.datetime.now().isoformat(), shortcut_id)
    )
    
    conn.commit()
    return cursor.rowcount > 0

@ensure_connection
def save_stt_settings(conn, settings_dict):
    """
    Sauvegarde les paramètres de reconnaissance vocale dans la base de données
    
    Args:
        conn: Connexion à la base de données
        settings_dict: Dictionnaire des paramètres
        
    Returns:
        bool: True si la sauvegarde a réussi
    """
    try:
        cursor = conn.cursor()
        
        # Convertir les valeurs en JSON si nécessaire
        for key, value in settings_dict.items():
            if not isinstance(value, str):
                import json
                settings_dict[key] = json.dumps(value)
        
        # Sauvegarder chaque paramètre
        for key, value in settings_dict.items():
            cursor.execute(
                "INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)",
                (f"stt_setting_{key}", value)
            )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des paramètres STT: {e}")
        return False

@ensure_connection
def load_stt_settings(conn, default_settings=None):
    """
    Charge les paramètres de reconnaissance vocale depuis la base de données
    
    Args:
        conn: Connexion à la base de données
        default_settings: Paramètres par défaut à utiliser si aucun n'est trouvé
        
    Returns:
        dict: Dictionnaire des paramètres
    """
    try:
        cursor = conn.cursor()
        
        # Préparer le dictionnaire de résultats avec les valeurs par défaut
        settings = default_settings.copy() if default_settings else {}
        
        # Récupérer tous les paramètres STT
        cursor.execute("SELECT key, value FROM user_preferences WHERE key LIKE 'stt_setting_%'")
        rows = cursor.fetchall()
        
        for row in rows:
            # Extraire le nom du paramètre sans le préfixe
            param_name = row[0].replace('stt_setting_', '')
            value = row[1]
            
            # Essayer de convertir en type approprié
            try:
                import json
                # Essayer de convertir en JSON
                settings[param_name] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Si ce n'est pas du JSON valide, conserver la valeur telle quelle
                settings[param_name] = value
        
        return settings
    except Exception as e:
        print(f"Erreur lors du chargement des paramètres STT: {e}")
        return default_settings if default_settings else {}

@ensure_connection
def get_db_info(conn):
    """
    Récupère des informations sur la base de données
    
    Args:
        conn: Connexion à la base de données
        
    Returns:
        dict: Informations sur la base de données
    """
    cursor = conn.cursor()
    
    # Récupérer la liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Récupérer le nombre d'entrées dans chaque table
    table_counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_counts[table] = count
        except:
            table_counts[table] = "Erreur"
    
    # Récupérer la taille du fichier de base de données
    import os
    db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    
    # Récupérer la date de dernière modification
    last_modified = None
    if os.path.exists(DB_PATH):
        import datetime
        last_modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(DB_PATH)
        ).strftime('%Y-%m-%d %H:%M:%S')
    
    # Récupérer la version de SQLite
    cursor.execute("SELECT sqlite_version()")
    sqlite_version = cursor.fetchone()[0]
    
    return {
        "path": DB_PATH,
        "size": db_size,
        "size_formatted": f"{db_size / (1024*1024):.2f} MB" if db_size > 0 else "0 MB",
        "tables": tables,
        "table_counts": table_counts,
        "last_modified": last_modified,
        "sqlite_version": sqlite_version
    }

# Initialiser la base de données au chargement du module
initialize_database()
