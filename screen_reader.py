"""
Module de lecture d'écran intelligente pour l'assistant Whisp
"""

import pyautogui
import pytesseract
from PIL import Image, ImageEnhance
import re
import win32gui
import win32process
import psutil
import time
from tts_module import ajouter_texte_a_lire
from screen_context import localiser_element_ecran

def get_active_window_process():
    """
    Obtient le nom du processus de la fenêtre active
    """
    try:
        # Obtenir le handle de la fenêtre active
        hwnd = win32gui.GetForegroundWindow()
        
        # Obtenir l'ID du processus
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Obtenir le nom du processus
        process = psutil.Process(pid)
        process_name = process.name().lower()
        
        # Obtenir le titre de la fenêtre
        window_title = win32gui.GetWindowText(hwnd)
        
        return process_name, window_title
    except Exception as e:
        print(f"Erreur lors de l'obtention du processus de la fenêtre active: {e}")
        return None, None

def lire_ecran_intelligemment(point_depart=None):
    """
    Analyse et lit le contenu de l'écran de manière intelligente
    en fonction de l'application active
    
    Args:
        point_depart: Description textuelle du point à partir duquel commencer la lecture
    """
    print("Analyse intelligente de l'écran en cours...")
    
    # Obtenir le processus de la fenêtre active
    process_name, window_title = get_active_window_process()
    print(f"Fenêtre active: {process_name} - {window_title}")
    
    # Capturer l'écran
    screenshot = pyautogui.screenshot()
    
    # Améliorer le contraste pour une meilleure reconnaissance
    enhancer = ImageEnhance.Contrast(screenshot)
    enhanced_image = enhancer.enhance(1.5)
    
    # Texte à lire
    texte_a_lire = ""
    
    # Adapter l'analyse en fonction de l'application
    if process_name in ["chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe"]:
        # Navigateur web - se concentrer sur le contenu principal
        texte_a_lire = extraire_contenu_navigateur(enhanced_image, window_title)
    
    elif process_name in ["explorer.exe"]:
        # Explorateur de fichiers
        texte_a_lire = extraire_contenu_explorateur(enhanced_image, window_title)
    
    elif process_name in ["notepad.exe", "code.exe", "wordpad.exe"]:
        # Éditeurs de texte
        texte_a_lire = extraire_contenu_editeur(enhanced_image)
    
    elif process_name in ["winword.exe", "excel.exe", "powerpnt.exe"]:
        # Applications Office
        texte_a_lire = extraire_contenu_office(enhanced_image, process_name)
    
    else:
        # Méthode générique pour les autres applications
        texte_a_lire = extraire_contenu_generique(enhanced_image, window_title)
    
    # Si aucun texte n'a été extrait, utiliser la méthode générique
    if not texte_a_lire:
        texte_a_lire = extraire_contenu_generique(enhanced_image, window_title)
    
    # Nettoyer et formater le texte
    texte_a_lire = nettoyer_texte(texte_a_lire)
    
    # Si un point de départ est spécifié, commencer la lecture à partir de ce point
    if point_depart:
        texte_a_lire = commencer_lecture_a_partir_de(texte_a_lire, point_depart, enhanced_image)
    
    # Ajouter une introduction
    if point_depart:
        introduction = f"Lecture à partir de '{point_depart}' dans {window_title}. "
    else:
        introduction = f"Contenu de {window_title}. "
    
    texte_complet = introduction + texte_a_lire
    
    # Lire le texte
    if texte_complet:
        ajouter_texte_a_lire(texte_complet)
        return texte_complet
    else:
        message = "Aucun contenu textuel n'a pu être extrait de l'écran."
        ajouter_texte_a_lire(message)
        return message

def extraire_contenu_navigateur(image, titre):
    """
    Extrait le contenu principal d'une page web
    en ignorant les menus, barres d'outils, etc.
    """
    # Dimensions de l'image
    largeur, hauteur = image.size
    
    # Définir une zone centrale qui contient probablement le contenu principal
    # Exclure les barres d'outils, menus, etc.
    marge_haut = int(hauteur * 0.15)  # Ignorer la barre d'adresse et les onglets
    marge_bas = int(hauteur * 0.1)    # Ignorer la barre d'état
    marge_gauche = int(largeur * 0.05) # Ignorer les barres latérales éventuelles
    marge_droite = int(largeur * 0.05) # Ignorer les barres latérales éventuelles
    
    # Découper l'image pour ne garder que la zone de contenu
    zone_contenu = image.crop((
        marge_gauche,
        marge_haut,
        largeur - marge_droite,
        hauteur - marge_bas
    ))
    
    # Extraire le texte de la zone de contenu
    texte = pytesseract.image_to_string(zone_contenu, lang='fra')
    
    # Ajouter le titre de la page
    if titre:
        texte = f"Page web: {titre}\n\n{texte}"
    
    return texte

