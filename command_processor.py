"""
Module de traitement central des commandes pour l'assistant Whisp
"""

import time
import re
import sys
import traceback

# Importer les fonctions de l'interface web
try:
    from web_interface import command_to_web, response_to_web, log_to_web
    web_interface_available = True
except ImportError:
    web_interface_available = False
    print("Interface web non disponible")
from config import get_dictation_mode, get_dictated_text, get_translation_mode
from text_processing import ecrire_texte_avec_accents, nettoyer_commande, normaliser_commande

# Import des optimisations Numba
try:
    from math_optimization import calculate_text_similarity, fuzzy_search, math_optimizer
    NUMBA_MATH_AVAILABLE = True
except ImportError as e:
    print(f"Numba math non disponible, utilisation des fonctions standards: {e}")
    NUMBA_MATH_AVAILABLE = False
from command_aliases import is_command_alias
from exit_commands import est_commande_sortie, demander_confirmation_sortie, traiter_reponse_confirmation
from dictation_mode import traiter_dictee, traiter_commande_ecriture
from keyboard_commands import executer_commande_clavier
from mouse_commands import executer_commande_souris
from system_commands import executer_commande_systeme
from browser_commands import executer_commande_navigateur
from productivity_commands import executer_commande_productivite
from window_manager import executer_commande_fenetre
from git_commands import executer_commande_git
from dev_environment_commands import executer_commande_dev
from project_management_commands import executer_commande_projet
from web_dev_commands import executer_commande_web_dev
from database_commands import executer_commande_database
from reminder_commands import executer_commande_rappel, start_reminder_checker
from search_commands import executer_commande_recherche
from file_commands import executer_commande_fichier
from screen_context import decrire_contexte_ecran
from accessibility_commands import executer_commande_accessibilite
from analysis_commands import executer_commande_analyse, executer_commande_traduction
from tts_module import est_commande_arret_tts, interrompre_lecture
from screen_reader import lire_ecran_intelligemment
from screen_reader_commands import est_commande_lecture_ecran, executer_commande_lecture_ecran
from shortcuts_database import executer_raccourci_personnalise
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity, catch_errors

# Obtenir l'instance du gestionnaire d'erreurs
error_handler = get_error_handler()

