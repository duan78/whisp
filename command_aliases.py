"""
Module de gestion des alias de commandes pour l'assistant Whisp
"""
try:
    # Essayer d'abord l'import en tant que package
    from whisp_assistant.database_manager import (
        load_command_aliases, save_command_aliases, 
        add_command_alias as db_add_alias, 
        remove_command_alias as db_remove_alias
    )
except ImportError:
    # Sinon, utiliser l'import relatif
    from database_manager import (
        load_command_aliases, save_command_aliases, 
        add_command_alias as db_add_alias, 
        remove_command_alias as db_remove_alias
    )

class CommandAliases:
    """Classe pour gérer les alias de commandes"""
    
    def __init__(self):
        """Initialisation avec les dictionnaires d'alias par catégorie"""
        # Dictionnaire principal des alias par catégorie
        self.aliases = {}
        self.command_lookup = {}
        
        # Charger les alias depuis la base de données
        self._load_and_initialize()
    
    def _load_and_initialize(self):
        """Charge les alias depuis la base de données et initialise les structures de données"""
        try:
            # Charger les alias depuis la base de données
            self.aliases = load_command_aliases() or {}
            
            # Si la base de données est vide, initialiser avec les valeurs par défaut
            if not self.aliases:
                print("Aucun alias trouvé dans la base de données, initialisation avec les valeurs par défaut")
                self.aliases = self._get_default_aliases()
                # Sauvegarder les valeurs par défaut dans la base de données
                save_command_aliases(self.aliases)
            
            # Construire un dictionnaire inversé pour la recherche rapide
            self.command_lookup = {}
            for command, alias_list in self.aliases.items():
                for alias in alias_list:
                    self.command_lookup[alias] = command
                    
            print(f"Initialisation des alias terminée: {len(self.aliases)} commandes, {len(self.command_lookup)} alias")
        except Exception as e:
            print(f"Erreur lors de l'initialisation des alias: {e}")
            # En cas d'erreur, utiliser les valeurs par défaut sans les sauvegarder
            self.aliases = self._get_default_aliases()
            self.command_lookup = {}
            for command, alias_list in self.aliases.items():
                for alias in alias_list:
                    self.command_lookup[alias] = command
    
    def _get_default_aliases(self):
        """Retourne les alias par défaut"""
        return {
            # Commandes générales
            "exit": [
                "quitter", "sortir", "fermer", "arrêter", "au revoir", "bye", 
                "à plus tard", "à bientôt", "termine toi", "termine-toi",
                "quitte l'assistant", "quitter l'assistant", "ferme l'assistant", "fermer l'assistant",
                "arrête l'assistant", "arrêter l'assistant", "éteins l'assistant", "éteindre l'assistant",
                "bonne journée", "bonne soirée", "bonne nuit", "termine le programme", 
                "terminer le programme", "ferme le programme", "fermer le programme", 
                "quitte", "exit", "stop assistant"
            ],
            "select_all": [
                "tout sélectionner", "sélectionner tout", "sélectionne tout", 
                "tout sélectionne", "select all", "sélectionnez tout", 
                "sélectionne le tout", "sélectionner le tout"
            ],
            "screen_context": [
                "contexte", "contexte écran", "décris l'écran", "décris ce que tu vois", 
                "analyse l'écran", "que vois-tu", "décris le contexte", 
                "analyse le contexte de l'écran", "montre-moi ce que tu vois",
                "qu'est-ce que tu vois", "qu'est-ce qu'il y a à l'écran",
                "analyse ce qui est affiché", "décris ce qui est affiché"
            ],
            
            # Commandes de lecture d'écran
            "screen_read": [
                "lis l'écran", "lit l'écran", "lire l'écran",
                "lis le contenu de l'écran", "lit le contenu de l'écran", "lire le contenu de l'écran",
                "lecture d'écran", "lecture de l'écran", "lis ce qui est affiché",
                "lis le texte à l'écran", "lis ce qu'il y a à l'écran"
            ],
            "screen_read_from": [
                "lis l'écran à partir de", "lis à partir de", "lis depuis",
                "lis le texte à partir de", "lis le texte depuis",
                "lis le contenu à partir de", "lis le contenu depuis",
                "lecture à partir de", "lecture depuis",
                "lit l'écran à partir de", "lit à partir de", "lit depuis",
                "lit le texte à partir de", "lit le texte depuis",
                "lit le contenu à partir de", "lit le contenu depuis",
                "lire l'écran à partir de", "lire à partir de", "lire depuis",
                "lire le texte à partir de", "lire le texte depuis",
                "lire le contenu à partir de", "lire le contenu depuis"
            ],
            
            # Commandes de dictée
            "start_dictation": [
                "écris", "écrit", "tape", "saisis", "note", "dictée",
                "commence la dictée", "commencer la dictée", "débute la dictée",
                "débuter la dictée", "active la dictée", "activer la dictée",
                "mode dictée", "passe en mode dictée", "passer en mode dictée",
                "prends note", "prendre note", "écris ce texte", "tape ce texte"
            ],
            "end_dictation": [
                "fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                "fin dictée", "stop dictée", "arrête dictée", "termine dictée",
                "c'est tout", "c'est fini", "j'ai terminé", "c'est bon",
                "fin de la saisie", "fin de la note", "fin de l'écriture"
            ],
            
            # Commandes de traduction
            "start_translation": [
                "traduis", "traduire", "traduction", "mode traduction",
                "commence la traduction", "commencer la traduction",
                "active la traduction", "activer la traduction",
                "passe en mode traduction", "passer en mode traduction",
                "traduis en", "traduire en", "traduction en"
            ],
            "end_translation": [
                "fin de traduction", "terminer traduction", "arrêter traduction",
                "fin traduction", "stop traduction", "arrête traduction", 
                "termine traduction", "quitter la traduction", "quitter traduction"
            ],
            
            # Commandes de navigation
            "go_to_website": [
                "va sur", "aller sur", "ouvre", "ouvrir", "navigue vers", 
                "va à", "aller à", "visite", "visiter", "ouvre le site",
                "ouvrir le site", "va sur le site", "aller sur le site"
            ],
            
            # Commandes de clavier
            "copy": [
                "copier", "copie", "copie ça", "copier ça", "copier le texte",
                "copie le texte", "copie cette sélection", "copier cette sélection"
            ],
            "paste": [
                "coller", "colle", "colle ça", "coller ça", "coller le texte",
                "colle le texte", "colle ici", "coller ici"
            ],
            "cut": [
                "couper", "coupe", "coupe ça", "couper ça", "couper le texte",
                "coupe le texte", "coupe cette sélection", "couper cette sélection"
            ],
            "undo": [
                "annuler", "annule", "annule ça", "annuler ça", "ctrl z",
                "annule la dernière action", "annuler la dernière action",
                "revenir en arrière", "reviens en arrière"
            ],
            "redo": [
                "rétablir", "rétablis", "rétablis ça", "rétablir ça", "ctrl y",
                "refaire", "refais", "refais la dernière action", "refaire la dernière action"
            ],
            "save": [
                "sauvegarder", "sauvegarde", "enregistrer", "enregistre",
                "sauvegarde le document", "sauvegarder le document",
                "enregistre le document", "enregistrer le document",
                "sauvegarde le fichier", "sauvegarder le fichier",
                "enregistre le fichier", "enregistrer le fichier"
            ],
            "select_all": [
                "tout sélectionner", "sélectionner tout", "sélectionne tout",
                "tout sélectionne", "select all", "sélectionnez tout",
                "sélectionne le tout", "sélectionner le tout"
            ],
            "find": [
                "rechercher", "recherche", "chercher", "cherche",
                "trouver", "trouve", "recherche dans la page",
                "cherche dans la page", "trouve dans la page"
            ],
            "print": [
                "imprimer", "imprime", "imprimer le document",
                "imprime le document", "imprimer la page", "imprime la page"
            ],
            
            # Commandes de souris
            "click": [
                "cliquer", "clique", "clic", "click", "appuie",
                "clique ici", "cliquer ici", "appuie ici"
            ],
            "double_click": [
                "double cliquer", "double clique", "double clic", "double click",
                "double-cliquer", "double-clique", "double-clic"
            ],
            "right_click": [
                "clic droit", "clique droit", "cliquer droit", "click droit",
                "clique avec le bouton droit", "cliquer avec le bouton droit",
                "menu contextuel", "ouvre le menu contextuel"
            ],
            "scroll_up": [
                "défiler vers le haut", "défile vers le haut", "scroll up",
                "monte", "monter", "remonter", "remonte"
            ],
            "scroll_down": [
                "défiler vers le bas", "défile vers le bas", "scroll down",
                "descends", "descendre", "descend"
            ],
            "drag": [
                "glisser", "glisse", "faire glisser", "fais glisser",
                "glisser-déposer", "glisse-dépose", "drag"
            ],
            "drop": [
                "déposer", "dépose", "lâcher", "lâche", "drop"
            ],
            
            # Commandes de fenêtre
            "maximize_window": [
                "maximiser", "maximise", "agrandir", "agrandis", "plein écran",
                "maximiser la fenêtre", "maximise la fenêtre",
                "agrandir la fenêtre", "agrandis la fenêtre",
                "mettre en plein écran", "mets en plein écran"
            ],
            "minimize_window": [
                "minimiser", "minimise", "réduire", "réduis",
                "minimiser la fenêtre", "minimise la fenêtre",
                "réduire la fenêtre", "réduis la fenêtre"
            ],
            "close_window": [
                "fermer fenêtre", "ferme fenêtre", "fermer la fenêtre", "ferme la fenêtre",
                "fermer cette fenêtre", "ferme cette fenêtre"
            ],
            "switch_window": [
                "changer de fenêtre", "change de fenêtre", "passer à la fenêtre",
                "passe à la fenêtre", "aller à la fenêtre", "va à la fenêtre",
                "basculer vers", "bascule vers"
            ],
            "move_window": [
                "déplacer la fenêtre", "déplace la fenêtre", "bouger la fenêtre",
                "bouge la fenêtre", "déplacer cette fenêtre", "déplace cette fenêtre"
            ],
            "resize_window": [
                "redimensionner la fenêtre", "redimensionne la fenêtre",
                "changer la taille de la fenêtre", "change la taille de la fenêtre"
            ],
            
            # Commandes de navigation par onglets
            "new_tab": [
                "nouvel onglet", "nouveau onglet", "ouvrir un onglet", "ouvre un onglet",
                "créer un onglet", "crée un onglet", "ajouter un onglet", "ajoute un onglet"
            ],
            "close_tab": [
                "fermer onglet", "ferme onglet", "fermer l'onglet", "ferme l'onglet",
                "fermer cet onglet", "ferme cet onglet"
            ],
            "next_tab": [
                "onglet suivant", "prochain onglet", "onglet d'après",
                "passer à l'onglet suivant", "passe à l'onglet suivant",
                "aller à l'onglet suivant", "va à l'onglet suivant"
            ],
            "previous_tab": [
                "onglet précédent", "onglet d'avant",
                "passer à l'onglet précédent", "passe à l'onglet précédent",
                "aller à l'onglet précédent", "va à l'onglet précédent"
            ],
            "switch_tab": [
                "changer d'onglet", "change d'onglet", "passer à l'onglet",
                "passe à l'onglet", "aller à l'onglet", "va à l'onglet"
            ],
            
            # Commandes système
            "lock_screen": [
                "verrouiller l'écran", "verrouille l'écran", "verrouiller",
                "verrouille", "verrouiller l'ordinateur", "verrouille l'ordinateur"
            ],
            "sleep_mode": [
                "mettre en veille", "mets en veille", "veille",
                "passer en mode veille", "passe en mode veille"
            ],
            "shutdown": [
                "éteindre", "éteins", "arrêter l'ordinateur", "arrête l'ordinateur",
                "éteindre l'ordinateur", "éteins l'ordinateur", "shutdown"
            ],
            "restart": [
                "redémarrer", "redémarre", "redémarrer l'ordinateur",
                "redémarre l'ordinateur", "reboot", "restart"
            ],
            "volume_up": [
                "augmenter le volume", "augmente le volume", "monter le volume",
                "monte le volume", "plus fort", "volume plus fort"
            ],
            "volume_down": [
                "baisser le volume", "baisse le volume", "diminuer le volume",
                "diminue le volume", "moins fort", "volume moins fort"
            ],
            "mute": [
                "couper le son", "coupe le son", "mute", "muet",
                "mettre en sourdine", "mets en sourdine"
            ],
            
            # Commandes de rappels
            "set_reminder": [
                "rappelle-moi", "rappelle moi", "créer un rappel", "crée un rappel",
                "ajouter un rappel", "ajoute un rappel", "définis un rappel",
                "définir un rappel", "programmer un rappel", "programme un rappel"
            ],
            "show_reminders": [
                "afficher les rappels", "affiche les rappels", "montrer les rappels",
                "montre les rappels", "voir les rappels", "vois les rappels",
                "liste des rappels", "liste les rappels"
            ],
            "delete_reminder": [
                "supprimer le rappel", "supprime le rappel", "effacer le rappel",
                "efface le rappel", "enlever le rappel", "enlève le rappel"
            ],
            
            # Commandes TTS
            "stop_tts": [
                "arrête de parler", "arrêter de parler", "stop parole", "stop voix",
                "tais-toi", "silence", "arrête la lecture", "arrêter la lecture",
                "stop lecture", "stop tts", "arrête tts", "arrêter tts"
            ],
            "change_tts_engine": [
                "changer de voix", "change de voix", "changer la voix",
                "change la voix", "utiliser une autre voix", "utilise une autre voix",
                "changer le moteur tts", "change le moteur tts"
            ],
            
            # Commandes STT
            "change_stt_engine": [
                "changer de reconnaissance vocale", "change de reconnaissance vocale",
                "changer le moteur de reconnaissance", "change le moteur de reconnaissance",
                "utiliser un autre moteur", "utilise un autre moteur",
                "changer le moteur stt", "change le moteur stt"
            ],
        }
    
    def get_command_from_alias(self, text):
        """
        Recherche si le texte correspond à un alias connu
        
        Args:
            text (str): Le texte à vérifier
            
        Returns:
            str or None: La commande normalisée ou None si aucune correspondance
        """
        # Vérifier les correspondances exactes
        if text in self.command_lookup:
            return self.command_lookup[text]
            
        # Vérifier les correspondances partielles (pour les commandes comme "va sur X")
        for alias in self.command_lookup:
            if alias.endswith(" ") and text.startswith(alias):
                return self.command_lookup[alias]
        
        return None
    
    def get_aliases_for_command(self, command):
        """
        Récupère tous les alias pour une commande donnée
        
        Args:
            command (str): La commande normalisée
            
        Returns:
            list: Liste des alias pour cette commande
        """
        return self.aliases.get(command, [])
    
    def add_alias(self, command, alias):
        """
        Ajoute un nouvel alias pour une commande
        
        Args:
            command (str): La commande normalisée
            alias (str): Le nouvel alias à ajouter
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        # Vérifier si l'alias existe déjà pour la même commande
        if alias in self.command_lookup and self.command_lookup[alias] == command:
            return True  # Considéré comme un succès si l'alias existe déjà pour cette commande
            
        # Vérifier si l'alias existe déjà pour une autre commande
        if alias in self.command_lookup:
            return False
            
        try:
            # Ajouter l'alias dans la base de données
            if db_add_alias(command, alias):
                # Mettre à jour les dictionnaires en mémoire
                if command in self.aliases:
                    if alias not in self.aliases[command]:
                        self.aliases[command].append(alias)
                else:
                    self.aliases[command] = [alias]
                    
                self.command_lookup[alias] = command
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'alias '{alias}' pour la commande '{command}': {e}")
            return False
    
    def remove_alias(self, alias):
        """
        Supprime un alias
        
        Args:
            alias (str): L'alias à supprimer
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        if alias in self.command_lookup:
            command = self.command_lookup[alias]
            
            try:
                # Supprimer l'alias de la base de données
                if db_remove_alias(alias):
                    # Mettre à jour les dictionnaires en mémoire
                    if command in self.aliases and alias in self.aliases[command]:
                        self.aliases[command].remove(alias)
                    del self.command_lookup[alias]
                    return True
                return False
            except Exception as e:
                print(f"Erreur lors de la suppression de l'alias '{alias}': {e}")
                return False
        return False
    
    def save_to_database(self):
        """Sauvegarde tous les alias dans la base de données"""
        try:
            save_command_aliases(self.aliases)
            print(f"Sauvegarde des alias dans la base de données: {len(self.aliases)} commandes")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des alias dans la base de données: {e}")
            return False
            
    def reload_from_database(self):
        """Recharge les alias depuis la base de données"""
        try:
            # Recharger les alias depuis la base de données
            db_aliases = load_command_aliases() or {}
            
            # Si la base de données est vide, utiliser les valeurs par défaut
            if not db_aliases:
                print("Aucun alias trouvé dans la base de données lors du rechargement, utilisation des valeurs par défaut")
                db_aliases = self._get_default_aliases()
                # Sauvegarder les valeurs par défaut dans la base de données
                save_command_aliases(db_aliases)
            
            self.aliases = db_aliases
            
            # Reconstruire le dictionnaire inversé
            self.command_lookup = {}
            for command, alias_list in self.aliases.items():
                for alias in alias_list:
                    self.command_lookup[alias] = command
                    
            print(f"Rechargement des alias depuis la base de données: {len(self.aliases)} commandes, {len(self.command_lookup)} alias")
            return True
        except Exception as e:
            print(f"Erreur lors du rechargement des alias depuis la base de données: {e}")
            return False

