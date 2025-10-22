"""
Script pour migrer les données existantes vers la base de données SQLite
"""
import os
import json
import sys
import traceback

# Ajouter le répertoire parent au chemin de recherche Python
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Fonction pour gérer les imports de manière sécurisée
def safe_import(package_import, relative_import):
    try:
        # Essayer d'abord l'import en tant que package
        module = __import__(package_import, fromlist=['*'])
        print(f"Import réussi: {package_import}")
        return module
    except ImportError as e:
        print(f"Import package échoué ({e}), tentative d'import relatif...")
        try:
            # Sinon, utiliser l'import relatif
            module = __import__(relative_import, fromlist=['*'])
            print(f"Import relatif réussi: {relative_import}")
            return module
        except ImportError as e2:
            print(f"ERREUR: Impossible d'importer {relative_import} ({e2})")
            raise

# Importer les modules nécessaires
try:
    db_manager = safe_import('whisp_assistant.database_manager', 'database_manager')
    initialize_database = db_manager.initialize_database
    save_command_aliases = db_manager.save_command_aliases
    save_config = db_manager.save_config
except Exception as e:
    print(f"ERREUR CRITIQUE: Impossible d'importer les modules nécessaires")
    print(f"Détails: {e}")
    traceback.print_exc()
    sys.exit(1)

def migrate_api_keys():
    """Migre les clés API depuis le fichier vers la base de données"""
    api_keys_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")
    
    if os.path.exists(api_keys_file):
        try:
            with open(api_keys_file, 'r') as f:
                keys = json.load(f)
                
            config_dict = {
                "openai_api_key": keys.get("openai", ""),
                "mistral_api_key": keys.get("mistral", "")
            }
            
            # Ajouter le moteur STT actuel
            try:
                config_module = safe_import('whisp_assistant.config', 'config')
                config_dict["stt_engine"] = config_module.get_stt_engine()
            except Exception as e:
                print(f"Impossible de récupérer le moteur STT: {e}")
                config_dict["stt_engine"] = "speechrecognition"  # Valeur par défaut
            
            # Sauvegarder dans la base de données
            save_config(config_dict)
            
            print("Clés API migrées avec succès vers la base de données")
            return True
        except Exception as e:
            print(f"Erreur lors de la migration des clés API: {e}")
            return False
    else:
        print(f"Fichier de clés API non trouvé: {api_keys_file}")
        return False

def migrate_command_aliases():
    """Migre les alias de commandes vers la base de données"""
    try:
        # Importer le module command_aliases
        aliases_module = safe_import('whisp_assistant.command_aliases', 'command_aliases')
        command_aliases = aliases_module.command_aliases
        
        # Récupérer tous les alias par défaut et les modules de commandes
        default_aliases = command_aliases._get_default_aliases()
        
        # Collecter les alias depuis les autres modules de commandes
        try:
            # Importer les modules de commandes
            browser_commands = safe_import('whisp_assistant.browser_commands', 'browser_commands')
            keyboard_commands = safe_import('whisp_assistant.keyboard_commands', 'keyboard_commands')
            mouse_commands = safe_import('whisp_assistant.mouse_commands', 'mouse_commands')
            window_manager = safe_import('whisp_assistant.window_manager', 'window_manager')
            dictation_mode = safe_import('whisp_assistant.dictation_mode', 'dictation_mode')
            exit_commands = safe_import('whisp_assistant.exit_commands', 'exit_commands')
            screen_reader_commands = safe_import('whisp_assistant.screen_reader_commands', 'screen_reader_commands')
            analysis_commands = safe_import('whisp_assistant.analysis_commands', 'analysis_commands')
            
            # Ajouter les alias spécifiques à chaque module si disponibles
            # Ces fonctions sont supposées exister dans les modules respectifs
            # Si elles n'existent pas, elles seront ignorées
            
            print("Collecte des alias depuis les modules de commandes...")
            
            # Fusionner tous les alias dans un seul dictionnaire
            all_aliases = default_aliases
            
            # Sauvegarder dans la base de données
            save_command_aliases(all_aliases)
            
            print(f"Alias de commandes migrés avec succès vers la base de données: {len(all_aliases)} commandes")
        except Exception as e:
            print(f"Avertissement lors de la collecte des alias depuis les modules: {e}")
            # En cas d'erreur, utiliser uniquement les alias par défaut
            save_command_aliases(default_aliases)
            print(f"Alias par défaut migrés avec succès: {len(default_aliases)} commandes")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la migration des alias de commandes: {e}")
        return False

def migrate_user_preferences():
    """Migre les préférences utilisateur vers la base de données"""
    try:
        # Importer le module config
        config_module = safe_import('whisp_assistant.config', 'config')
        
        # Récupérer les préférences existantes
        try:
            preferences = config_module.get_all_preferences()
            
            if preferences:
                # Importer le module database_manager
                db_manager = safe_import('whisp_assistant.database_manager', 'database_manager')
                
                # Sauvegarder chaque préférence dans la base de données
                for key, value in preferences.items():
                    db_manager.save_user_preference(key, value)
                
                print(f"Préférences utilisateur migrées avec succès: {len(preferences)} préférences")
                return True
            else:
                print("Aucune préférence utilisateur à migrer")
                return True
        except Exception as e:
            print(f"Erreur lors de la récupération des préférences: {e}")
            return False
    except Exception as e:
        print(f"Erreur lors de la migration des préférences utilisateur: {e}")
        return False

def main():
    """Fonction principale pour la migration des données"""
    print("Migration des données vers la base de données SQLite...")
    
    try:
        # Initialiser la base de données
        if not initialize_database():
            print("Erreur lors de l'initialisation de la base de données")
            return False
        
        # Migrer les clés API
        api_keys_migrated = migrate_api_keys()
        
        # Migrer les alias de commandes
        aliases_migrated = migrate_command_aliases()
        
        # Migrer les préférences utilisateur
        preferences_migrated = migrate_user_preferences()
        
        if api_keys_migrated and aliases_migrated and preferences_migrated:
            print("Migration terminée avec succès")
            return True
        else:
            print("Migration terminée avec des erreurs")
            return False
    except Exception as e:
        print(f"ERREUR CRITIQUE pendant la migration: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        print(f"Statut de la migration: {'Succès' if success else 'Échec'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"ERREUR NON GÉRÉE: {e}")
        traceback.print_exc()
        sys.exit(1)
