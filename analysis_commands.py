"""
Module pour les commandes d'analyse et de traduction utilisant l'API Mistral
"""

import os
import requests
import json
import re
import importlib.util
from tts_module import ajouter_texte_a_lire
from text_processing import ecrire_texte_avec_accents
from config import (set_translation_mode, get_translation_mode, get_translation_text, 
                   get_target_language, append_translation_text, get_mistral_api_key)

# Vérifier si pyperclip est disponible
has_pyperclip = importlib.util.find_spec("pyperclip") is not None

def appeler_api_mistral(prompt):
    """
    Appelle l'API Mistral avec le prompt donné
    """
    # Récupérer la clé API depuis la configuration
    mistral_api_key = get_mistral_api_key()
    
    # Vérifier si la clé est définie
    if not mistral_api_key:
        # Essayer de forcer la définition des variables d'environnement
        import importlib
        config_module = importlib.import_module("config")
        if hasattr(config_module, "force_set_env_variables"):
            config_module.force_set_env_variables()
            # Récupérer à nouveau la clé
            mistral_api_key = get_mistral_api_key()
    
    # Vérifier à nouveau si la clé est définie
    if not mistral_api_key:
        return "Erreur: Clé API Mistral non configurée. Veuillez la configurer dans les paramètres de l'application."
    
    # Vérifier si la clé est dans l'environnement
    import os
    env_key = os.environ.get("MISTRAL_API_KEY", "")
    if not env_key:
        # Essayer de définir la variable d'environnement
        try:
            os.environ["MISTRAL_API_KEY"] = mistral_api_key
            print(f"Variable d'environnement MISTRAL_API_KEY définie dans appeler_api_mistral")
        except Exception as e:
            print(f"Erreur lors de la définition de la variable d'environnement dans appeler_api_mistral: {e}")
            return f"Erreur: Impossible de définir la variable d'environnement MISTRAL_API_KEY. {str(e)}"
    
    url = "https://api.mistral.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {mistral_api_key}"
    }
    
    data = {
        "model": "mistral-large-latest",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant personnel extrêmement concis. Réponds en 1-3 phrases maximum, de manière claire et directe. Évite toute introduction ou conclusion inutile. Va droit au but."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 250,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            reponse = result["choices"][0]["message"]["content"].strip()
            # S'assurer que la réponse se termine par un point
            if reponse and not reponse.endswith(('.', '!', '?')):
                reponse += '.'
            return reponse
        else:
            return "Désolé, je n'ai pas pu obtenir une réponse."
    
    except requests.exceptions.RequestException as e:
        return f"Erreur lors de la communication avec l'API Mistral: {str(e)}"

def est_commande_analyse(texte):
    """
    Détermine si le texte est une commande d'analyse
    """
    declencheurs = [
        # Commandes directes
        r"^analyse\s+",
        r"^explique[\s-]moi\s+",
        r"^dis[\s-]moi\s+",
        r"^parle[\s-]moi de\s+",
        r"^raconte[\s-]moi\s+",
        r"^informe[\s-]moi sur\s+",
        r"^renseigne[\s-]moi sur\s+",
        r"^donne[\s-]moi des infos sur\s+",
        r"^je veux savoir\s+",
        r"^j'aimerais savoir\s+",
        r"^peux-tu me dire\s+",
        r"^pourrais-tu me dire\s+",
        r"^peux-tu m'expliquer\s+",
        r"^pourrais-tu m'expliquer\s+",
        
        # Pronoms et adverbes interrogatifs
        r"^qu['e]est[\s-]ce que\s+",
        r"^qu['e]est[\s-]ce qu['e]\s+",
        r"^qui est\s+",
        r"^qui sont\s+",
        r"^comment\s+",
        r"^pourquoi\s+",
        r"^quand\s+",
        r"^où\s+",
        r"^d'où\s+",
        r"^lequel\s+",
        r"^laquelle\s+",
        r"^lesquels\s+",
        r"^lesquelles\s+",
        r"^quel\s+",
        r"^quelle\s+",
        r"^quels\s+",
        r"^quelles\s+",
        r"^combien\s+",
        
        # Questions indirectes
        r"^je me demande\s+",
        r"^je voudrais savoir\s+",
        r"^j'aimerais comprendre\s+",
        r"^peux-tu m'aider à comprendre\s+",
        r"^aide-moi à comprendre\s+",
        
        # Demandes d'information spécifiques
        r"^définis\s+",
        r"^défini\s+",
        r"^définition de\s+",
        r"^qu'est-ce qu'un\s+",
        r"^qu'est-ce qu'une\s+",
        r"^c'est quoi\s+",
        r"^signification de\s+",
        r"^sens de\s+",
        r"^explique le concept de\s+",
        r"^explique la notion de\s+"
    ]
    
    for pattern in declencheurs:
        if re.search(pattern, texte.lower()):
            return True
    
    return False

def executer_commande_analyse(texte):
    """
    Exécute une commande d'analyse en utilisant l'API Mistral
    """
    if est_commande_analyse(texte):
        print(f"Analyse en cours: {texte}")
        reponse = appeler_api_mistral(texte)
        
        # Lire la réponse à haute voix
        if reponse and not reponse.startswith("Erreur:"):
            ajouter_texte_a_lire(reponse)
        
        return reponse
    
    return None

def est_commande_debut_traduction(texte):
    """
    Détermine si le texte est une commande pour démarrer le mode traduction
    """
    declencheurs = [
        # Variations avec "traduis"
        r"^traduis en ([\w\s]+)[\.!]?$",
        r"^traduit en ([\w\s]+)[\.!]?$",  # Homonyme
        r"^traduire en ([\w\s]+)[\.!]?$",
        r"^traduction en ([\w\s]+)[\.!]?$",
        r"^tradui en ([\w\s]+)[\.!]?$",  # Erreur de reconnaissance courante
        r"^traduc en ([\w\s]+)[\.!]?$",  # Erreur de reconnaissance courante
        
        # Variations avec "écris/écrit"
        r"^écris en ([\w\s]+)[\.!]?$",
        r"^écrit en ([\w\s]+)[\.!]?$",  # Homonyme
        r"^écrire en ([\w\s]+)[\.!]?$",
        r"^écriture en ([\w\s]+)[\.!]?$",
        
        # Variations avec "commence"
        r"^commence (?:une |la )?traduction en ([\w\s]+)[\.!]?$",
        r"^commencer (?:une |la )?traduction en ([\w\s]+)[\.!]?$",
        r"^débuter (?:une |la )?traduction en ([\w\s]+)[\.!]?$",
        r"^débute (?:une |la )?traduction en ([\w\s]+)[\.!]?$",
        
        # Variations avec "mode"
        r"^mode traduction en ([\w\s]+)[\.!]?$",
        r"^activer (?:le )?mode traduction en ([\w\s]+)[\.!]?$",
        r"^active (?:le )?mode traduction en ([\w\s]+)[\.!]?$",
        
        # Autres formulations
        r"^je veux traduire en ([\w\s]+)[\.!]?$",
        r"^je voudrais traduire en ([\w\s]+)[\.!]?$",
        r"^j'aimerais traduire en ([\w\s]+)[\.!]?$",
        r"^je veux écrire en ([\w\s]+)[\.!]?$",
        r"^je voudrais écrire en ([\w\s]+)[\.!]?$",
        r"^j'aimerais écrire en ([\w\s]+)[\.!]?$"
    ]
    
    for pattern in declencheurs:
        match = re.search(pattern, texte.lower())
        if match:
            langue = match.group(1).strip()
            return langue
    
    return None

def est_commande_traduction(texte):
    """
    Détermine si le texte est une commande de traduction directe
    """
    declencheurs = [
        # Variations avec "traduis"
        r"^traduis en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^traduit en ([\w\s]+?)(?:\s+:)?\s+(.+)$",  # Homonyme
        r"^traduire en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^traduction en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        
        # Variations avec "écris"
        r"^écris en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^écrit en ([\w\s]+?)(?:\s+:)?\s+(.+)$",  # Homonyme
        r"^écrire en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^écriture en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        
        # Variations avec "dis"
        r"^dis en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^dit en ([\w\s]+?)(?:\s+:)?\s+(.+)$",  # Homonyme
        r"^dire en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        
        # Variations avec "convertis"
        r"^convertis en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^convertit en ([\w\s]+?)(?:\s+:)?\s+(.+)$",  # Homonyme
        r"^convertir en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        
        # Variations avec "mets"
        r"^mets en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        r"^met en ([\w\s]+?)(?:\s+:)?\s+(.+)$",  # Homonyme
        r"^mettre en ([\w\s]+?)(?:\s+:)?\s+(.+)$",
        
        # Variations avec "comment dit-on"
        r"^comment dit-on (.+) en ([\w\s]+)[\.!]?$",
        r"^comment on dit (.+) en ([\w\s]+)[\.!]?$",
        
        # Variations avec "comment écrire"
        r"^comment écrire (.+) en ([\w\s]+)[\.!]?$",
        r"^comment écrit-on (.+) en ([\w\s]+)[\.!]?$"
    ]
    
    for pattern in declencheurs:
        match = re.search(pattern, texte.lower())
        if match:
            # Certains patterns ont la langue en premier, d'autres en second
            if "comment dit-on" in pattern or "comment on dit" in pattern or "comment écrire" in pattern or "comment écrit-on" in pattern:
                langue = match.group(2).strip()
                texte_a_traduire = match.group(1).strip()
            else:
                langue = match.group(1).strip()
                texte_a_traduire = match.group(2).strip()
            
            return langue, texte_a_traduire
    
    return None

def est_commande_fin_traduction(texte):
    """
    Détermine si le texte est une commande pour terminer le mode traduction
    """
    phrases_arret = [
        # Variations avec "fin"
        "fin de traduction", "fin de la traduction", "fin traduction", 
        "fin de cette traduction", "fin de ma traduction", "fini de traduire",
        "fini la traduction", "finis la traduction", "finir traduction", 
        "finir la traduction", "finir cette traduction",
        
        # Variations avec "terminer"
        "terminer traduction", "terminer la traduction", "termine traduction", 
        "termine la traduction", "terminé la traduction", "terminé de traduire",
        "terminer cette traduction", "termine cette traduction",
        
        # Variations avec "arrêter"
        "arrêter traduction", "arrêter la traduction", "arrête traduction", 
        "arrête la traduction", "arrêté de traduire", "arrêté la traduction",
        "arrêter cette traduction", "arrête cette traduction",
        
        # Variations avec "stop"
        "stop traduction", "stop la traduction", "stopper traduction", 
        "stopper la traduction", "stop cette traduction",
        
        # Commandes pour traduire
        "traduire maintenant", "traduire tout", "traduire le texte", 
        "traduis maintenant", "traduis tout", "traduis le texte",
        "traduit maintenant", "traduit tout", "traduit le texte",
        
        # Phrases de fin génériques
        "c'est tout", "c'est fini", "c'est terminé", 
        "j'ai fini", "j'ai terminé", "j'ai fini de dicter",
        "j'ai terminé de dicter", "voilà c'est tout", "ça sera tout"
    ]
    
    # Phrases qui doivent correspondre exactement (et non être contenues)
    phrases_exactes = ["c'est bon", "voilà", "terminé", "fini", "ok", "d'accord"]
    
    texte_lower = texte.lower().strip()
    
    # Vérifier si le texte contient une des phrases d'arrêt
    for phrase in phrases_arret:
        if phrase in texte_lower:
            return True
    
    # Vérifier si le texte correspond exactement à une des phrases exactes
    if texte_lower in phrases_exactes:
        return True
    
    return False

def traduire_texte(langue, texte_a_traduire):
    """
    Traduit le texte dans la langue spécifiée en utilisant l'API Mistral
    """
    prompt = f"Traduis le texte suivant en {langue}. Donne uniquement la traduction, sans explications ni commentaires : \"{texte_a_traduire}\""
    
    print(f"Traduction en cours vers {langue}: {texte_a_traduire}")
    traduction = appeler_api_mistral(prompt)
    
    # Nettoyer la traduction (enlever les guillemets si présents)
    traduction = traduction.strip('"\'')
    
    # Copier la traduction dans le presse-papiers
    try:
        import pyperclip
        pyperclip.copy(traduction)
        print(f"Traduction copiée dans le presse-papiers: {traduction}")
    except ImportError:
        print("Module pyperclip non disponible, impossible de copier dans le presse-papiers")
    except Exception as e:
        print(f"Erreur lors de la copie dans le presse-papiers: {str(e)}")
    
    return traduction

def activer_mode_traduction(langue):
    """
    Active le mode traduction pour la langue spécifiée
    """
    set_translation_mode(True, langue)
    message = f"Mode traduction activé en {langue}. Dictez votre texte. Dites 'fin de traduction' quand vous avez terminé."
    # Ne pas lire le message à haute voix pour éviter de perturber l'utilisateur
    # ajouter_texte_a_lire(message)
    return message

def traiter_texte_traduction(texte):
    """
    Traite le texte en mode traduction
    """
    append_translation_text(texte)
    return f"Ajouté au texte à traduire : {texte}"

def terminer_traduction():
    """
    Termine le mode traduction et traduit le texte accumulé
    """
    texte_a_traduire = get_translation_text()
    langue = get_target_language()
    
    if not texte_a_traduire:
        set_translation_mode(False)
        message = "Traduction annulée : aucun texte à traduire."
        # Ne pas lire le message à haute voix
        # ajouter_texte_a_lire(message)
        return message
    
    # Traduire le texte accumulé
    traduction = traduire_texte(langue, texte_a_traduire)
    
    # Écrire la traduction
    ecrire_texte_avec_accents(traduction)
    
    # Désactiver le mode traduction
    set_translation_mode(False)
    
    # Préparer le message de réponse
    reponse = f"Traduit en {langue} : {traduction}"
    
    # Ne pas lire la réponse à haute voix pour éviter de perturber l'utilisateur
    # if traduction and not traduction.startswith("Erreur:"):
    #     ajouter_texte_a_lire(reponse)
    
    return reponse

def executer_commande_traduction(texte):
    """
    Exécute une commande de traduction en utilisant l'API Mistral
    """
    # Nettoyer le texte pour éviter les problèmes de reconnaissance
    texte = texte.strip()
    
    # Si déjà en mode traduction, traiter le texte comme faisant partie de la traduction
    # Cette vérification doit être faite en premier pour éviter d'interpréter des commandes
    # pendant le mode traduction
    if get_translation_mode():
        if est_commande_fin_traduction(texte):
            print(f"Commande de fin de traduction détectée: {texte}")
            return terminer_traduction()
        else:
            return traiter_texte_traduction(texte)
    
    # Vérification rapide pour les commandes de traduction avec "écris/écrit en"
    texte_lower = texte.lower()
    if texte_lower.startswith(("écris en ", "écrit en ", "écrire en ", "écriture en ")):
        langue = texte_lower.split("en ")[1].strip()
        if langue:  # Si la langue est spécifiée
            print(f"Commande de traduction avec 'écris/écrit en' détectée pour la langue: {langue}")
            return activer_mode_traduction(langue)
    
    # Vérification supplémentaire pour les cas où "écris en" n'est pas au début
    for declencheur in ["écris en ", "écrit en ", "écrire en ", "écriture en "]:
        if declencheur in texte_lower:
            parties = texte_lower.split(declencheur, 1)
            if len(parties) > 1:
                langue = parties[1].strip()
                if langue:  # Si la langue est spécifiée
                    print(f"Commande de traduction avec '{declencheur.strip()}' détectée pour la langue: {langue}")
                    return activer_mode_traduction(langue)
    
    # Vérifier si c'est une commande de sélection (à ignorer)
    if texte_lower.endswith('.'):
        texte_lower = texte_lower[:-1].strip()
        
    # Liste des commandes de sélection à ignorer
    commandes_selection = ["tout sélectionner", "sélectionner tout", "sélectionne tout", 
                          "tout sélectionne", "select all", "sélectionnez tout", 
                          "sélectionne le tout", "sélectionner le tout"]
    
    if texte_lower in commandes_selection:
        return None
    
    # Vérification rapide pour les commandes de traduction simples
    if texte_lower.startswith(("traduis en ", "traduit en ", "traduire en ", "traduction en ", 
                              "écris en ", "écrit en ", "écrire en ", "écriture en ")):
        langue = texte_lower.split("en ")[1].strip()
        if langue:  # Si la langue est spécifiée
            print(f"Commande de traduction simple détectée pour la langue: {langue}")
            return activer_mode_traduction(langue)
    
    # Vérifier si c'est une commande pour démarrer le mode traduction
    langue = est_commande_debut_traduction(texte)
    if langue:
        print(f"Commande de début de traduction détectée pour la langue: {langue}")
        return activer_mode_traduction(langue)
    
    # Vérifier si c'est une commande de traduction directe
    resultat = est_commande_traduction(texte)
    if resultat:
        langue, texte_a_traduire = resultat
        print(f"Commande de traduction directe détectée: langue={langue}, texte={texte_a_traduire}")
        traduction = traduire_texte(langue, texte_a_traduire)
        
        # Écrire la traduction
        ecrire_texte_avec_accents(traduction)
        
        # Préparer le message de réponse
        reponse = f"Traduit en {langue} : {traduction}"
        
        # Ne pas lire la réponse à haute voix pour éviter de perturber l'utilisateur
        # if traduction and not traduction.startswith("Erreur:"):
        #     ajouter_texte_a_lire(reponse)
        
        return reponse
    
    # Si aucune commande de traduction n'est reconnue, retourner None
    # pour indiquer que ce n'est pas une commande de traduction
    return None
