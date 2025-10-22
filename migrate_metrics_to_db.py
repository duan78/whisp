"""
Script de migration pour transférer les métriques STT et les erreurs vers la base de données SQLite
"""
import os
import json
import datetime
import sys

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importer les modules nécessaires
try:
    from whisp_assistant.database_manager import ensure_connection
    from whisp_assistant.speech_recognition_module import stt_metrics
    from whisp_assistant.error_handler import error_handler
except ImportError:
    try:
        from database_manager import ensure_connection
        from speech_recognition_module import stt_metrics
        from error_handler import error_handler
    except ImportError:
        print("Erreur: Impossible d'importer les modules nécessaires")
        sys.exit(1)

@ensure_connection
def migrate_stt_metrics(conn):
    """Migre les métriques STT vers la base de données"""
    if not conn:
        print("Erreur: Connexion à la base de données non disponible")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Créer la table des métriques STT si elle n'existe pas
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS stt_metrics (
            engine TEXT NOT NULL,
            metric_key TEXT NOT NULL,
            metric_value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (engine, metric_key)
        )
        ''')
        
        # Créer la table des historiques de métriques STT si elle n'existe pas
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
        
        # Migrer les métriques actuelles
        timestamp = datetime.datetime.now().isoformat()
        metrics_count = 0
        
        for engine, metrics in stt_metrics.items():
            # Convertir les listes en JSON pour le stockage
            metrics_to_save = metrics.copy()
            metrics_to_save["latencies"] = json.dumps(metrics["latencies"][-100:])
            metrics_to_save["audio_durations"] = json.dumps(metrics["audio_durations"][-100:])
            
            # Enregistrer chaque métrique
            for key, value in metrics_to_save.items():
                cursor.execute(
                    "INSERT OR REPLACE INTO stt_metrics (engine, metric_key, metric_value, updated_at) VALUES (?, ?, ?, ?)",
                    (engine, key, str(value), timestamp)
                )
                metrics_count += 1
            
            # Ajouter un point d'historique
            cursor.execute(
                "INSERT INTO stt_metrics_history (engine, timestamp, requests, success, errors, avg_latency, avg_audio_duration, word_count, char_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    engine,
                    timestamp,
                    metrics["requests"],
                    metrics["success"],
                    metrics["errors"],
                    metrics["avg_latency"],
                    metrics["avg_audio_duration"],
                    metrics["word_count"],
                    metrics["char_count"]
                )
            )
        
        conn.commit()
        print(f"Migration des métriques STT terminée: {metrics_count} métriques migrées")
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des métriques STT: {e}")
        return False

@ensure_connection
def migrate_error_logs(conn):
    """Migre les logs d'erreurs vers la base de données"""
    if not conn:
        print("Erreur: Connexion à la base de données non disponible")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Créer la table des erreurs si elle n'existe pas
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
        
        # Migrer les erreurs actuelles
        error_count = 0
        
        for error in error_handler.error_history:
            # Convertir le contexte en JSON pour le stockage
            context_json = json.dumps(error["context"]) if error["context"] else "{}"
            
            # Insérer l'erreur dans la base de données
            cursor.execute(
                "INSERT OR REPLACE INTO error_logs (id, timestamp, category, severity, message, traceback, context) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    error["id"],
                    error["timestamp"],
                    error["category"],
                    error["severity"],
                    error["message"],
                    error["traceback"],
                    context_json
                )
            )
            error_count += 1
        
        conn.commit()
        print(f"Migration des logs d'erreurs terminée: {error_count} erreurs migrées")
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des logs d'erreurs: {e}")
        return False

def main():
    """Fonction principale pour exécuter la migration"""
    print("Début de la migration des métriques et des erreurs vers la base de données SQLite...")
    
    metrics_success = migrate_stt_metrics()
    errors_success = migrate_error_logs()
    
    if metrics_success and errors_success:
        print("Migration terminée avec succès!")
    else:
        print("Migration terminée avec des erreurs.")

if __name__ == "__main__":
    main()