class CommandProcessor:
    """Classe de traitement des commandes vocales"""
    
    def __init__(self):
        """Initialisation du processeur de commandes"""
        # Démarrer le vérificateur de rappels
        start_reminder_checker()
    
    @catch_errors(category=ErrorCategory.COMMAND_PROCESSING, severity=ErrorSeverity.HIGH)
    def process_command(self, texte):
        """Traite une commande vocale et retourne le résultat"""
        # Enregistrer la commande dans l'interface web si disponible
        if web_interface_available:
            command_to_web(texte)
        
        try:
            # Vérifier si c'est une réponse à une demande de confirmation de sortie
            from exit_commands import confirmation_en_cours
            if confirmation_en_cours:
                if traiter_reponse_confirmation(texte):
                    return "Traitement de la confirmation de sortie"
                
            # Vérifier d'abord si c'est une commande d'arrêt du TTS
            if est_commande_arret_tts(texte):
                interrompre_lecture()
                # Retourner None pour que l'assistant continue d'écouter
                # sans donner de réponse qui serait lue par le TTS
                return None
            
            # Si en mode traduction, traiter en priorité
            if get_translation_mode():
                try:
                    resultat = executer_commande_traduction(texte)
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat)
                    return resultat
                except Exception as e:
                    error_msg = f"Erreur lors de l'exécution de la commande de traduction: {str(e)}"
                    print(error_msg)
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        context={"mode": "traduction", "texte": texte}
                    )
                    if web_interface_available:
                        log_to_web("Erreur lors de la traduction. Veuillez réessayer.", "error")
                    return "Erreur lors de la traduction. Veuillez réessayer."
            
            # Vérifier si c'est une commande pour quitter l'assistant
            if est_commande_sortie(texte):
                print(f"Commande de sortie détectée: '{texte}'")
                demander_confirmation_sortie()
                return "Demande de confirmation pour quitter l'assistant..."
                
            # Vérifier si c'est une commande de sélection (prioritaire)
            try:
                commande_normalisee, parametres = normaliser_commande(texte)
                
                if commande_normalisee == "select_all":
                    resultat = executer_commande_clavier("sélectionner tout")
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat)
                    return resultat
            except Exception as e:
                error_msg = f"Erreur lors de la normalisation de la commande: {str(e)}"
                print(error_msg)
                error_handler.handle_error(
                    e,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.LOW,
                    context={"action": "normalisation", "texte": texte}
                )
                # Continuer malgré l'erreur
                
            # Si en mode dictée, vérifier d'abord si c'est une commande de fin
            if get_dictation_mode():
                try:
                    # Vérification spécifique pour les commandes de fin de dictée
                    commande_normalisee, _ = normaliser_commande(texte)
                    
                    if commande_normalisee == "end_dictation":
                        # Traitement prioritaire des commandes de fin
                        from dictation_mode import terminer_dictee
                        resultat = terminer_dictee(get_dictated_text())
                        # Enregistrer la réponse dans l'interface web si disponible
                        if web_interface_available:
                            response_to_web(resultat)
                        return resultat
                    
                    # Sinon, traiter comme dictée normale
                    resultat = traiter_dictee(texte)
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat)
                    return resultat
                except Exception as e:
                    error_msg = f"Erreur lors du traitement de la dictée: {str(e)}"
                    print(error_msg)
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        context={"mode": "dictée", "texte": texte}
                    )
                    if web_interface_available:
                        log_to_web("Erreur lors de la dictée. Veuillez réessayer.", "error")
                    return "Erreur lors de la dictée. Veuillez réessayer."
            
            # Sinon, vérifier si c'est une commande d'écriture
            try:
                resultat_ecriture = traiter_commande_ecriture(texte)
                if resultat_ecriture:
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat_ecriture)
                    return resultat_ecriture
            except Exception as e:
                error_msg = f"Erreur lors du traitement de la commande d'écriture: {str(e)}"
                print(error_msg)
                error_handler.handle_error(
                    e,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "écriture", "texte": texte}
                )
                # Continuer avec les autres types de commandes
            
            # Vérifier si c'est une commande de contexte d'écran
            try:
                commande_normalisee, _ = normaliser_commande(texte)
                if commande_normalisee == "screen_context":
                    resultat = decrire_contexte_ecran()
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat)
                    return resultat
            except Exception as e:
                error_msg = f"Erreur lors de l'analyse du contexte d'écran: {str(e)}"
                print(error_msg)
                error_handler.handle_error(
                    e,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "contexte d'écran"}
                )
                if web_interface_available:
                    log_to_web("Erreur lors de l'analyse du contexte d'écran. Veuillez réessayer.", "error")
                return "Erreur lors de l'analyse du contexte d'écran. Veuillez réessayer."
                
            # Vérifier si c'est une commande de lecture d'écran
            if est_commande_lecture_ecran(texte):
                try:
                    resultat = executer_commande_lecture_ecran(texte)
                    # Enregistrer la réponse dans l'interface web si disponible
                    if web_interface_available:
                        response_to_web(resultat)
                    return resultat
                except Exception as e:
                    error_msg = f"Erreur lors de la lecture d'écran: {str(e)}"
                    print(error_msg)
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        context={"action": "lecture d'écran", "texte": texte}
                    )
                    if web_interface_available:
                        log_to_web("Erreur lors de la lecture d'écran. Veuillez réessayer.", "error")
                    return "Erreur lors de la lecture d'écran. Veuillez réessayer."
            
            # Vérification rapide pour les commandes de traduction avec "écris/écrit en"
            if texte.lower().startswith(("écris en ", "écrit en ", "écrire en ", "écriture en ")):
                try:
                    resultat = executer_commande_traduction(texte)
                    if resultat:
                        if web_interface_available:
                            response_to_web(resultat)
                        return resultat
                except Exception as e:
                    error_msg = f"Erreur lors de la traduction: {str(e)}"
                    print(error_msg)
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        context={"action": "traduction", "texte": texte}
                    )
                    # Continuer avec les autres types de commandes
            
            # Vérification spéciale pour "va sur amazon"
            if "va sur amazon" in texte.lower() or "aller sur amazon" in texte.lower():
                print("Commande spéciale 'va sur amazon' détectée")
                try:
                    resultat = executer_commande_navigateur(texte)
                    if resultat:
                        if web_interface_available:
                            response_to_web(resultat)
                        return resultat
                except Exception as e:
                    error_msg = f"Erreur lors de la navigation vers Amazon: {str(e)}"
                    print(error_msg)
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        context={"action": "navigation", "site": "amazon"}
                    )
                    if web_interface_available:
                        log_to_web("Erreur lors de la navigation vers Amazon. Veuillez réessayer.", "error")
                    return "Erreur lors de la navigation vers Amazon. Veuillez réessayer."
            
            # Vérifier d'abord si c'est un raccourci personnalisé
            try:
                # Utiliser le texte nettoyé pour la recherche de raccourcis
                texte_nettoye = nettoyer_commande(texte)
                if executer_raccourci_personnalise(texte_nettoye):
                    resultat = f"Raccourci personnalisé exécuté : {texte_nettoye}"
                    if web_interface_available:
                        response_to_web(resultat)
                        log_to_web(f"Raccourci personnalisé exécuté : {texte_nettoye}", "info")
                    return resultat
            except Exception as e:
                error_msg = f"Erreur lors de l'exécution du raccourci personnalisé: {str(e)}"
                print(error_msg)
                error_handler.handle_error(
                    e,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.MEDIUM,
                    notify_user=False,
                    context={"action": "raccourci personnalisé", "texte": texte}
                )
                # Continuer avec les autres types de commandes
            
            # Essayer les différents types de commandes dans l'ordre
            commandes = [
                # Priorité aux commandes d'accessibilité pour les personnes à mobilité réduite
                executer_commande_accessibilite,
                # Commandes de traduction (prioritaires pour éviter les conflits)
                executer_commande_traduction,
                # Commandes d'analyse (prioritaires pour éviter les conflits)
                executer_commande_analyse,
                # Commandes de navigateur (prioritaires pour les opérations sur les onglets et sites web)
                executer_commande_navigateur,
                # Commandes de fenêtre (pour la navigation entre applications)
                self.executer_commande_fenetre_wrapper,
                # Commandes de souris (prioritaires pour les clics)
                executer_commande_souris,
                # Commandes de recherche (prioritaires pour une meilleure expérience utilisateur)
                executer_commande_recherche,
                # Commandes de lecture d'écran (après les autres commandes prioritaires)
                executer_commande_lecture_ecran,
                executer_commande_clavier,
                executer_commande_systeme,
                executer_commande_productivite,
                executer_commande_git,
                executer_commande_dev,
                executer_commande_projet,
                executer_commande_web_dev,
                executer_commande_database,
                executer_commande_rappel,
                executer_commande_fichier
            ]
            
            # Liste pour suivre les erreurs rencontrées
            erreurs_commandes = []
            
            for commande_handler in commandes:
                try:
                    resultat = commande_handler(texte)
                    if resultat:
                        # Enregistrer la réponse dans l'interface web si disponible
                        if web_interface_available:
                            response_to_web(resultat)
                        return resultat
                except Exception as e:
                    # Récupérer le nom de la fonction pour le diagnostic
                    handler_name = commande_handler.__name__ if hasattr(commande_handler, "__name__") else str(commande_handler)
                    error_msg = f"Erreur lors de l'exécution de {handler_name}: {str(e)}"
                    print(error_msg)
                    
                    # Enregistrer l'erreur mais continuer avec les autres handlers
                    erreurs_commandes.append((handler_name, str(e)))
                    error_handler.handle_error(
                        e,
                        category=ErrorCategory.COMMAND_PROCESSING,
                        severity=ErrorSeverity.MEDIUM,
                        notify_user=False,  # Ne pas notifier l'utilisateur pour chaque erreur de handler
                        context={"handler": handler_name, "texte": texte}
                    )
                    # Continuer avec le prochain handler
            
            # Si des erreurs ont été rencontrées mais qu'aucun handler n'a réussi, les signaler
            if erreurs_commandes:
                error_summary = f"Plusieurs erreurs rencontrées lors du traitement de la commande: {texte}"
                print(error_summary)
                print(f"Détails des erreurs: {erreurs_commandes}")
                
                # Enregistrer un résumé des erreurs
                error_handler.handle_error(
                    error_summary,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.MEDIUM,
                    context={"erreurs": erreurs_commandes, "texte": texte}
                )
            
            # Si aucune commande n'a été reconnue, tenter d'écrire directement le texte
            try:
                # Suppression de la condition sur le nombre de mots pour permettre les mots simples
                ecrire_texte_avec_accents(texte)
                resultat = f"Texte écrit : {texte}"
                # Enregistrer la réponse dans l'interface web si disponible
                if web_interface_available:
                    response_to_web(resultat)
                return resultat
            except Exception as e:
                error_msg = f"Erreur lors de l'écriture du texte: {str(e)}"
                print(error_msg)
                error_handler.handle_error(
                    e,
                    category=ErrorCategory.COMMAND_PROCESSING,
                    severity=ErrorSeverity.MEDIUM,
                    context={"action": "écriture directe", "texte": texte}
                )
                
                # Message d'erreur générique en cas d'échec complet
                error_response = "Désolé, je n'ai pas pu traiter cette commande. Veuillez réessayer."
                if web_interface_available:
                    response_to_web(error_response)
                    log_to_web("Erreur lors du traitement de la commande. Veuillez réessayer.", "error")
                return error_response
                
        except Exception as e:
            # Capture des erreurs non gérées
            error_msg = f"Erreur non gérée lors du traitement de la commande: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            error_handler.handle_error(
                e,
                category=ErrorCategory.COMMAND_PROCESSING,
                severity=ErrorSeverity.HIGH,
                context={"texte": texte, "trace": traceback.format_exc()}
            )
            
            # Message d'erreur pour l'utilisateur
            error_response = "Une erreur s'est produite lors du traitement de votre commande. Veuillez réessayer."
            if web_interface_available:
                response_to_web(error_response)
                log_to_web("Erreur lors du traitement de la commande. L'erreur a été enregistrée.", "error")
            
            return error_response
            
    def executer_commande_fenetre_wrapper(self, texte):
        """Wrapper pour executer_commande_fenetre qui gère le cas spécial des sites web"""
        # Vérification préalable pour les sites web courants
        commande_normalisee, parametres = normaliser_commande(texte)
        
        if commande_normalisee == "go_to_website" and "website" in parametres:
            site_name = parametres["website"].lower()
            
            # Vérification directe pour Amazon (cas prioritaire)
            if site_name and "amazon" in site_name:
                print(f"Amazon détecté dans command_processor: {site_name}")
                from browser_commands import executer_commande_navigateur
                return executer_commande_navigateur(texte)
            
            # Liste des sites web courants à vérifier en priorité
            common_sites = ["google", "facebook", "youtube", "twitter", "instagram", "linkedin"]
            if site_name and any(site in site_name for site in common_sites):
                print(f"Site web courant détecté dans command_processor: {site_name}")
                from browser_commands import executer_commande_navigateur
                return executer_commande_navigateur(texte)
        
        # Si ce n'est pas un site web courant, continuer avec la vérification normale
        from window_manager import executer_commande_fenetre
        
        resultat = executer_commande_fenetre(texte)
        
        # Si le résultat est "SITE_WEB_CONNU", cela signifie que c'est un site web
        # et que nous devons laisser browser_commands le gérer
        if resultat == "SITE_WEB_CONNU":
            from browser_commands import executer_commande_navigateur
            return executer_commande_navigateur(texte)
        
        return resultat
        
        # Si en mode traduction, traiter en priorité
        if get_translation_mode():
            resultat = executer_commande_traduction(texte)
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat)
            return resultat
        
        # Vérifier si c'est une commande pour quitter l'assistant
        if est_commande_sortie(texte):
            print(f"Commande de sortie détectée: '{texte}'")
            demander_confirmation_sortie()
            return "Demande de confirmation pour quitter l'assistant..."
            
        # Vérifier si c'est une commande de sélection (prioritaire)
        texte_nettoye = nettoyer_commande(texte)
            
        if texte_nettoye in ["tout sélectionner", "sélectionner tout", "sélectionne tout", 
                          "tout sélectionne", "select all", "sélectionnez tout", 
                          "sélectionne le tout", "sélectionner le tout"]:
            resultat = executer_commande_clavier("sélectionner tout")
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat)
            return resultat
            
        # Si en mode dictée, vérifier d'abord si c'est une commande de fin
        if get_dictation_mode():
            # Vérification spécifique pour les commandes de fin de dictée
            texte_nettoye = nettoyer_commande(texte)
            phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                            "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
            
            if texte_nettoye in phrases_arret:
                # Traitement prioritaire des commandes de fin
                from dictation_mode import terminer_dictee
                resultat = terminer_dictee(get_dictated_text())
                # Enregistrer la réponse dans l'interface web si disponible
                if web_interface_available:
                    response_to_web(resultat)
                return resultat
            
            # Sinon, traiter comme dictée normale
            resultat = traiter_dictee(texte)
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat)
            return resultat
        
        # Sinon, vérifier si c'est une commande d'écriture
        resultat_ecriture = traiter_commande_ecriture(texte)
        if resultat_ecriture:
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat_ecriture)
            return resultat_ecriture
        
        # Vérifier si c'est une commande de contexte d'écran
        if nettoyer_commande(texte) in ["contexte", "contexte écran", "décris l'écran", "décris ce que tu vois", 
                            "analyse l'écran", "que vois-tu", "décris le contexte", 
                            "analyse le contexte de l'écran"]:
            resultat = decrire_contexte_ecran()
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat)
            return resultat
            
        # Vérifier si c'est une commande de lecture d'écran
        if est_commande_lecture_ecran(texte):
            resultat = executer_commande_lecture_ecran(texte)
            # Enregistrer la réponse dans l'interface web si disponible
            if web_interface_available:
                response_to_web(resultat)
            return resultat
        
        # Vérification rapide pour les commandes de traduction avec "écris/écrit en"
        if texte.lower().startswith(("écris en ", "écrit en ", "écrire en ", "écriture en ")):
            resultat = executer_commande_traduction(texte)
            if resultat:
                if web_interface_available:
                    response_to_web(resultat)
                return resultat
        
        # Essayer les différents types de commandes dans l'ordre
        commandes = [
            # Priorité aux commandes d'accessibilité pour les personnes à mobilité réduite
            executer_commande_accessibilite,
            # Commandes de traduction (prioritaires pour éviter les conflits)
            executer_commande_traduction,
            # Commandes d'analyse (prioritaires pour éviter les conflits)
            executer_commande_analyse,
            # Commandes de navigateur (prioritaires pour les opérations sur les onglets et sites web)
            executer_commande_navigateur,
            # Commandes de fenêtre (pour la navigation entre applications)
            self.executer_commande_fenetre_wrapper,
            # Commandes de souris (prioritaires pour les clics)
            executer_commande_souris,
            # Commandes de recherche (prioritaires pour une meilleure expérience utilisateur)
            executer_commande_recherche,
            # Commandes de lecture d'écran (après les autres commandes prioritaires)
            executer_commande_lecture_ecran,
            executer_commande_clavier,
            executer_commande_systeme,
            executer_commande_productivite,
            executer_commande_git,
            executer_commande_dev,
            executer_commande_projet,
            executer_commande_web_dev,
            executer_commande_database,
            executer_commande_rappel,
            executer_commande_fichier
        ]
        
        for commande_handler in commandes:
            resultat = commande_handler(texte)
            if resultat:
                # Enregistrer la réponse dans l'interface web si disponible
                if web_interface_available:
                    response_to_web(resultat)
                return resultat
        
        # Si aucune commande n'a été reconnue, tenter d'écrire directement le texte
        # Suppression de la condition sur le nombre de mots pour permettre les mots simples
        ecrire_texte_avec_accents(texte)
        resultat = f"Texte écrit : {texte}"
        # Enregistrer la réponse dans l'interface web si disponible
        if web_interface_available:
            response_to_web(resultat)
        return resultat
        
        # Cette partie ne devrait jamais être atteinte car nous avons déjà géré tous les cas
        # mais nous la gardons comme filet de sécurité
        resultat = f"Commande non reconnue : {texte}"
        
        # Enregistrer la réponse dans l'interface web si disponible
        if web_interface_available and resultat:
            response_to_web(resultat)
            
        return resultat
