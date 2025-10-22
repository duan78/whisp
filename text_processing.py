"""
Module de traitement de texte pour l'assistant Whisp
"""

import pyperclip
import pyautogui

def ameliorer_formatage(texte):
    """Améliore le formatage du texte dicté"""
    if not texte:
        return texte
    
    # Mettre la première lettre en majuscule si c'est une phrase
    if len(texte) > 0 and texte[0].isalpha():
        texte = texte[0].upper() + texte[1:]
    
    # Remplacer les mots dictés pour la ponctuation
    remplacements_ponctuation = {
        " point ": ".",
        " virgule ": ",",
        " point d'interrogation ": "?",
        " point d'exclamation ": "!",
        " deux points ": ":",
        " point-virgule ": ";",
        " à la ligne ": "\n",
        " nouvelle ligne ": "\n",
        " retour à la ligne ": "\n",
        " ouvre parenthèse ": " (",
        " ferme parenthèse ": ") ",
        " ouvre guillemets ": " « ",
        " ferme guillemets ": " » ",
        " ouvre crochet ": " [",
        " ferme crochet ": "] ",
        " ouvre accolade ": " {",
        " ferme accolade ": "} ",
        " tiret ": "-",
        " tiret du bas ": "_",
        " pourcentage ": "%",
        " arobase ": "@",
        " dièse ": "#",
        " esperluette ": "&",
        " et commercial ": "&",
        " astérisque ": "*",
        " plus ": "+",
        " égal ": "=",
        " dollar ": "$",
        " euro ": "€",
        " supérieur ": ">",
        " inférieur ": "<",
        " barre oblique ": "/",
        " barre verticale ": "|",
        " tilde ": "~",
        " accent circonflexe ": "^",
        " point point point ": "...",
        " points de suspension ": "...",
    }
    
    for mot, remplacement in remplacements_ponctuation.items():
        texte = texte.replace(mot, remplacement)
    
    # Améliorer la ponctuation
    # Ajouter un espace après la ponctuation si nécessaire
    for ponctuation in ['.', ',', ':', ';', '!', '?']:
        texte = texte.replace(ponctuation + ' ', ponctuation + ' ')
        texte = texte.replace(ponctuation + 'a', ponctuation + ' a')
        texte = texte.replace(ponctuation + 'à', ponctuation + ' à')
        texte = texte.replace(ponctuation + 'e', ponctuation + ' e')
        texte = texte.replace(ponctuation + 'é', ponctuation + ' é')
        texte = texte.replace(ponctuation + 'i', ponctuation + ' i')
        texte = texte.replace(ponctuation + 'o', ponctuation + ' o')
        texte = texte.replace(ponctuation + 'u', ponctuation + ' u')
        texte = texte.replace(ponctuation + 'y', ponctuation + ' y')
    
    # Supprimer les espaces avant la ponctuation
    for ponctuation in ['.', ',', ':', ';', '!', '?']:
        texte = texte.replace(' ' + ponctuation, ponctuation)
    
    # Ajouter un espace après les guillemets ouvrants et avant les guillemets fermants
    texte = texte.replace('«', '« ')
    texte = texte.replace('»', ' »')
    
    # Corriger les espaces multiples
    while '  ' in texte:
        texte = texte.replace('  ', ' ')
    
    # Corriger les majuscules après les points
    phrases = texte.split('. ')
    for i in range(1, len(phrases)):
        if phrases[i] and phrases[i][0].isalpha() and phrases[i][0].islower():
            phrases[i] = phrases[i][0].upper() + phrases[i][1:]
    texte = '. '.join(phrases)
    
    return texte

def ecrire_texte_avec_accents(texte):
    """Écrit du texte en préservant les caractères accentués"""
    if not texte:
        return
    
    # Copier le texte dans le presse-papier
    pyperclip.copy(texte)
    
    # Coller le texte avec Ctrl+V
    pyautogui.hotkey('ctrl', 'v')

def nettoyer_commande(texte):
    """Nettoie une commande vocale pour la normalisation
    - Supprime les points finaux
    - Convertit en minuscules
    - Supprime les espaces en début et fin
    - Normalise les caractères accentués (optionnel)
    """
    if not texte:
        return texte
        
    # Supprimer le point final s'il existe
    if texte.endswith("."):
        texte = texte[:-1]
    
    # Supprimer les points d'exclamation et d'interrogation s'ils existent
    if texte.endswith("!") or texte.endswith("?"):
        texte = texte[:-1]
        
    # Convertir en minuscules et supprimer les espaces en début et fin
    return texte.lower().strip()

def nettoyer_reponse_stt(texte, moteur=None):
    """Nettoie une réponse de reconnaissance vocale pour la rendre utilisable comme commande
    
    Args:
        texte (str): Le texte à nettoyer
        moteur (str, optional): Le moteur de reconnaissance utilisé (whisper, whisper_ct2, vosk, speechrecognition)
        
    Returns:
        str: Le texte nettoyé
    """
    if not texte:
        return texte
    
    # Appliquer le nettoyage de base des commandes (points, etc.)
    texte_nettoye = nettoyer_commande(texte)
    
    # Nettoyages spécifiques par moteur
    if moteur in ["whisper", "whisper_ct2", "vosk"]:
        # Ces moteurs ont tendance à ajouter des majuscules et des points qui perturbent les commandes
        texte_nettoye = texte_nettoye.lower()
        
        # Corrections spécifiques pour les patterns problématiques courants
        corrections = {
            "rechercher": "recherche",
            "recherches": "recherche", 
            "recherché": "recherche",
            "nouvelle longlet": "nouvel onglet",
            "nouveau longlet": "nouvel onglet",
            "nouvelle onglet": "nouvel onglet"
        }
        
        for erreur, correction in corrections.items():
            if texte_nettoye.startswith(erreur):
                texte_nettoye = texte_nettoye.replace(erreur, correction, 1)
    
    return texte_nettoye

def normaliser_commande(texte):
    """Normalise une commande en utilisant le système d'alias
    
    Args:
        texte (str): Le texte de la commande à normaliser
        
    Returns:
        tuple: (commande_normalisée, paramètres) ou (None, None) si non reconnue
    """
    from command_aliases import get_normalized_command, extract_command_parameters
    
    # Nettoyage et normalisation de la commande
    cleaned_text = nettoyer_reponse_stt(texte)
    normalized_command = get_normalized_command(cleaned_text)

    # Extraction des paramètres si commande reconnue
    if normalized_command:
        parameters = extract_command_parameters(cleaned_text, normalized_command)
        return normalized_command, parameters

    return None, None
