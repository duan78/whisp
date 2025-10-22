"""
Module de gestion des commandes de navigateur pour l'assistant Whisp
"""

import webbrowser
import pyautogui
import re
from window_manager import detect_application_context, is_browser_active, get_active_browser, get_active_browser_tab_info

# Dictionnaire des sites web populaires avec leurs URLs
SITES_POPULAIRES = {
    # Sites internationaux
    "google": "https://www.google.fr",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://github.com",
    "amazon": "https://www.amazon.fr",
    "netflix": "https://www.netflix.com",
    "wikipedia": "https://fr.wikipedia.org",
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
    "yahoo": "https://fr.yahoo.com",
    "twitch": "https://www.twitch.tv",
    "reddit": "https://www.reddit.com",
    "pinterest": "https://www.pinterest.fr",
    "tiktok": "https://www.tiktok.com",
    "snapchat": "https://www.snapchat.com",
    "discord": "https://discord.com",
    "spotify": "https://open.spotify.com",
    "deezer": "https://www.deezer.com",
    "perplexity": "https://www.perplexity.ai",
    "chatgpt": "https://chat.openai.com",
    "claude": "https://claude.ai",
    "bing": "https://www.bing.com",
    "maps": "https://maps.google.com",
    "drive": "https://drive.google.com",
    "dropbox": "https://www.dropbox.com",
    "onedrive": "https://onedrive.live.com",
    
    # Sites professionnels
    "clickup": "https://app.clickup.com",
    "trello": "https://trello.com",
    "asana": "https://app.asana.com",
    "notion": "https://www.notion.so",
    "jira": "https://www.atlassian.com/software/jira",
    "confluence": "https://www.atlassian.com/software/confluence",
    "slack": "https://slack.com",
    "teams": "https://teams.microsoft.com",
    "zoom": "https://zoom.us",
    "meet": "https://meet.google.com",
    "webex": "https://www.webex.com",
    "salesforce": "https://www.salesforce.com",
    "hubspot": "https://www.hubspot.com",
    "zendesk": "https://www.zendesk.fr",
    "freshdesk": "https://freshdesk.com",
    "monday": "https://monday.com",
    "airtable": "https://airtable.com",
    "figma": "https://www.figma.com",
    "canva": "https://www.canva.com",
    "miro": "https://miro.com",
    "tableau": "https://www.tableau.com",
    "power bi": "https://powerbi.microsoft.com",
    "looker": "https://looker.com",
    "quickbooks": "https://quickbooks.intuit.com",
    "xero": "https://www.xero.com",
    "sage": "https://www.sage.com",
    "docusign": "https://www.docusign.fr",
    "adobe": "https://www.adobe.com",
    "office": "https://www.office.com",
    "google workspace": "https://workspace.google.com",
    
    # Sites d'actualités français
    "le monde": "https://www.lemonde.fr",
    "le figaro": "https://www.lefigaro.fr",
    "le parisien": "https://www.leparisien.fr",
    "liberation": "https://www.liberation.fr",
    "les echos": "https://www.lesechos.fr",
    "l'equipe": "https://www.lequipe.fr",
    "france info": "https://www.francetvinfo.fr",
    "france 24": "https://www.france24.com/fr",
    "bfm tv": "https://www.bfmtv.com",
    "cnews": "https://www.cnews.fr",
    "lci": "https://www.lci.fr",
    "mediapart": "https://www.mediapart.fr",
    "le point": "https://www.lepoint.fr",
    "l'express": "https://www.lexpress.fr",
    "marianne": "https://www.marianne.net",
    "telerama": "https://www.telerama.fr",
    "le nouvel obs": "https://www.nouvelobs.com",
    "charlie hebdo": "https://charliehebdo.fr",
    "le canard enchaine": "https://www.lecanardenchaine.fr",
    "courrier international": "https://www.courrierinternational.com",
    "la croix": "https://www.la-croix.com",
    "l'humanite": "https://www.humanite.fr",
    "challenges": "https://www.challenges.fr",
    "capital": "https://www.capital.fr",
    "ouest france": "https://www.ouest-france.fr",
    "sud ouest": "https://www.sudouest.fr",
    "la depeche": "https://www.ladepeche.fr",
    "20 minutes": "https://www.20minutes.fr",
    
    # Sites d'actualités internationaux
    "bbc": "https://www.bbc.com",
    "bbc news": "https://www.bbc.com/news",
    "cnn": "https://www.cnn.com",
    "the new york times": "https://www.nytimes.com",
    "the washington post": "https://www.washingtonpost.com",
    "the guardian": "https://www.theguardian.com",
    "the times": "https://www.thetimes.co.uk",
    "the economist": "https://www.economist.com",
    "financial times": "https://www.ft.com",
    "wall street journal": "https://www.wsj.com",
    "bloomberg": "https://www.bloomberg.com",
    "reuters": "https://www.reuters.com",
    "associated press": "https://apnews.com",
    "al jazeera": "https://www.aljazeera.com",
    "euronews": "https://www.euronews.com",
    "der spiegel": "https://www.spiegel.de",
    "die welt": "https://www.welt.de",
    "el pais": "https://elpais.com",
    "el mundo": "https://www.elmundo.es",
    "la repubblica": "https://www.repubblica.it",
    "corriere della sera": "https://www.corriere.it",
    "le soir": "https://www.lesoir.be",
    "la libre belgique": "https://www.lalibre.be",
    "le temps": "https://www.letemps.ch",
    "nrc": "https://www.nrc.nl",
    "politico": "https://www.politico.eu",
    "the daily mail": "https://www.dailymail.co.uk",
    "the independent": "https://www.independent.co.uk",
    "the mirror": "https://www.mirror.co.uk",
    "the sun": "https://www.thesun.co.uk",
    
    # Sites français
    "le monde": "https://www.lemonde.fr",
    "le figaro": "https://www.lefigaro.fr",
    "le parisien": "https://www.leparisien.fr",
    "liberation": "https://www.liberation.fr",
    "les echos": "https://www.lesechos.fr",
    "l'equipe": "https://www.lequipe.fr",
    "france info": "https://www.francetvinfo.fr",
    "france 24": "https://www.france24.com/fr",
    "bfm tv": "https://www.bfmtv.com",
    "tf1": "https://www.tf1.fr",
    "france 2": "https://www.france.tv/france-2",
    "france 3": "https://www.france.tv/france-3",
    "m6": "https://www.6play.fr",
    "canal plus": "https://www.canalplus.com",
    "arte": "https://www.arte.tv/fr",
    "ouest france": "https://www.ouest-france.fr",
    "sud ouest": "https://www.sudouest.fr",
    "la depeche": "https://www.ladepeche.fr",
    "20 minutes": "https://www.20minutes.fr",
    "mediapart": "https://www.mediapart.fr",
    "le point": "https://www.lepoint.fr",
    "l'express": "https://www.lexpress.fr",
    "marianne": "https://www.marianne.net",
    "telerama": "https://www.telerama.fr",
    "le nouvel obs": "https://www.nouvelobs.com",
    "charlie hebdo": "https://charliehebdo.fr",
    "le canard enchaine": "https://www.lecanardenchaine.fr",
    "courrier international": "https://www.courrierinternational.com",
    "la croix": "https://www.la-croix.com",
    "l'humanite": "https://www.humanite.fr",
    "challenges": "https://www.challenges.fr",
    "capital": "https://www.capital.fr",
    "doctissimo": "https://www.doctissimo.fr",
    "allocine": "https://www.allocine.fr",
    "leboncoin": "https://www.leboncoin.fr",
    "seloger": "https://www.seloger.com",
    "pap": "https://www.pap.fr",
    "pole emploi": "https://www.pole-emploi.fr",
    "indeed": "https://fr.indeed.com",
    "service public": "https://www.service-public.fr",
    "impots": "https://www.impots.gouv.fr",
    "ameli": "https://www.ameli.fr",
    "caf": "https://www.caf.fr",
    "sncf": "https://www.sncf-connect.com",
    "ratp": "https://www.ratp.fr",
    "meteo france": "https://meteofrance.com",
    "la poste": "https://www.laposte.fr",
    "fnac": "https://www.fnac.com",
    "darty": "https://www.darty.com",
    "cdiscount": "https://www.cdiscount.com",
    "boulanger": "https://www.boulanger.com",
    "carrefour": "https://www.carrefour.fr",
    "leclerc": "https://www.e.leclerc",
    "auchan": "https://www.auchan.fr",
    "intermarche": "https://www.intermarche.com",
    "monoprix": "https://www.monoprix.fr",
    "decathlon": "https://www.decathlon.fr",
    "leroy merlin": "https://www.leroymerlin.fr",
    "ikea": "https://www.ikea.com/fr",
    "castorama": "https://www.castorama.fr",
    "bricorama": "https://www.bricorama.fr",
    "but": "https://www.but.fr",
    "conforama": "https://www.conforama.fr",
    "maison du monde": "https://www.maisonsdumonde.com",
    "la redoute": "https://www.laredoute.fr",
    "zalando": "https://www.zalando.fr",
    "vinted": "https://www.vinted.fr",
    "showroomprive": "https://www.showroomprive.com",
    "veepee": "https://www.veepee.fr",
    "sarenza": "https://www.sarenza.com",
    "sephora": "https://www.sephora.fr",
    "nocibe": "https://www.nocibe.fr",
    "marionnaud": "https://www.marionnaud.fr",
    "yves rocher": "https://www.yves-rocher.fr",
    "sephora": "https://www.sephora.fr",
    "nocibe": "https://www.nocibe.fr",
    "marionnaud": "https://www.marionnaud.fr",
    "yves rocher": "https://www.yves-rocher.fr"
}