def extraire_contenu_explorateur(image, titre):
    """
    Extrait le contenu de l'explorateur de fichiers
    """
    # Dimensions de l'image
    largeur, hauteur = image.size
    
    # Définir une zone qui contient probablement la liste des fichiers
    # Exclure la barre de navigation, le ruban, etc.
    marge_haut = int(hauteur * 0.2)    # Ignorer le ruban et la barre d'adresse
    marge_bas = int(hauteur * 0.05)    # Ignorer la barre d'état
    marge_gauche = int(largeur * 0.2)  # Ignorer le volet de navigation
    marge_droite = int(largeur * 0.05) # Marge de droite
    
    # Découper l'image pour ne garder que la zone de contenu
    zone_contenu = image.crop((
        marge_gauche,
        marge_haut,
        largeur - marge_droite,
        hauteur - marge_bas
    ))
    
    # Extraire le texte de la zone de contenu
    texte = pytesseract.image_to_string(zone_contenu, lang='fra')
    
    # Ajouter le titre du dossier
    if titre:
        texte = f"Dossier: {titre}\n\n{texte}"
    
    return texte

def extraire_contenu_editeur(image):
    """
    Extrait le contenu d'un éditeur de texte
    """
    # Dimensions de l'image
    largeur, hauteur = image.size
    
    # Définir une zone qui contient probablement le texte
    # Exclure les menus, barres d'outils, etc.
    marge_haut = int(hauteur * 0.1)    # Ignorer les menus et barres d'outils
    marge_bas = int(hauteur * 0.05)    # Ignorer la barre d'état
    marge_gauche = int(largeur * 0.05) # Marge de gauche
    marge_droite = int(largeur * 0.05) # Marge de droite
    
    # Découper l'image pour ne garder que la zone de texte
    zone_texte = image.crop((
        marge_gauche,
        marge_haut,
        largeur - marge_droite,
        hauteur - marge_bas
    ))
    
    # Extraire le texte
    texte = pytesseract.image_to_string(zone_texte, lang='fra')
    
    return texte

def extraire_contenu_office(image, process_name):
    """
    Extrait le contenu d'une application Office
    """
    # Dimensions de l'image
    largeur, hauteur = image.size
    
    # Définir une zone qui contient probablement le contenu
    # Exclure le ruban, les barres d'outils, etc.
    marge_haut = int(hauteur * 0.15)   # Ignorer le ruban
    marge_bas = int(hauteur * 0.05)    # Ignorer la barre d'état
    marge_gauche = int(largeur * 0.05) # Marge de gauche
    marge_droite = int(largeur * 0.05) # Marge de droite
    
    # Découper l'image pour ne garder que la zone de contenu
    zone_contenu = image.crop((
        marge_gauche,
        marge_haut,
        largeur - marge_droite,
        hauteur - marge_bas
    ))
    
    # Extraire le texte
    texte = pytesseract.image_to_string(zone_contenu, lang='fra')
    
    # Adapter le message en fonction de l'application
    if process_name == "winword.exe":
        texte = f"Document Word:\n\n{texte}"
    elif process_name == "excel.exe":
        texte = f"Feuille de calcul Excel:\n\n{texte}"
    elif process_name == "powerpnt.exe":
        texte = f"Présentation PowerPoint:\n\n{texte}"
    
    return texte

def extraire_contenu_generique(image, titre):
    """
    Méthode générique pour extraire le contenu de n'importe quelle application
    """
    # Dimensions de l'image
    largeur, hauteur = image.size
    
    # Définir une zone centrale qui contient probablement le contenu principal
    marge_haut = int(hauteur * 0.1)    # Ignorer les menus et barres d'outils
    marge_bas = int(hauteur * 0.05)    # Ignorer la barre d'état
    marge_gauche = int(largeur * 0.05) # Marge de gauche
    marge_droite = int(largeur * 0.05) # Marge de droite
    
    # Découper l'image pour ne garder que la zone centrale
    zone_centrale = image.crop((
        marge_gauche,
        marge_haut,
        largeur - marge_droite,
        hauteur - marge_bas
    ))
    
    # Extraire le texte
    texte = pytesseract.image_to_string(zone_centrale, lang='fra')
    
    # Ajouter le titre de la fenêtre
    if titre:
        texte = f"{titre}:\n\n{texte}"
    
    return texte

