"""
Module de gestion du mode dictée pour l'assistant Whisp
"""

from config import set_dictation_mode, get_dictation_mode, get_dictated_text, append_dictated_text
from text_processing import ameliorer_formatage, ecrire_texte_avec_accents

def activer_mode_dictee(texte_initial=""):
    """Active le mode dictée continue"""
    set_dictation_mode(True, texte_initial)
    return "Mode dictée activé. Parlez maintenant, dites 'fin de dictée' pour terminer."

def traiter_dictee(texte):
    """Traite le texte en mode dictée continue"""
    from command_aliases import is_command_alias
    from text_processing import nettoyer_commande
    from shortcuts_database import executer_raccourci_personnalise
    
    # Vérifier si c'est une commande de fin de dictée
    texte_nettoye = nettoyer_commande(texte)
    
    # Vérifier d'abord si c'est un raccourci personnalisé
    try:
        if executer_raccourci_personnalise(texte_nettoye):
            return f"Raccourci personnalisé exécuté : {texte_nettoye}"
    except Exception as e:
        print(f"Erreur lors de l'exécution du raccourci personnalisé en mode dictée: {str(e)}")
        # Continuer avec le traitement normal
    
    # Vérification stricte pour les commandes de fin
    if is_command_alias(texte_nettoye, "end_dictation"):
        # Si le texte est exactement une commande de fin
        texte_dicte = get_dictated_text()
        return terminer_dictee(texte_dicte)
    
    # Vérification plus souple si la commande est incluse dans un texte plus long
    texte_lower = texte.lower()
    phrases_arret = ["fin de dictée", "terminer dictée", "arrêter dictée", "finir dictée", 
                     "fin dictée", "stop dictée", "arrête dictée", "termine dictée"]
    
    for phrase in phrases_arret:
        if phrase in texte_lower:
            # On enlève la phrase d'arrêt du texte final si elle s'y trouve
            texte_dicte = get_dictated_text()
            for p in phrases_arret:
                texte_dicte = texte_dicte.replace(p, "").strip()
            
            return terminer_dictee(texte_dicte)
    
    # Sinon, on ajoute le texte à la dictée en cours
    # Ignorer les textes trop courts qui sont probablement des fragments
    if len(texte.strip()) < 2:
        return f"Dictée en cours... ({len(get_dictated_text())} caractères)"
        
    # Vérifier si le texte commence par une minuscule et si le texte dicté ne se termine pas par une ponctuation
    # pour déterminer s'il s'agit probablement d'une continuation de phrase
    texte_dicte = get_dictated_text()
    
    # Logique améliorée pour la détection de continuation de phrase
    if texte_dicte and texte:
        dernier_mot_dicte = texte_dicte.split()[-1] if texte_dicte.split() else ""
        premier_mot_texte = texte.split()[0] if texte.split() else ""
        
        # Si le dernier mot dicté semble être le début du premier mot du nouveau texte
        # ou si le texte commence par une minuscule et le texte dicté ne se termine pas par une ponctuation
        if (dernier_mot_dicte and premier_mot_texte and 
            (dernier_mot_dicte in premier_mot_texte or 
             (texte[0].islower() and not texte_dicte[-1] in ".!?"))):
            # C'est probablement une continuation, on ajoute sans espace supplémentaire
            # et on supprime le dernier mot du texte dicté pour éviter les doublons
            if dernier_mot_dicte in premier_mot_texte:
                texte_dicte = texte_dicte[:-len(dernier_mot_dicte)].rstrip()
                set_dictation_mode(True, texte_dicte)
            append_dictated_text(texte, False)
        else:
            # Sinon, on ajoute normalement avec un espace
            append_dictated_text(texte)
    else:
        # Premier texte de la dictée
        append_dictated_text(texte)
    
    return f"Dictée en cours... ({len(get_dictated_text())} caractères)"

def terminer_dictee(texte_dicte):
    """Termine la dictée et écrit le texte final"""
    texte_final = ameliorer_formatage(texte_dicte)
    # Utiliser la fonction spéciale pour écrire avec accents
    ecrire_texte_avec_accents(texte_final)
    
    # Désactiver le mode dictée
    set_dictation_mode(False)
    
    return f"Mode dictée terminé. Texte écrit : {texte_final}"

def traiter_commande_ecriture(texte):
    """Détecte si une commande d'écriture a été demandée"""
    from command_aliases import is_command_alias, extract_command_parameters
    from text_processing import nettoyer_commande
    from shortcuts_database import executer_raccourci_personnalise
    
    # Vérifier d'abord si nous sommes déjà en mode dictée
    # Si c'est le cas, ne pas interpréter de nouvelles commandes
    if get_dictation_mode():
        return None
    
    # Nettoyer le texte
    texte_nettoye = nettoyer_commande(texte)
    
    # Vérifier si c'est un raccourci personnalisé
    try:
        if executer_raccourci_personnalise(texte_nettoye):
            return f"Raccourci personnalisé exécuté : {texte_nettoye}"
    except Exception as e:
        print(f"Erreur lors de l'exécution du raccourci personnalisé dans traiter_commande_ecriture: {str(e)}")
        # Continuer avec le traitement normal
    
    # Vérifier si c'est un alias de la commande "start_dictation"
    if is_command_alias(texte_nettoye, "start_dictation"):
        # Extraire le texte initial à écrire (s'il y en a)
        params = extract_command_parameters(texte_nettoye, "start_dictation")
        texte_initial = params.get("initial_text", "")
        
        # Activer le mode dictée avec le texte initial
        return activer_mode_dictee(texte_initial)
    
    # Conserver la méthode originale pour la compatibilité
    # Liste des mots déclencheurs possibles
    declencheurs = ["écris", "écrit", "tape", "saisis", "note", "dictée"]
    
    # Nettoyer le texte en enlevant le point final s'il existe
    texte_clean = texte.lower().strip()
    if texte_clean.endswith("."):
        texte_clean = texte_clean[:-1].strip()
    
    # Ignorer les commandes qui ressemblent à des commandes de traduction
    if any(texte_clean.startswith(f"{declencheur} en ") for declencheur in ["écris", "écrit", "écrire", "écriture"]) or \
       any(f"{declencheur} en " in texte_clean for declencheur in ["écris", "écrit", "écrire", "écriture"]):
        return None
    
    # Vérifier si un des déclencheurs est présent
    for declencheur in declencheurs:
        if declencheur in texte_clean:
            # Extraire le texte initial à écrire (s'il y en a)
            parties = texte.lower().split(declencheur, 1)
            texte_initial = ""
            
            if len(parties) > 1:
                texte_initial = parties[1].strip()
                
                # Enlever les préfixes courants dans le langage naturel
                prefixes_a_supprimer = [
                    "le texte", "le message", "ceci", "ça", "s'il te plait",
                    "s'il vous plait", "pour moi", "ce qui suit", ":"
                ]
                for prefixe in prefixes_a_supprimer:
                    if texte_initial.startswith(prefixe):
                        texte_initial = texte_initial[len(prefixe):].strip()
            
            # Activer le mode dictée avec le texte initial
            return activer_mode_dictee(texte_initial)
    
    return None  # Aucun déclencheur trouvé
