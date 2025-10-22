"""
Module d'analyse du contexte de l'écran pour l'assistant Whisp
Utilise l'API Pixtral de Mistral AI pour décrire ce qui est affiché à l'écran
et localiser des éléments pour le contrôle de la souris
"""

import os
import io
import base64
import pyautogui
import re
from PIL import Image
import time
from mistralai import Mistral
from tts_module import ajouter_texte_a_lire
import pytesseract

# Configuration du chemin vers Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configuration de l'API Mistral AI
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_MODEL = "pixtral-12b-2409"  # Modèle Pixtral pour l'analyse d'images

def capture_ecran():
    """Capture l'écran actuel et retourne l'image"""
    # Capturer l'écran entier
    screenshot = pyautogui.screenshot()
    return screenshot

def encoder_image_base64(image):
    """Encode l'image en base64 pour l'API"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def analyser_image_avec_pixtral(image_base64, prompt="Décris ce qui est affiché sur cet écran:"):
    """Analyse l'image avec l'API Pixtral de Mistral AI"""
    if not MISTRAL_API_KEY:
        return "Erreur: Clé API Mistral non configurée. Veuillez définir la variable d'environnement MISTRAL_API_KEY."
    
    try:
        # Initialiser le client Mistral
        client = Mistral(api_key=MISTRAL_API_KEY)
        
        # Définir les messages pour le chat
        system_content = ""
        if "localise" in prompt.lower() or "trouve" in prompt.lower() or "coordonnées" in prompt.lower():
            system_content = """Tu es un assistant spécialisé dans l'analyse d'images d'écran et la localisation précise d'éléments. 
            Ta tâche est de trouver les coordonnées exactes des éléments demandés. 
            Sois très précis dans tes réponses et donne toujours les coordonnées au format demandé."""
        else:
            system_content = """Tu es un assistant qui analyse des captures d'écran et décrit précisément ce qui est affiché. 
            Décris le contenu de manière détaillée mais concise, en français. 
            Mentionne les applications ouvertes, les fenêtres visibles, et tout élément important à l'écran."""
        
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_base64}"
                    }
                ]
            }
        ]
        
        # Obtenir la réponse du chat
        chat_response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=messages
        )
        
        # Retourner le contenu de la réponse
        return chat_response.choices[0].message.content
    except Exception as e:
        return f"Erreur lors de l'appel à l'API Mistral: {str(e)}"

def decrire_contexte_ecran():
    """Capture et analyse l'écran actuel pour décrire le contexte"""
    print("Capture de l'écran en cours...")
    image = capture_ecran()
    
    print("Encodage de l'image...")
    image_base64 = encoder_image_base64(image)
    
    print("Analyse de l'image avec Pixtral...")
    description = analyser_image_avec_pixtral(image_base64)
    
    # Lire la description à haute voix
    if description and not description.startswith("Erreur:"):
        ajouter_texte_a_lire(description)
    
    return description