def executer_commande_navigateur(texte):
    """Exécute des commandes de navigateur en fonction du texte transcrit"""
    texte_original = texte
    texte = texte.lower().strip()
    
    # Vérification des commandes simples et directes
    if texte == "ferme l'onglet" or texte == "ferme onglet" or texte == "fermez l'onglet" or texte == "fermez l'onglet.":
        pyautogui.hotkey('ctrl', 'w')
        return "Onglet fermé"
    elif texte == "onglet précédent":
        pyautogui.hotkey('ctrl', 'shift', 'tab')
        return "Navigation vers l'onglet précédent"
    elif texte == "onglet suivant":
        pyautogui.hotkey('ctrl', 'tab')
        return "Navigation vers l'onglet suivant"
    
    # Détecter le contexte du navigateur
    context = detect_application_context()
    browser_active = context["is_browser"]
    browser_name = context["browser_name"]
    tab_url = context["tab_url"]
    tab_title = context["tab_title"]
    
    print(f"Contexte navigateur: Actif={browser_active}, Navigateur={browser_name}, Titre onglet={tab_title}")
    
    # ===== NAVIGATION ET APPLICATIONS =====
    if any(cmd in texte for cmd in ["ouvre le navigateur", "lance le navigateur", "démarre le navigateur", 
                                    "ouvrir le navigateur", "lancer le navigateur", "démarrer le navigateur",
                                    "ouvre navigateur", "lance navigateur", "démarre navigateur", 
                                    "ouvrir navigateur", "lancer navigateur", "démarrer navigateur",
                                    "ouvre le browser", "lance le browser", "démarre le browser",
                                    "ouvre browser", "lance browser", "démarre browser",
                                    "ouvre chrome", "lance chrome", "démarre chrome",
                                    "ouvre firefox", "lance firefox", "démarre firefox",
                                    "ouvre edge", "lance edge", "démarre edge"]):
        webbrowser.open('https://www.google.com')
        return "Navigateur ouvert"
    
    elif any(cmd in texte for cmd in ["ferme la fenêtre", "ferme cette page", "fermer la fenêtre", "fermer cette page",
                                     "ferme fenêtre", "fermer fenêtre", "ferme page", "fermer page",
                                     "ferme la page", "fermer la page", "ferme cette fenêtre", "fermer cette fenêtre",
                                     "quitte la fenêtre", "quitter la fenêtre", "quitte cette fenêtre", "quitter cette fenêtre",
                                     "quitte la page", "quitter la page", "quitte cette page", "quitter cette page",
                                     "ferme l'application", "fermer l'application", "quitte l'application", "quitter l'application"]):
        pyautogui.hotkey('alt', 'f4')
        return "Fenêtre fermée"
    
    elif any(cmd in texte for cmd in ["ouvre youtube", "lance youtube", "démarre youtube", 
                                     "ouvrir youtube", "lancer youtube", "démarrer youtube",
                                     "va sur youtube", "aller sur youtube", "accède à youtube", 
                                     "accéder à youtube", "visite youtube", "visiter youtube",
                                     "ouvre site youtube", "ouvrir site youtube"]):
        webbrowser.open('https://www.youtube.com')
        return "YouTube ouvert"
        
    elif any(cmd in texte for cmd in ["ouvre facebook", "lance facebook", "démarre facebook", 
                                     "ouvrir facebook", "lancer facebook", "démarrer facebook",
                                     "va sur facebook", "aller sur facebook", "accède à facebook", 
                                     "accéder à facebook", "visite facebook", "visiter facebook",
                                     "ouvre site facebook", "ouvrir site facebook"]):
        webbrowser.open('https://www.facebook.com')
        return "Facebook ouvert"
    
    elif any(cmd in texte for cmd in ["ouvre gmail", "lance gmail", "démarre gmail", 
                                     "ouvrir gmail", "lancer gmail", "démarrer gmail",
                                     "va sur gmail", "aller sur gmail", "accède à gmail", 
                                     "accéder à gmail", "visite gmail", "visiter gmail",
                                     "ouvre site gmail", "ouvrir site gmail", 
                                     "ouvre ma boîte mail", "ouvrir ma boîte mail",
                                     "ouvre mes mails", "ouvrir mes mails", 
                                     "ouvre mes emails", "ouvrir mes emails"]):
        webbrowser.open('https://mail.google.com')
        return "Gmail ouvert"
    
    # Déplacer les commandes d'onglet avant les commandes de page pour éviter les confusions
    elif any(cmd in texte for cmd in ["onglet suivant", "tab suivante", "tab suivant", "onglet d'après", 
                                     "prochain onglet", "prochaine tab", "onglet après", "tab après",
                                     "va à l'onglet suivant", "aller à l'onglet suivant", "passe à l'onglet suivant",
                                     "passer à l'onglet suivant", "change d'onglet", "changer d'onglet",
                                     "onglet à droite", "tab à droite"]):
        pyautogui.hotkey('ctrl', 'tab')
        return "Navigation vers l'onglet suivant"
        
    elif any(cmd in texte for cmd in ["onglet précédent", "tab précédente", "tab précédent", "onglet d'avant", 
                                     "onglet avant", "tab avant", "onglet précédente", "tab précédente",
                                     "va à l'onglet précédent", "aller à l'onglet précédent", "passe à l'onglet précédent",
                                     "passer à l'onglet précédent", "retourne à l'onglet précédent", 
                                     "retourner à l'onglet précédent", "onglet à gauche", "tab à gauche"]) or texte.strip().lower() == "onglet précédent":
        pyautogui.hotkey('ctrl', 'shift', 'tab')
        return "Navigation vers l'onglet précédent"
        
    elif any(cmd in texte for cmd in ["page précédente", "retourne en arrière", "retourner en arrière", 
                                     "reviens en arrière", "revenir en arrière", "retourne à la page précédente", 
                                     "retourner à la page précédente", "va à la page précédente", 
                                     "aller à la page précédente", "page d'avant", "retour", "précédent",
                                     "retourne", "reviens", "recule", "reculer"]):
        pyautogui.hotkey('alt', 'left')
        return "Navigation vers la page précédente"
        
    elif any(cmd in texte for cmd in ["page suivante", "avance", "avancer", "va à la page suivante", 
                                     "aller à la page suivante", "page d'après", "suivant", 
                                     "continue", "continuer", "page après", "avance d'une page",
                                     "avancer d'une page", "va en avant", "aller en avant"]):
        pyautogui.hotkey('alt', 'right')
        return "Navigation vers la page suivante"
        
    elif any(cmd in texte for cmd in ["actualise la page", "rafraîchis la page", "actualiser la page", "rafraîchir la page",
                                     "actualise", "rafraîchis", "actualiser", "rafraîchir", 
                                     "recharge la page", "recharger la page", "recharge", "recharger",
                                     "mets à jour la page", "mettre à jour la page", "mets à jour", "mettre à jour",
                                     "rafraîchissement", "actualisation", "rechargement", "mise à jour"]):
        pyautogui.hotkey('f5')
        return "Page actualisée"
    
    elif any(cmd in texte for cmd in ["nouvel onglet", "nouveau onglet", "ouvre un nouvel onglet", "ouvrir un nouvel onglet",
                                     "ouvre un nouveau onglet", "ouvrir un nouveau onglet", "crée un nouvel onglet", 
                                     "créer un nouvel onglet", "crée un nouveau onglet", "créer un nouveau onglet",
                                     "ajoute un onglet", "ajouter un onglet", "ouvre onglet", "ouvrir onglet",
                                     "crée onglet", "créer onglet", "ajoute onglet", "ajouter onglet", "Nouvel anglais."]):
        pyautogui.hotkey('ctrl', 't')
        return "Nouvel onglet ouvert"
        
    elif any(cmd in texte for cmd in ["ferme l'onglet", "fermer l'onglet", "ferme cet onglet", "fermer cet onglet",
                                     "ferme onglet", "fermer onglet", "supprime l'onglet", "supprimer l'onglet",
                                     "supprime cet onglet", "supprimer cet onglet", "supprime onglet", "supprimer onglet",
                                     "ferme tab", "fermer tab", "ferme cette tab", "fermer cette tab",
                                     "quitte l'onglet", "quitter l'onglet", "quitte cet onglet", "quitter cet onglet",
                                     "quitte onglet", "quitter onglet", "ferme lenglet", "ferme l'anglais", "fermer l'anglais",
                                     "ferme anglais", "fermer anglais", "ferme longuet", "fermer longuet", 
                                     "ferme longlet", "fermer longlet", "ferme langlais", "fermer langlais",
                                     "ferme l'angle", "fermer l'angle", "ferme langle", "fermer langle",
                                     "ferme l'anglet", "fermer l'anglet", "ferme langlet", "fermer langlet",
                                     "ferme l'ongle", "fermer l'ongle", "ferme longle", "fermer longle",
                                     "ferme la page", "fermer la page", "ferme cette page", "fermer cette page",
                                     "ferme l'onglet actif", "fermer l'onglet actif", "ferme l'onglet courant", "fermer l'onglet courant",
                                     "fermez l'onglet", "fermez onglet", "fermez cet onglet", "fermez cette page",
                                     "fermez l'onglet."]) or texte.strip().lower() == "ferme l'onglet":
        pyautogui.hotkey('ctrl', 'w')
        return "Onglet fermé"
    
    elif any(cmd in texte for cmd in ["onglet suivant", "tab suivante", "tab suivant", "onglet d'après", 
                                     "prochain onglet", "prochaine tab", "onglet après", "tab après",
                                     "va à l'onglet suivant", "aller à l'onglet suivant", "passe à l'onglet suivant",
                                     "passer à l'onglet suivant", "change d'onglet", "changer d'onglet",
                                     "onglet à droite", "tab à droite"]):
        pyautogui.hotkey('ctrl', 'tab')
        return "Navigation vers l'onglet suivant"
        
    elif any(cmd in texte for cmd in ["onglet précédent", "tab précédente", "tab précédent", "onglet d'avant", 
                                     "onglet avant", "tab avant", "onglet précédente", "tab précédente",
                                     "va à l'onglet précédent", "aller à l'onglet précédent", "passe à l'onglet précédent",
                                     "passer à l'onglet précédent", "retourne à l'onglet précédent", 
                                     "retourner à l'onglet précédent", "onglet à gauche", "tab à gauche"]):
        pyautogui.hotkey('ctrl', 'shift', 'tab')
        return "Navigation vers l'onglet précédent"
        
    elif any(cmd in texte for cmd in ["aller à l'adresse", "va à l'adresse", "barre d'adresse", 
                                     "sélectionne la barre d'adresse", "sélectionner la barre d'adresse",
                                     "focus barre d'adresse", "focus sur la barre d'adresse", 
                                     "sélectionne l'url", "sélectionner l'url", "change l'adresse",
                                     "changer l'adresse", "modifie l'adresse", "modifier l'adresse",
                                     "tape une adresse", "taper une adresse", "entre une adresse",
                                     "entrer une adresse", "saisir une adresse", "saisis une adresse"]):
        pyautogui.hotkey('ctrl', 'l')
        return "Barre d'adresse sélectionnée"
        
    elif any(cmd in texte for cmd in ["plein écran", "mode plein écran", "active le plein écran", "activer le plein écran",
                                     "passe en plein écran", "passer en plein écran", "affiche en plein écran", 
                                     "afficher en plein écran", "mets en plein écran", "mettre en plein écran",
                                     "désactive le plein écran", "désactiver le plein écran", "quitte le plein écran",
                                     "quitter le plein écran", "sort du plein écran", "sortir du plein écran",
                                     "bascule plein écran", "basculer plein écran", "toggle plein écran"]):
        pyautogui.press('f11')
        return "Mode plein écran activé/désactivé"
    
    elif "cherche" in texte:
        try:
            # Cas 1: "cherche [terme] sur [site]"
            if "sur" in texte:
                recherche = texte.split("cherche")[1].split("sur")[0].strip()
                site = texte.split("sur")[1].strip()
                
                if "google" in site:
                    webbrowser.open(f'https://www.google.com/search?q={recherche}')
                    return f"Recherche de '{recherche}' sur Google"
                elif "youtube" in site:
                    webbrowser.open(f'https://www.youtube.com/results?search_query={recherche}')
                    return f"Recherche de '{recherche}' sur YouTube"
                elif "wikipédia" in site:
                    webbrowser.open(f'https://fr.wikipedia.org/wiki/{recherche}')
                    return f"Recherche de '{recherche}' sur Wikipédia"
                else:
                    return f"Site de recherche '{site}' non reconnu"
            
            # Cas 2: "cherche [terme]" (sans préciser le site)
            else:
                recherche = texte.split("cherche")[1].strip()
                
                # Si un navigateur est actif, utiliser le moteur de recherche par défaut
                if browser_active:
                    # Ouvrir un nouvel onglet
                    if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                        pyautogui.hotkey('ctrl', 't')
                    elif browser_name == "firefox":
                        pyautogui.hotkey('ctrl', 't')
                    elif browser_name == "safari":
                        pyautogui.hotkey('command', 't')
                    else:
                        pyautogui.hotkey('ctrl', 't')
                    
                    # Attendre que l'onglet soit ouvert
                    pyautogui.sleep(0.5)
                    
                    # Taper la recherche et appuyer sur Entrée
                    pyautogui.write(recherche)
                    pyautogui.press('enter')
                    
                    return f"Recherche de '{recherche}' dans un nouvel onglet"
                else:
                    # Si aucun navigateur n'est actif, ouvrir Google
                    webbrowser.open(f'https://www.google.com/search?q={recherche}')
                    return f"Recherche de '{recherche}' sur Google"
        except Exception as e:
            return f"Erreur lors de la recherche: {str(e)}"
    
    # Nouvelle commande "va sur" + site
    elif "va sur" in texte or "aller sur" in texte or "ouvre le site" in texte or "ouvrir le site" in texte:
        # Extraire le nom du site
        match = None
        for pattern in ["va sur (.+)", "aller sur (.+)", "ouvre le site (.+)", "ouvrir le site (.+)"]:
            match = re.search(pattern, texte)
            if match:
                site_name = match.group(1).strip().lower()
                break
        
        if match:
            # Vérifier d'abord si le site est dans notre dictionnaire de sites populaires
            site_found = False
            for key, url in SITES_POPULAIRES.items():
                # Vérification exacte ou si le nom du site est contenu dans la clé ou vice versa
                if key == site_name or key in site_name or site_name in key:
                    site_found = True
                    # Si un navigateur est déjà ouvert, ouvrir dans un nouvel onglet
                    if browser_active:
                        # Ouvrir un nouvel onglet
                        if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                            pyautogui.hotkey('ctrl', 't')
                        elif browser_name == "firefox":
                            pyautogui.hotkey('ctrl', 't')
                        elif browser_name == "safari":
                            pyautogui.hotkey('command', 't')
                        else:
                            pyautogui.hotkey('ctrl', 't')
                        
                        # Attendre que l'onglet soit ouvert
                        pyautogui.sleep(0.5)
                        
                        # Taper l'URL et appuyer sur Entrée
                        pyautogui.write(url)
                        pyautogui.press('enter')
                        
                        return f"Ouverture de {key.capitalize()} dans un nouvel onglet"
                    else:
                        # Sinon, ouvrir dans une nouvelle fenêtre
                        webbrowser.open(url)
                        return f"Ouverture de {key.capitalize()} dans une nouvelle fenêtre"
                    
                    # Sortir de la boucle dès qu'on a trouvé une correspondance
                    break
            
            # Si le site n'est pas dans notre liste, essayer d'ouvrir directement
            if not site_found:
                if "." in site_name:  # Vérifier si c'est une URL valide
                    if not site_name.startswith(('http://', 'https://')):
                        site_name = 'https://' + site_name
                    
                    if browser_active:
                        # Ouvrir un nouvel onglet
                        if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                            pyautogui.hotkey('ctrl', 't')
                        elif browser_name == "firefox":
                            pyautogui.hotkey('ctrl', 't')
                        elif browser_name == "safari":
                            pyautogui.hotkey('command', 't')
                        else:
                            pyautogui.hotkey('ctrl', 't')
                    
                    # Attendre que l'onglet soit ouvert
                    pyautogui.sleep(0.5)
                    
                    # Taper l'URL et appuyer sur Entrée
                    pyautogui.write(site_name)
                    pyautogui.press('enter')
                    
                    return f"Ouverture de {site_name} dans un nouvel onglet"
                else:
                    webbrowser.open(site_name)
                    return f"Ouverture de {site_name} dans une nouvelle fenêtre"
            else:
                # Essayer avec .com, .fr, etc.
                site_url = f"https://www.{site_name}.com"
                
                if browser_active:
                    # Ouvrir un nouvel onglet
                    if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                        pyautogui.hotkey('ctrl', 't')
                    elif browser_name == "firefox":
                        pyautogui.hotkey('ctrl', 't')
                    elif browser_name == "safari":
                        pyautogui.hotkey('command', 't')
                    else:
                        pyautogui.hotkey('ctrl', 't')
                    
                    # Attendre que l'onglet soit ouvert
                    pyautogui.sleep(0.5)
                    
                    # Taper l'URL et appuyer sur Entrée
                    pyautogui.write(site_url)
                    pyautogui.press('enter')
                    
                    return f"Tentative d'ouverture de {site_name} dans un nouvel onglet"
                else:
                    webbrowser.open(site_url)
                    return f"Tentative d'ouverture de {site_name} dans une nouvelle fenêtre"
    
    # Commandes spécifiques au contexte de l'onglet actif
    elif any(cmd in texte for cmd in ["recharge cette page", "actualise cette page", "rafraîchis cette page",
                                     "recharge la page actuelle", "actualise la page actuelle", 
                                     "rafraîchis la page actuelle", "recharge", "actualise", "rafraîchis"]):
        if browser_active:
            pyautogui.press('f5')
            return f"Page {tab_title or 'actuelle'} actualisée"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["ferme cet onglet", "ferme l'onglet actuel", "ferme cette page",
                                     "ferme la page actuelle", "ferme onglet", "ferme page"]):
        if browser_active:
            pyautogui.hotkey('ctrl', 'w')
            return f"Onglet {tab_title or 'actuel'} fermé"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["duplique cet onglet", "duplique l'onglet actuel", "duplique cette page",
                                     "duplique la page actuelle", "clone cet onglet", "clone cette page"]):
        if browser_active:
            if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                pyautogui.hotkey('ctrl', 'shift', 'k')  # Raccourci pour dupliquer l'onglet dans Chrome/Edge
            elif browser_name == "firefox":
                # Firefox n'a pas de raccourci standard pour dupliquer un onglet
                # On peut utiliser Alt+D pour sélectionner l'URL, puis Ctrl+C, Ctrl+T, Ctrl+V, Enter
                pyautogui.hotkey('alt', 'd')
                pyautogui.sleep(0.2)
                pyautogui.hotkey('ctrl', 'c')
                pyautogui.sleep(0.2)
                pyautogui.hotkey('ctrl', 't')
                pyautogui.sleep(0.5)
                pyautogui.hotkey('ctrl', 'v')
                pyautogui.sleep(0.2)
                pyautogui.press('enter')
            elif browser_name == "safari":
                # Safari sur macOS
                pyautogui.hotkey('command', 'l')  # Sélectionner l'URL
                pyautogui.sleep(0.2)
                pyautogui.hotkey('command', 'c')  # Copier
                pyautogui.sleep(0.2)
                pyautogui.hotkey('command', 't')  # Nouvel onglet
                pyautogui.sleep(0.5)
                pyautogui.hotkey('command', 'v')  # Coller
                pyautogui.sleep(0.2)
                pyautogui.press('enter')  # Aller à l'URL
            else:
                # Méthode générique
                pyautogui.hotkey('ctrl', 'l')  # Sélectionner l'URL
                pyautogui.sleep(0.2)
                pyautogui.hotkey('ctrl', 'c')  # Copier
                pyautogui.sleep(0.2)
                pyautogui.hotkey('ctrl', 't')  # Nouvel onglet
                pyautogui.sleep(0.5)
                pyautogui.hotkey('ctrl', 'v')  # Coller
                pyautogui.sleep(0.2)
                pyautogui.press('enter')  # Aller à l'URL
                
            return f"Onglet {tab_title or 'actuel'} dupliqué"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["partage cette page", "partage cet onglet", "partage ce site",
                                     "partager cette page", "partager cet onglet", "partager ce site",
                                     "envoie cette page", "envoie cet onglet", "envoie ce site",
                                     "envoyer cette page", "envoyer cet onglet", "envoyer ce site"]):
        if browser_active:
            # Sélectionner l'URL pour la copier
            pyautogui.hotkey('ctrl', 'l')
            pyautogui.sleep(0.2)
            pyautogui.hotkey('ctrl', 'c')
            
            return f"URL de {tab_title or 'la page actuelle'} copiée dans le presse-papiers"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["ajoute aux favoris", "ajoute cette page aux favoris", 
                                     "ajoute ce site aux favoris", "marque cette page", 
                                     "marque ce site", "ajoute aux marque-pages",
                                     "ajoute cette page aux marque-pages", "ajoute ce site aux marque-pages"]):
        if browser_active:
            if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                pyautogui.hotkey('ctrl', 'd')
            elif browser_name == "firefox":
                pyautogui.hotkey('ctrl', 'd')
            elif browser_name == "safari":
                pyautogui.hotkey('command', 'd')
            else:
                pyautogui.hotkey('ctrl', 'd')
                
            return f"{tab_title or 'Page actuelle'} ajoutée aux favoris"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["affiche l'historique", "montre l'historique", "ouvre l'historique",
                                     "afficher l'historique", "montrer l'historique", "ouvrir l'historique",
                                     "voir l'historique", "consulter l'historique"]):
        if browser_active:
            if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                pyautogui.hotkey('ctrl', 'h')
            elif browser_name == "firefox":
                pyautogui.hotkey('ctrl', 'h')
            elif browser_name == "safari":
                pyautogui.hotkey('command', 'y')
            else:
                pyautogui.hotkey('ctrl', 'h')
                
            return "Historique de navigation affiché"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["affiche les téléchargements", "montre les téléchargements", 
                                     "ouvre les téléchargements", "afficher les téléchargements", 
                                     "montrer les téléchargements", "ouvrir les téléchargements",
                                     "voir les téléchargements", "consulter les téléchargements"]):
        if browser_active:
            if browser_name == "chrome" or browser_name == "edge" or browser_name == "brave":
                pyautogui.hotkey('ctrl', 'j')
            elif browser_name == "firefox":
                pyautogui.hotkey('ctrl', 'j')
            elif browser_name == "safari":
                pyautogui.hotkey('command', 'option', 'l')
            else:
                pyautogui.hotkey('ctrl', 'j')
                
            return "Téléchargements affichés"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["mode lecture", "active le mode lecture", "activer le mode lecture",
                                     "passe en mode lecture", "passer en mode lecture"]):
        if browser_active:
            if browser_name == "firefox":
                pyautogui.hotkey('ctrl', 'alt', 'r')
            elif browser_name == "safari":
                pyautogui.hotkey('shift', 'command', 'r')
            elif browser_name == "edge":
                pyautogui.hotkey('ctrl', 'shift', 'r')
            else:
                return "Mode lecture non disponible ou raccourci inconnu pour ce navigateur"
                
            return "Mode lecture activé"
        else:
            return "Aucun navigateur actif détecté"
            
    elif any(cmd in texte for cmd in ["mode navigation privée", "ouvre une fenêtre privée", 
                                     "ouvre une fenêtre de navigation privée", "mode incognito", 
                                     "ouvre une fenêtre incognito", "navigation privée", "incognito"]):
        if browser_name == "chrome" or browser_name == "brave":
            pyautogui.hotkey('ctrl', 'shift', 'n')
        elif browser_name == "firefox":
            pyautogui.hotkey('ctrl', 'shift', 'p')
        elif browser_name == "edge":
            pyautogui.hotkey('ctrl', 'shift', 'n')
        elif browser_name == "safari":
            pyautogui.hotkey('command', 'shift', 'n')
        else:
            # Ouvrir Chrome en mode incognito par défaut
            webbrowser.get('chrome %s --incognito').open('https://www.google.com')
            
        return "Fenêtre de navigation privée ouverte"
    
    return None  # Commande non reconnue
