"""
Module pour gérer les commandes de sortie de l'application
"""

import threading
import time
from config import set_running
from tts_module import ajouter_texte_a_lire, interrompre_lecture, est_commande_arret_tts

# Variables globales pour gérer l'état de confirmation
confirmation_en_cours = False
confirmation_thread = None
confirmation_reponse = None

def est_commande_sortie(texte):
    """Vérifie si le texte est une commande pour quitter l'application"""
    from command_aliases import is_command_alias
    from text_processing import nettoyer_commande
    
    texte_nettoye = nettoyer_commande(texte)
    
    # Vérifier si c'est un alias de la commande "exit"
    if is_command_alias(texte_nettoye, "exit"):
        return True
    
    # Phrases ambiguës à exclure
    phrases_ambigues = [
        "je vais y aller", "je dois y aller", "je dois partir", "je vais partir",
        "je m'en vais", "je m'en va", "je dois m'en aller", "je vais m'en aller",
        "fin de traduction", "terminer traduction", "arrêter traduction", "finir traduction",
        "fin traduction", "stop traduction", "arrête traduction", "termine traduction"
    ]
    
    # Si c'est une phrase ambiguë, ne pas la considérer comme une commande de sortie
    texte_lower = texte.lower().strip()
    if any(phrase == texte_lower for phrase in phrases_ambigues) or any(phrase in texte_lower for phrase in phrases_ambigues):
        return False
    
    return False

def est_confirmation_positive(texte):
    """Vérifie si le texte est une confirmation positive"""
    texte_lower = texte.lower().strip()
    
    # Liste des confirmations positives
    confirmations_positives = [
        "oui", "ouais", "yes", "yep", "ok", "d'accord", "bien sûr", "affirmatif",
        "exactement", "tout à fait", "absolument", "certainement", "correct",
        "c'est ça", "c'est exact", "je confirme", "confirme", "je veux bien"
    ]
    
    # Vérifier si le texte correspond à une confirmation positive
    # Traitement spécial pour les réponses très courtes comme "oui"
    if len(texte_lower) <= 5:
        # Pour les réponses courtes, vérifier si elles sont exactement dans la liste
        # ou si elles commencent par un mot de la liste
        for confirmation in confirmations_positives:
            if texte_lower == confirmation or texte_lower.startswith(confirmation):
                print(f"Confirmation positive courte détectée: '{texte_lower}'")
                return True
    else:
        # Pour les réponses plus longues, utiliser la méthode originale
        for confirmation in confirmations_positives:
            if confirmation in texte_lower or texte_lower == confirmation:
                return True
    
    return False

def est_confirmation_negative(texte):
    """Vérifie si le texte est une confirmation négative"""
    texte_lower = texte.lower().strip()
    
    # Liste des confirmations négatives
    confirmations_negatives = [
        "non", "no", "nope", "pas du tout", "négatif", "jamais", "pas maintenant",
        "plus tard", "annule", "annuler", "cancel", "reste", "rester", "continue",
        "continuer", "ne quitte pas", "ne pas quitter", "ne ferme pas", "ne pas fermer"
    ]
    
    # Vérifier si le texte correspond à une confirmation négative
    for confirmation in confirmations_negatives:
        if confirmation in texte_lower or texte_lower == confirmation:
            return True
    
    return False

def demander_confirmation_sortie():
    """Demande une confirmation vocale avant de quitter l'application"""
    global confirmation_en_cours, confirmation_thread, confirmation_reponse
    
    # Vérifier si une confirmation est déjà en cours
    if confirmation_en_cours:
        return True
    
    # Marquer qu'une confirmation est en cours
    confirmation_en_cours = True
    confirmation_reponse = None
    
    # Interrompre toute lecture TTS en cours
    interrompre_lecture()
    
    # Demander confirmation
    ajouter_texte_a_lire("Voulez-vous vraiment quitter l'assistant? Répondez par oui ou non.")
    
    # Démarrer un thread pour gérer le timeout
    confirmation_thread = threading.Thread(target=_gerer_timeout_confirmation, daemon=True)
    confirmation_thread.start()
    
    return True

def _gerer_timeout_confirmation():
    """Gère le timeout pour la confirmation de sortie"""
    global confirmation_en_cours, confirmation_reponse
    
    # Attendre 15 secondes pour une réponse
    timeout = 15
    start_time = time.time()
    
    while confirmation_en_cours and (time.time() - start_time) < timeout:
        # Vérifier si une réponse a été reçue
        if confirmation_reponse is not None:
            break
        time.sleep(0.1)
    
    # Si aucune réponse n'a été reçue après le timeout
    if confirmation_reponse is None and confirmation_en_cours:
        ajouter_texte_a_lire("Aucune réponse reçue. L'assistant reste actif.")
        confirmation_en_cours = False
    
def traiter_reponse_confirmation(texte):
    """Traite la réponse à la demande de confirmation"""
    global confirmation_en_cours, confirmation_reponse
    
    # Vérifier si une confirmation est en cours
    if not confirmation_en_cours:
        return False
    
    # Vérifier si c'est une commande d'arrêt du TTS
    if est_commande_arret_tts(texte):
        # Ne pas traiter les commandes d'arrêt du TTS comme des réponses
        return True
    
    # Log pour le débogage
    print(f"Traitement de la réponse de confirmation: '{texte}'")
    
    # Vérifier si c'est une confirmation positive
    if est_confirmation_positive(texte):
        confirmation_reponse = True
        confirmation_en_cours = False
        ajouter_texte_a_lire("D'accord, je vais quitter. Au revoir!")
        # Attendre que le message soit lu avant de quitter
        time.sleep(2)
        # Forcer l'arrêt de l'application
        set_running(False)
        # Ajouter un log pour le débogage
        print("Confirmation positive reçue - Arrêt de l'application demandé")
        # Forcer l'arrêt immédiat pour éviter tout problème
        import os
        os._exit(0)
        return True
    
    # Vérifier si c'est une confirmation négative
    if est_confirmation_negative(texte):
        confirmation_reponse = False
        confirmation_en_cours = False
        ajouter_texte_a_lire("D'accord, je reste à votre disposition.")
        return True
    
    # Si ce n'est ni positif ni négatif, demander une réponse claire
    ajouter_texte_a_lire("Je n'ai pas compris. Veuillez répondre par oui ou non.")
    return True