def localiser_element_ecran(element_description):
    """
    Localise un élément sur l'écran en fonction de sa description
    et retourne ses coordonnées (x, y)
    """
    print(f"Recherche de l'élément: {element_description}")
    
    # Capturer l'écran
    image = capture_ecran()
    
    # Obtenir les dimensions de l'écran
    screen_width, screen_height = pyautogui.size()
    print(f"Dimensions de l'écran: {screen_width}x{screen_height}")
    
    # Utiliser OCR pour trouver du texte
    try:
        import pytesseract
        from PIL import ImageEnhance
        
        # Améliorer le contraste de l'image pour une meilleure reconnaissance
        enhancer = ImageEnhance.Contrast(image)
        enhanced_image = enhancer.enhance(1.5)
        
        # Utiliser OCR pour trouver du texte
        text_data = pytesseract.image_to_data(enhanced_image, lang='fra', output_type=pytesseract.Output.DICT)
        
        # Rechercher des correspondances avec la description
        element_words = element_description.lower().split()
        best_match = None
        best_match_score = 0
        
        for i, text in enumerate(text_data['text']):
            if text.strip():
                text_lower = text.lower()
                # Calculer un score de correspondance simple
                score = sum(1 for word in element_words if word in text_lower)
                if score > best_match_score:
                    best_match_score = score
                    x = text_data['left'][i] + text_data['width'][i] // 2
                    y = text_data['top'][i] + text_data['height'][i] // 2
                    best_match = (x, y)
        
        if best_match and best_match_score >= len(element_words) / 2:
            print(f"Élément trouvé par OCR aux coordonnées: {best_match}")
            return best_match
    except Exception as e:
        print(f"OCR non disponible ou erreur: {e}")
    
    # Si OCR échoue, essayer avec OpenCV pour détecter des éléments visuels
    try:
        # Vérifier si OpenCV est disponible
        try:
            import cv2
            import numpy as np
            cv2_available = True
        except ImportError:
            print("Module OpenCV (cv2) non installé. Utilisez 'pip install opencv-python' pour l'installer.")
            cv2_available = False
            return None
        
        if not cv2_available:
            return None
            
        # Convertir l'image PIL en format OpenCV
        img = np.array(image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 1. Détection des contours (pour les boutons, zones cliquables)
        # Utiliser une méthode adaptative pour mieux gérer les variations de luminosité
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                               cv2.THRESH_BINARY_INV, 11, 2)
        contours, _ = cv2.findContours(adaptive_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer les contours par taille et forme
        ui_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 100 < area < 50000:  # Filtrer par taille
                # Calculer le ratio largeur/hauteur pour identifier les éléments d'interface
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h if h > 0 else 0
                
                # Les éléments d'interface ont souvent un ratio largeur/hauteur entre 1:3 et 5:1
                if 0.3 < aspect_ratio < 5:
                    ui_contours.append((cnt, x, y, w, h))
        
        # 2. Détection des éléments d'interface spécifiques
        # Détecter les rectangles (boutons, zones de texte, etc.)
        rectangles = []
        for cnt, x, y, w, h in ui_contours:
            # Approximer le contour pour détecter les formes rectangulaires
            epsilon = 0.04 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            # Les rectangles ont généralement 4 sommets
            if len(approx) == 4:
                rectangles.append((x, y, w, h))
        
        # 3. Détection des éléments actifs (zones plus claires/colorées)
        # Appliquer un filtre de détection de bords pour trouver les éléments saillants
        edges = cv2.Canny(img, 50, 150)
        
        # Dilater les bords pour connecter les lignes proches
        kernel = np.ones((3, 3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Trouver les contours des éléments saillants
        edge_contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        edge_contours = [cnt for cnt in edge_contours if cv2.contourArea(cnt) > 100]
        
        # 4. Combiner les résultats et sélectionner le meilleur candidat
        all_elements = []
        
        # Ajouter les rectangles détectés
        for x, y, w, h in rectangles:
            center_x = x + w // 2
            center_y = y + h // 2
            all_elements.append((center_x, center_y, w * h))  # Coordonnées et taille
        
        # Ajouter les contours d'interface
        for cnt, x, y, w, h in ui_contours:
            center_x = x + w // 2
            center_y = y + h // 2
            all_elements.append((center_x, center_y, w * h))
        
        # Ajouter les éléments saillants
        for cnt in edge_contours:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                center_x = int(M["m10"] / M["m00"])
                center_y = int(M["m01"] / M["m00"])
                area = cv2.contourArea(cnt)
                all_elements.append((center_x, center_y, area))
        
        if all_elements:
            # Obtenir les dimensions de l'écran
            screen_width, screen_height = pyautogui.size()
            screen_center_x, screen_center_y = screen_width // 2, screen_height // 2
            
            # Trouver l'élément le plus proche du centre de l'écran
            # Pondérer par la distance et la taille (préférer les éléments plus grands et plus centraux)
            best_element = min(all_elements, 
                              key=lambda e: (((e[0] - screen_center_x) ** 2 + (e[1] - screen_center_y) ** 2) ** 0.5) / (e[2] ** 0.3))
            
            cX, cY = best_element[0], best_element[1]
            print(f"Élément visuel trouvé aux coordonnées: ({cX}, {cY})")
            return (cX, cY)
    except Exception as e:
        print(f"Erreur lors de la détection visuelle: {e}")
    
    print("Élément non trouvé sur l'écran")
    return None
    
def detecter_elements_interactifs(image):
    """
    Détecte les éléments interactifs sur l'écran (boutons, liens, champs de texte, etc.)
    Retourne une liste de tuples (x, y, largeur, hauteur, score) pour chaque élément détecté
    """
    try:
        # Vérifier si OpenCV est disponible
        try:
            import cv2
            import numpy as np
            cv2_available = True
        except ImportError:
            print("Module OpenCV (cv2) non installé. Utilisez 'pip install opencv-python' pour l'installer.")
            return []
            
        # Convertir l'image PIL en format OpenCV
        img = np.array(image)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Obtenir les dimensions de l'image
        height, width = img.shape[:2]
        
        # Liste pour stocker les éléments détectés
        elements = []
        
        # Utiliser les fonctions spécialisées pour détecter les formes et couleurs
        elements += detecter_formes_geometriques(img)
        elements += detecter_elements_par_couleur(img)
        
        # 1. Détection des boutons et zones cliquables
        # Convertir en HSV pour mieux détecter les couleurs distinctives des éléments d'interface
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Détecter les zones de couleur bleue (souvent utilisées pour les liens et boutons)
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([140, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Détecter les zones de couleur verte (souvent utilisées pour les boutons d'action)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # Combiner les masques
        color_mask = cv2.bitwise_or(blue_mask, green_mask)
        
        # Trouver les contours des zones colorées
        color_contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Ajouter les zones colorées à la liste des éléments
        for cnt in color_contours:
            if cv2.contourArea(cnt) > 100:  # Ignorer les très petites zones
                x, y, w, h = cv2.boundingRect(cnt)
                # Score plus élevé pour les éléments colorés (probablement interactifs)
                elements.append((x + w//2, y + h//2, w, h, 0.8))
        
        # 2. Détection des rectangles et formes géométriques (boutons, champs de saisie)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Utiliser Canny pour détecter les bords
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilater les bords pour fermer les contours
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Trouver les contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer et ajouter les rectangles à la liste des éléments
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 100 < area < 50000:  # Filtrer par taille
                # Approximer le contour pour détecter les formes
                epsilon = 0.04 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Vérifier si c'est un rectangle (4 sommets)
                if len(approx) == 4:
                    # Calculer le ratio largeur/hauteur
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    # Les boutons et champs de saisie ont souvent un ratio entre 1:3 et 5:1
                    if 0.3 < aspect_ratio < 5:
                        # Score basé sur la forme rectangulaire
                        elements.append((x + w//2, y + h//2, w, h, 0.6))
        
        # 3. Détection des zones de contraste élevé (souvent des éléments interactifs)
        # Calculer le gradient de l'image
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        
        # Normaliser le gradient
        gradient_magnitude = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # Seuiller pour obtenir les zones de fort contraste
        _, high_contrast = cv2.threshold(gradient_magnitude, 100, 255, cv2.THRESH_BINARY)
        
        # Trouver les contours des zones de fort contraste
        contrast_contours, _ = cv2.findContours(high_contrast, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Ajouter les zones de fort contraste à la liste des éléments
        for cnt in contrast_contours:
            if cv2.contourArea(cnt) > 200:  # Ignorer les très petites zones
                x, y, w, h = cv2.boundingRect(cnt)
                # Score plus faible pour les zones de contraste (moins fiables)
                elements.append((x + w//2, y + h//2, w, h, 0.4))
        
        return elements
    except Exception as e:
        print(f"Erreur lors de la détection des éléments interactifs: {e}")
        return []

def detecter_formes_geometriques(img):
    """
    Détecte les formes géométriques (triangles, carrés, rectangles, cercles) dans l'image
    Retourne une liste de tuples (x, y, largeur, hauteur, score, forme)
    """
    try:
        import cv2
        import numpy as np
        
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Flou pour réduire le bruit
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Détection des contours avec Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilater les contours pour fermer les petits écarts
        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Trouver les contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Liste pour stocker les formes détectées
        formes_detectees = []
        
        for cnt in contours:
            # Ignorer les très petits contours
            if cv2.contourArea(cnt) < 100:
                continue
                
            # Approximer le contour
            epsilon = 0.04 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            
            # Obtenir les coordonnées et dimensions du rectangle englobant
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Centre de l'élément
            cx, cy = x + w//2, y + h//2
            
            # Déterminer la forme en fonction du nombre de sommets
            if len(approx) == 3:
                forme = "triangle"
                score = 0.95  # Score élevé pour les triangles car facilement identifiables
            elif len(approx) == 4:
                # Différencier carré et rectangle
                aspect_ratio = float(w) / h
                if 0.9 <= aspect_ratio <= 1.1:
                    forme = "carré"
                    score = 0.9
                else:
                    forme = "rectangle"
                    score = 0.85
            elif len(approx) >= 5 and len(approx) <= 8:
                # Détecter les cercles par circularité
                area = cv2.contourArea(cnt)
                perimeter = cv2.arcLength(cnt, True)
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                if circularity > 0.7:
                    forme = "cercle"
                    score = 0.9
                else:
                    forme = "polygone"
                    score = 0.7
            else:
                forme = "forme_complexe"
                score = 0.6
            
            # Ajouter la couleur à l'information sur la forme
            couleur = determiner_couleur_predominante(img, cnt)
            
            # Stocker les informations de forme avec couleur
            info_element = {
                "x": cx,
                "y": cy,
                "largeur": w,
                "hauteur": h,
                "score": score,
                "forme": forme,
                "couleur": couleur,
                "description": f"{couleur} {forme}" if couleur else forme
            }
            
            formes_detectees.append((cx, cy, w, h, score, info_element))
            
        return formes_detectees
    except Exception as e:
        print(f"Erreur lors de la détection des formes géométriques: {e}")
        return []

def determiner_couleur_predominante(img, contour):
    """Détermine la couleur prédominante dans la région délimitée par le contour"""
    import cv2
    import numpy as np
    
    try:
        # Créer un masque pour le contour
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, -1)
        
        # Appliquer le masque à l'image
        masked_img = cv2.bitwise_and(img, img, mask=mask)
        
        # Convertir en HSV pour une meilleure analyse des couleurs
        hsv = cv2.cvtColor(masked_img, cv2.COLOR_BGR2HSV)
        
        # Ignorer les pixels noirs (fond)
        non_zero_pixels = hsv[np.where(mask > 0)]
        
        if len(non_zero_pixels) == 0:
            return None
            
        # Calculer la moyenne des valeurs HSV
        mean_hsv = np.mean(non_zero_pixels, axis=0)
        
        # Définir les plages de couleurs en HSV
        hue = mean_hsv[0]
        saturation = mean_hsv[1]
        value = mean_hsv[2]
        
        # Si la saturation est trop faible, c'est probablement du gris/noir/blanc
        if saturation < 50:
            if value < 50:
                return "noir"
            elif value > 200:
                return "blanc"
            else:
                return "gris"
                
        # Déterminer la couleur en fonction de la teinte (hue)
        if 0 <= hue < 15 or 165 <= hue <= 180:
            return "rouge"
        elif 15 <= hue < 30:
            return "orange"
        elif 30 <= hue < 45:
            return "jaune"
        elif 45 <= hue < 75:
            return "vert"
        elif 75 <= hue < 105:
            return "turquoise"
        elif 105 <= hue < 135:
            return "bleu"
        elif 135 <= hue < 165:
            return "violet"
        else:
            return "inconnu"
    except Exception as e:
        print(f"Erreur lors de la détermination de la couleur: {e}")
        return None

def detecter_elements_par_couleur(img):
    """
    Détecte les éléments de couleurs spécifiques dans l'image
    Retourne une liste de tuples (x, y, largeur, hauteur, score, info)
    """
    try:
        import cv2
        import numpy as np
        
        # Définir les plages de couleurs en HSV
        couleurs_hsv = {
            "rouge1": (np.array([0, 100, 100]), np.array([10, 255, 255])),
            "rouge2": (np.array([160, 100, 100]), np.array([180, 255, 255])),  # Rouge est à cheval sur 0°
            "orange": (np.array([10, 100, 100]), np.array([25, 255, 255])),
            "jaune": (np.array([25, 100, 100]), np.array([35, 255, 255])),
            "vert": (np.array([35, 100, 100]), np.array([85, 255, 255])),
            "bleu": (np.array([85, 100, 100]), np.array([130, 255, 255])),
            "violet": (np.array([130, 100, 100]), np.array([160, 255, 255]))
        }
        
        # Convertir en HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        elements = []
        
        # Pour chaque couleur, trouver les régions correspondantes
        for nom_couleur, (lower, upper) in couleurs_hsv.items():
            # Créer un masque pour cette couleur
            if "rouge" in nom_couleur:
                # Cas spécial pour le rouge (à cheval sur 0°/180°)
                if nom_couleur == "rouge1":
                    mask = cv2.inRange(hsv, lower, upper)
                else:  # rouge2
                    mask = cv2.inRange(hsv, lower, upper)
                    
                # Si on traite la deuxième plage de rouge, fusionner avec le masque existant
                if nom_couleur == "rouge2":
                    continue  # On traitera les deux masques rouges ensemble
            else:
                mask = cv2.inRange(hsv, lower, upper)
            
            # Traitement spécial pour le rouge: combiner les deux plages
            if nom_couleur == "rouge1":
                lower_rouge2, upper_rouge2 = couleurs_hsv["rouge2"]
                mask_rouge2 = cv2.inRange(hsv, lower_rouge2, upper_rouge2)
                mask = cv2.bitwise_or(mask, mask_rouge2)
                nom_couleur = "rouge"  # Simplifier le nom
            
            # Éliminer le bruit
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Trouver les contours
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Pour chaque contour suffisamment grand
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 200:  # Ignorer les très petites régions
                    x, y, w, h = cv2.boundingRect(cnt)
                    cx, cy = x + w//2, y + h//2
                    
                    # Déterminer la forme approximative
                    epsilon = 0.04 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)
                    
                    if len(approx) == 3:
                        forme = "triangle"
                    elif len(approx) == 4:
                        # Différencier carré et rectangle
                        aspect_ratio = float(w) / h
                        if 0.9 <= aspect_ratio <= 1.1:
                            forme = "carré"
                        else:
                            forme = "rectangle"
                    elif len(approx) >= 5 and len(approx) <= 8:
                        forme = "cercle"
                    else:
                        forme = "forme"
                    
                    # Simplifier le nom de la couleur (supprimer les numéros)
                    couleur_simple = nom_couleur.rstrip("12")
                    
                    # Score élevé pour les éléments de couleur (très visibles)
                    score = 0.9
                    
                    # Informations complètes sur l'élément
                    info_element = {
                        "x": cx,
                        "y": cy,
                        "largeur": w,
                        "hauteur": h,
                        "score": score,
                        "forme": forme,
                        "couleur": couleur_simple,
                        "description": f"{couleur_simple} {forme}"
                    }
                    
                    elements.append((cx, cy, w, h, score, info_element))
        
        return elements
    except Exception as e:
        print(f"Erreur lors de la détection des éléments par couleur: {e}")
        return []

def localiser_element_par_attributs(attributs):
    """
    Localise un élément selon ses attributs (couleur, forme, etc.)
    
    Args:
        attributs: dict ou str - Description de l'élément recherché
        
    Returns:
        tuple (x, y) des coordonnées ou None si non trouvé
    """
    try:
        import numpy as np
        # Si attributs est une chaîne, la convertir en dictionnaire
        if isinstance(attributs, str):
            mots = attributs.lower().split()
            attr_dict = {}
            
            # Liste des couleurs reconnues
            couleurs = ["rouge", "bleu", "vert", "jaune", "orange", "violet", "noir", "blanc", "gris"]
            # Liste des formes reconnues
            formes = ["bouton", "carré", "rectangle", "cercle", "triangle", "icône", "polygone"]
            
            # Extraire couleurs et formes des mots
            for mot in mots:
                if mot in couleurs:
                    attr_dict["couleur"] = mot
                elif mot in formes:
                    attr_dict["forme"] = mot
            
            attributs = attr_dict
        
        # Capture de l'écran
        image = capture_ecran()
        
        # Obtenir tous les éléments détectés
        elements_formes = detecter_formes_geometriques(np.array(image))
        elements_couleurs = detecter_elements_par_couleur(np.array(image))
        
        # Combiner les éléments
        tous_elements = elements_formes + elements_couleurs
        
        # Filtrer selon les attributs
        elements_filtres = []
        
        for element in tous_elements:
            info = element[5]  # Le 6ème élément contient les informations détaillées
            
            match = True
            # Vérifier chaque attribut demandé
            for attr, valeur in attributs.items():
                if attr == "couleur" and "couleur" in info:
                    if valeur != info["couleur"]:
                        match = False
                        break
                elif attr == "forme" and "forme" in info:
                    # Gestion spéciale pour "bouton" qui peut correspondre à rectangle ou carré
                    if valeur == "bouton" and info["forme"] not in ["rectangle", "carré"]:
                        match = False
                        break
                    elif valeur != "bouton" and valeur != info["forme"]:
                        match = False
                        break
            
            if match:
                # Calculer un score de pertinence
                score = info["score"]
                # Bonus pour les éléments qui correspondent à plusieurs attributs
                score += 0.1 * len(attributs)
                elements_filtres.append((info["x"], info["y"], info["largeur"], info["hauteur"], score, info))
        
        # Si des éléments correspondent, retourner celui avec le meilleur score
        if elements_filtres:
            # Trier par score (du plus élevé au plus bas)
            elements_filtres.sort(key=lambda e: e[4], reverse=True)
            meilleur_element = elements_filtres[0]
            return (meilleur_element[0], meilleur_element[1])  # Coordonnées x, y
        
        return None
    except Exception as e:
        print(f"Erreur lors de la localisation par attributs: {e}")
        return None