# Instance globale pour l'accès facile
command_aliases = CommandAliases()

def is_command_alias(text, command):
    """
    Vérifie si le texte correspond à un alias pour la commande spécifiée
    
    Args:
        text (str): Le texte à vérifier
        command (str): La commande normalisée à comparer
        
    Returns:
        bool: True si le texte est un alias pour la commande
    """
    normalized_command = command_aliases.get_command_from_alias(text)
    return normalized_command == command

def get_normalized_command(text):
    """
    Récupère la commande normalisée à partir d'un texte
    
    Args:
        text (str): Le texte à normaliser
        
    Returns:
        str or None: La commande normalisée ou None si aucune correspondance
    """
    return command_aliases.get_command_from_alias(text)

def extract_command_parameters(text, command_type):
    """
    Extrait les paramètres d'une commande à partir du texte
    
    Args:
        text (str): Le texte complet de la commande
        command_type (str): Le type de commande normalisé
        
    Returns:
        dict: Dictionnaire des paramètres extraits
    """
    params = {}
    
    # Traitement spécifique selon le type de commande
    if command_type == "go_to_website":
        # Extraire le nom du site web
        for prefix in command_aliases.get_aliases_for_command("go_to_website"):
            if text.lower().startswith(prefix.lower() + " "):
                params["website"] = text[len(prefix) + 1:].strip()
                break
    
    elif command_type == "screen_read_from":
        # Extraire l'élément à partir duquel lire
        for prefix in command_aliases.get_aliases_for_command("screen_read_from"):
            if text.lower().startswith(prefix.lower() + " "):
                params["element"] = text[len(prefix) + 1:].strip()
                break
            
            # Gestion des cas où le préfixe se termine par "de" ou "depuis"
            if prefix.endswith(" de") or prefix.endswith(" depuis"):
                if text.lower().startswith(prefix.lower() + " "):
                    params["element"] = text[len(prefix) + 1:].strip()
                    break
    
    elif command_type == "start_dictation":
        # Extraire le texte initial pour la dictée
        for prefix in command_aliases.get_aliases_for_command("start_dictation"):
            if text.lower().startswith(prefix.lower() + " "):
                initial_text = text[len(prefix) + 1:].strip()
                
                # Enlever les préfixes courants dans le langage naturel
                prefixes_a_supprimer = [
                    "le texte", "le message", "ceci", "ça", "s'il te plait",
                    "s'il vous plait", "pour moi", "ce qui suit", ":"
                ]
                for prefixe in prefixes_a_supprimer:
                    if initial_text.startswith(prefixe):
                        initial_text = initial_text[len(prefixe):].strip()
                
                params["initial_text"] = initial_text
                break
    
    return params