def nettoyer_texte(texte):
    """
    Nettoie et formate le texte extrait
    """
    if not texte:
        return ""
    
    # Supprimer les lignes vides consécutives
    texte = re.sub(r'\n\s*\n', '\n\n', texte)
    
    # Supprimer les caractères spéciaux et les artefacts OCR courants
    texte = re.sub(r'[|]{2,}', '', texte)  # Supprimer les barres verticales répétées
    texte = re.sub(r'[_]{2,}', '', texte)  # Supprimer les underscores répétés
    
    # Supprimer les espaces en début et fin de texte
    texte = texte.strip()
    
    return texte
def lire_ecran_a_partir_de(element_description):
    """
    Lit le contenu de l'écran à partir d'un élément spécifié
    
    Args:
        element_description: Description textuelle de l'élément à partir duquel commencer la lecture
    """
    print(f"Lecture de l'écran à partir de: {element_description}")
    
    # Localiser l'élément sur l'écran
    coordonnees = localiser_element_ecran(element_description)
    
    if coordonnees:
        # Déplacer la souris vers l'élément pour un feedback visuel
        x, y = coordonnees
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.5)
        pyautogui.moveTo(current_x, current_y, duration=0.2)
        
        # Lire l'écran à partir de cet élément
        return lire_ecran_intelligemment(element_description)
    else:
        message = f"Impossible de trouver l'élément '{element_description}' sur l'écran."
        ajouter_texte_a_lire(message)
        return message

def commencer_lecture_a_partir_de(texte_complet, point_depart, image):
    """
    Modifie le texte pour commencer la lecture à partir d'un point spécifié
    
    Args:
        texte_complet: Le texte complet extrait de l'écran
        point_depart: Description textuelle du point de départ
        image: Image de l'écran pour analyse OCR supplémentaire si nécessaire
    
    Returns:
        Le texte à partir du point de départ
    """
    # Si le texte est vide, retourner tel quel
    if not texte_complet:
        return texte_complet
    
    # Essayer de trouver le point de départ dans le texte
    # 1. Recherche exacte
    if point_depart.lower() in texte_complet.lower():
        # Trouver l'index du point de départ (insensible à la casse)
        index_debut = texte_complet.lower().find(point_depart.lower())
        return texte_complet[index_debut:]
    
    # 2. Recherche de mots clés
    mots_cles = [mot for mot in point_depart.split() if len(mot) > 3]
    for mot in mots_cles:
        if mot.lower() in texte_complet.lower():
            index_debut = texte_complet.lower().find(mot.lower())
            # Trouver le début de la phrase contenant ce mot
            debut_phrase = texte_complet.rfind('.', 0, index_debut) + 1
            if debut_phrase == 0:  # Si pas de point trouvé avant
                debut_phrase = texte_complet.rfind('\n', 0, index_debut) + 1
            return texte_complet[debut_phrase:].strip()
    
    # 3. Si aucune correspondance n'est trouvée, essayer une analyse OCR ciblée
    try:
        # Localiser l'élément sur l'écran
        coordonnees = localiser_element_ecran(point_depart)
        if coordonnees:
            x, y = coordonnees
            
            # Définir une zone autour du point trouvé
            largeur, hauteur = image.size
            zone_x1 = max(0, x - 300)
            zone_y1 = max(0, y - 100)
            zone_x2 = min(largeur, x + 800)
            zone_y2 = min(hauteur, y + 500)
            
            # Découper l'image pour ne garder que la zone autour du point
            zone_texte = image.crop((zone_x1, zone_y1, zone_x2, zone_y2))
            
            # Extraire le texte de cette zone
            texte_zone = pytesseract.image_to_string(zone_texte, lang='fra')
            texte_zone = nettoyer_texte(texte_zone)
            
            if texte_zone:
                return texte_zone
    except Exception as e:
        print(f"Erreur lors de l'analyse OCR ciblée: {e}")
    
    # Si toutes les tentatives échouent, retourner le texte complet
    return texte_complet
