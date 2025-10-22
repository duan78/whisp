"""
Module de gestion des commandes de lecture d'écran pour l'assistant Whisp
"""

import re
from screen_reader import lire_ecran_intelligemment, lire_ecran_a_partir_de

def est_commande_lecture_ecran(texte):
    """
    Vérifie si le texte est une commande de lecture d'écran
    
    Args:
        texte: Texte à vérifier
        
    Returns:
        bool: True si c'est une commande de lecture d'écran, False sinon
    """
    from command_aliases import is_command_alias
    from text_processing import nettoyer_commande
    
    texte_nettoye = nettoyer_commande(texte)
    
    # Vérifier si c'est un alias de la commande "screen_read"
    if is_command_alias(texte_nettoye, "screen_read"):
        return True
    
    # Vérifier si c'est un alias de la commande "screen_read_from"
    if is_command_alias(texte_nettoye, "screen_read_from"):
        return True
    
    # Conserver la méthode originale pour la compatibilité
    texte = texte.lower()
    
    # Exclure explicitement les commandes de clic et de navigation
    if re.search(r"^(clic|clique|cliquer|appuie|appuyer|sélectionne|sélectionner)\s+sur\s+", texte):
        return False
    
    # Exclure explicitement les commandes de fermeture d'onglet
    if re.search(r"^(ferme|fermer|quitte|quitter|supprime|supprimer)\s+(l'onglet|cet onglet|cette page|la page|lenglet|l'anglais)", texte):
        return False
    
    # Exclure explicitement les commandes de traduction
    if re.search(r"^(traduis|traduit|traduire|traduction|tradui|traduc)\s+en\s+", texte):
        return False
    
    # Liste des commandes de lecture d'écran explicites
    commandes_explicites = [
        "lis l'écran", "lit l'écran", "lire l'écran",
        "lis le contenu de l'écran", "lit le contenu de l'écran", "lire le contenu de l'écran",
        "lecture d'écran", "lecture de l'écran"
    ]
    
    # Vérifier d'abord si c'est une commande explicite
    for cmd in commandes_explicites:
        if cmd in texte:
            return True
    
    # Commandes de lecture d'écran avec point de départ
    patterns_lecture = [
        r"^lis l'écran à partir de (.+)$",
        r"^lis à partir de (.+)$",
        r"^lis depuis (.+)$",
        r"^lis le texte à partir de (.+)$",
        r"^lis le texte depuis (.+)$",
        r"^lis le contenu à partir de (.+)$",
        r"^lis le contenu depuis (.+)$",
        r"^lecture à partir de (.+)$",
        r"^lecture depuis (.+)$",
        # Ajout des variantes avec "lit" (au lieu de "lis")
        r"^lit l'écran à partir de (.+)$",
        r"^lit à partir de (.+)$",
        r"^lit depuis (.+)$",
        r"^lit le texte à partir de (.+)$",
        r"^lit le texte depuis (.+)$",
        r"^lit le contenu à partir de (.+)$",
        r"^lit le contenu depuis (.+)$",
        # Ajout des variantes avec "lire"
        r"^lire l'écran à partir de (.+)$",
        r"^lire à partir de (.+)$",
        r"^lire depuis (.+)$",
        r"^lire le texte à partir de (.+)$",
        r"^lire le texte depuis (.+)$",
        r"^lire le contenu à partir de (.+)$",
        r"^lire le contenu depuis (.+)$",
    ]
    
    for pattern in patterns_lecture:
        if re.search(pattern, texte):
            return True
    
    return False

# Précompiler les expressions régulières pour une meilleure performance
PATTERNS_LECTURE_DEPUIS = [
    # Variantes avec "lis"
    re.compile(r"lis l'écran à partir de (.+)"),
    re.compile(r"lis à partir de (.+)"),
    re.compile(r"lis depuis (.+)"),
    re.compile(r"lis le texte à partir de (.+)"),
    re.compile(r"lis le texte depuis (.+)"),
    re.compile(r"lis le contenu à partir de (.+)"),
    re.compile(r"lis le contenu depuis (.+)"),
    # Variantes avec "lit"
    re.compile(r"lit l'écran à partir de (.+)"),
    re.compile(r"lit à partir de (.+)"),
    re.compile(r"lit depuis (.+)"),
    re.compile(r"lit le texte à partir de (.+)"),
    re.compile(r"lit le texte depuis (.+)"),
    re.compile(r"lit le contenu à partir de (.+)"),
    re.compile(r"lit le contenu depuis (.+)"),
    # Variantes avec "lire"
    re.compile(r"lire l'écran à partir de (.+)"),
    re.compile(r"lire à partir de (.+)"),
    re.compile(r"lire depuis (.+)"),
    re.compile(r"lire le texte à partir de (.+)"),
    re.compile(r"lire le texte depuis (.+)"),
    re.compile(r"lire le contenu à partir de (.+)"),
    re.compile(r"lire le contenu depuis (.+)"),
    # Autres formulations
    re.compile(r"lecture à partir de (.+)"),
    re.compile(r"lecture depuis (.+)"),
]

# Liste des commandes de lecture d'écran complète
COMMANDES_LECTURE_COMPLETE = [
    "lis l'écran", "lis le contenu de l'écran", 
    "lit l'écran", "lit le contenu de l'écran",
    "lire l'écran", "lire le contenu de l'écran",
    "lecture d'écran", "lecture de l'écran"
]

def executer_commande_lecture_ecran(texte):
    """
    Exécute une commande de lecture d'écran
    
    Args:
        texte: Texte de la commande
        
    Returns:
        str: Résultat de la commande ou None si ce n'est pas une commande de lecture d'écran
    """
    from command_aliases import is_command_alias, extract_command_parameters
    from text_processing import nettoyer_commande
    
    texte_nettoye = nettoyer_commande(texte)
    
    # Vérifier d'abord si c'est une commande de lecture d'écran
    if not est_commande_lecture_ecran(texte):
        return None
    
    # Vérifier si c'est un alias de la commande "screen_read"
    if is_command_alias(texte_nettoye, "screen_read"):
        return lire_ecran_intelligemment()
    
    # Vérifier si c'est un alias de la commande "screen_read_from"
    if is_command_alias(texte_nettoye, "screen_read_from"):
        params = extract_command_parameters(texte_nettoye, "screen_read_from")
        element = params.get("element", "")
        
        if element:
            return lire_ecran_a_partir_de(element)
    
    # Conserver la méthode originale pour la compatibilité
    texte = texte.lower()
    
    # Commande de lecture d'écran complète
    if any(cmd in texte for cmd in COMMANDES_LECTURE_COMPLETE):
        return lire_ecran_intelligemment()
    
    # Commande de lecture à partir d'un élément
    for pattern in PATTERNS_LECTURE_DEPUIS:
        match = pattern.search(texte)
        if match:
            element = match.group(1).strip()
            return lire_ecran_a_partir_de(element)
    
    return "Commande de lecture d'écran non reconnue."
