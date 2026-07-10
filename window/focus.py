"""Activation et bascule vers une fenêtre ou une application spécifique."""

from window._common import *  # noqa: F401,F403  (imports partagés + error_handler)
from window.enumeration import obtenir_fenetres_ouvertes
from window.active_app import get_active_application

def basculer_vers_fenetre(recherche, par_titre=True, par_process=True, exact=False):
    """
    Bascule vers une fenêtre spécifique en recherchant par titre ou par nom de processus
    
    Args:
        recherche (str): Texte à rechercher dans le titre ou le nom du processus
        par_titre (bool): Rechercher dans le titre de la fenêtre
        par_process (bool): Rechercher dans le nom du processus
        exact (bool): Correspondance exacte ou partielle
        
    Returns:
        bool: True si la fenêtre a été trouvée et activée, False sinon
    """
    os_type = get_os_type()
    recherche_lower = recherche.lower()
    
    # Journalisation pour le débogage
    print(f"Tentative de basculer vers la fenêtre: '{recherche}' (titre: {par_titre}, process: {par_process}, exact: {exact})")
    
    try:
        if os_type == 'windows':
            # Obtenir la liste des fenêtres
            fenetres = obtenir_fenetres_ouvertes()
            
            # Rechercher la fenêtre correspondante
            fenetre_trouvee = None
            
            for fenetre in fenetres:
                match_titre = False
                match_process = False
                
                if par_titre and fenetre['title']:
                    if exact:
                        match_titre = fenetre['title'].lower() == recherche_lower
                    else:
                        match_titre = recherche_lower in fenetre['title'].lower()
                
                if par_process and fenetre['process_name']:
                    if exact:
                        match_process = fenetre['process_name'] == recherche_lower
                    else:
                        match_process = recherche_lower in fenetre['process_name']
                
                if match_titre or match_process:
                    fenetre_trouvee = fenetre
                    break
            
            # Si une fenêtre correspondante est trouvée, l'activer
            if fenetre_trouvee:
                hwnd = fenetre_trouvee['hwnd']
                print(f"Fenêtre trouvée: '{fenetre_trouvee['title']}' ({fenetre_trouvee['process_name']})")
                
                # Importer les modules nécessaires
                import win32gui
                import win32con
                import win32api
                import win32process
                
                # Vérifier si la fenêtre est minimisée
                placement = win32gui.GetWindowPlacement(hwnd)
                if placement[1] == win32con.SW_SHOWMINIMIZED:
                    # Restaurer la fenêtre si elle est minimisée
                    print("Restauration de la fenêtre minimisée")
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                
                # Méthode 0: Traitement spécial pour certaines applications problématiques
                try:
                    process_name = fenetre_trouvee['process_name'].lower()
                    
                    # Traitement spécial pour WhatsApp et ApplicationFrameHost
                    if "whatsapp" in process_name or "applicationframehost" in process_name:
                        # Utiliser Win+Numéro pour les applications épinglées à la barre des tâches
                        # Cette méthode est la plus fiable pour WhatsApp et les applications UWP
                        try:
                            print("Tentative avec Win+Numéro pour application spéciale")
                            
                            # Définir les constantes pour SendInput
                            KEYEVENTF_KEYDOWN = 0x0000
                            KEYEVENTF_KEYUP = 0x0002
                            VK_LWIN = 0x5B  # Touche Windows gauche
                            
                            # Créer une structure d'entrée clavier
                            class KEYBDINPUT(ctypes.Structure):
                                _fields_ = [
                                    ("wVk", ctypes.c_ushort),
                                    ("wScan", ctypes.c_ushort),
                                    ("dwFlags", ctypes.c_ulong),
                                    ("time", ctypes.c_ulong),
                                    ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                                ]
                            
                            class INPUT(ctypes.Structure):
                                _fields_ = [
                                    ("type", ctypes.c_ulong),
                                    ("ki", KEYBDINPUT),
                                    ("padding", ctypes.c_ubyte * 8)
                                ]
                            
                            # Essayer les positions 1 à 9 dans la barre des tâches
                            for position in range(1, 10):
                                # Convertir la position en code de touche virtuelle
                                vk_position = 0x30 + position  # 0x31 = 1, 0x32 = 2, etc.
                                
                                # Appuyer sur Win
                                win_down = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(win_down), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Appuyer sur le numéro
                                num_down = INPUT(1, KEYBDINPUT(vk_position, 0, KEYEVENTF_KEYDOWN, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(num_down), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Relâcher le numéro
                                num_up = INPUT(1, KEYBDINPUT(vk_position, 0, KEYEVENTF_KEYUP, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(num_up), ctypes.sizeof(INPUT))
                                time.sleep(0.1)
                                
                                # Relâcher Win
                                win_up = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYUP, 0, None))
                                ctypes.windll.user32.SendInput(1, ctypes.byref(win_up), ctypes.sizeof(INPUT))
                                time.sleep(0.3)
                                
                                # Vérifier si nous sommes sur la bonne fenêtre
                                active_hwnd = win32gui.GetForegroundWindow()
                                if active_hwnd == hwnd:
                                    print(f"Fenêtre activée via Win+{position}")
                                    return True
                                
                                # Si ce n'est pas la bonne fenêtre mais que c'est une fenêtre de la même application
                                active_app, _, _ = get_active_application()
                                if active_app.lower() == process_name:
                                    print(f"Application activée via Win+{position} (fenêtre différente)")
                                    return True
                        except Exception as e:
                            print(f"Erreur Win+Numéro pour application spéciale: {e}")
                except Exception as e:
                    print(f"Erreur traitement spécial: {e}")
                
                # Méthode 1: Utiliser SetForegroundWindow directement avec contournement des restrictions
                try:
                    print("Tentative avec SetForegroundWindow")
                    # Obtenir le PID du processus
                    pid = fenetre_trouvee['pid']
                    
                    # Contourner les restrictions de sécurité de Windows
                    # Définir les constantes nécessaires
                    SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
                    SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001
                    SPIF_SENDCHANGE = 0x2
                    
                    # Sauvegarder le timeout actuel
                    timeout_buffer = ctypes.c_ulong()
                    ctypes.windll.user32.SystemParametersInfoW(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, 
                                                             ctypes.byref(timeout_buffer), 0)
                    original_timeout = timeout_buffer.value
                    
                    # Définir le timeout à 0 pour permettre le changement immédiat
                    try:
                        ctypes.windll.user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0,
                                                                 ctypes.c_ulong(0), SPIF_SENDCHANGE)
                    except (OSError, AttributeError) as e:
                        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to set foreground timeout: {e}", ErrorSeverity.LOW)
                    
                    # Autoriser le changement de fenêtre active
                    try:
                        # ASFW_ANY permet à n'importe quelle application de prendre le focus
                        ASFW_ANY = -1
                        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
                        # Puis autoriser spécifiquement notre PID cible
                        ctypes.windll.user32.AllowSetForegroundWindow(pid)
                    except (OSError, AttributeError) as e:
                        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to allow set foreground window: {e}", ErrorSeverity.LOW)
                    
                    # Mettre la fenêtre au premier plan
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    
                    # Attacher notre thread au thread de la fenêtre cible
                    foreground_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(
                        ctypes.windll.user32.GetForegroundWindow(), None)
                    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
                    
                    if foreground_thread_id != current_thread_id:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, True)
                            attached = True
                        except (OSError, AttributeError) as e:
                            error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to attach thread input: {e}", ErrorSeverity.LOW)
                            attached = False
                    else:
                        attached = False
                    
                    # Essayer SetForegroundWindow
                    result = win32gui.SetForegroundWindow(hwnd)
                    
                    # Détacher notre thread si nécessaire
                    if attached:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
                        except (OSError, AttributeError) as e:
                            error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to detach thread input: {e}", ErrorSeverity.LOW)
                    
                    # Restaurer le timeout original
                    try:
                        ctypes.windll.user32.SystemParametersInfoW(SPI_SETFOREGROUNDLOCKTIMEOUT, 0,
                                                                 ctypes.c_ulong(original_timeout), SPIF_SENDCHANGE)
                    except (OSError, AttributeError) as e:
                        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to restore foreground timeout: {e}", ErrorSeverity.LOW)
                    
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec SetForegroundWindow")
                        return True
                except Exception as e:
                    print(f"Erreur SetForegroundWindow: {e}")
                
                # Méthode 2: Utiliser SwitchToThisWindow
                try:
                    print("Tentative avec SwitchToThisWindow")
                    # Utiliser SwitchToThisWindow pour activer la fenêtre
                    ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
                    time.sleep(0.1)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec SwitchToThisWindow")
                        return True
                except Exception as e:
                    print(f"Erreur SwitchToThisWindow: {e}")
                
                # Méthode 3: Utiliser BringWindowToTop avec technique avancée
                try:
                    print("Tentative avec BringWindowToTop et technique avancée")
                    
                    # Définir les constantes
                    ASFW_ANY = -1
                    
                    # Obtenir le thread ID de la fenêtre cible et de notre thread
                    target_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
                    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
                    
                    # Attacher notre thread au thread de la fenêtre cible
                    attached = False
                    if target_thread_id != current_thread_id:
                        try:
                            attached = ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)
                        except (OSError, AttributeError) as e:
                            error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to attach thread input: {e}", ErrorSeverity.LOW)

                    # Autoriser n'importe quelle fenêtre à devenir active
                    try:
                        ctypes.windll.user32.AllowSetForegroundWindow(ASFW_ANY)
                    except (OSError, AttributeError) as e:
                        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to allow set foreground: {e}", ErrorSeverity.LOW)
                    
                    # Mettre la fenêtre au premier plan avec plusieurs techniques
                    try:
                        # S'assurer que la fenêtre est visible
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        
                        # Forcer la fenêtre au premier plan
                        win32gui.BringWindowToTop(hwnd)
                        
                        # Simuler un clic sur la barre de titre (technique alternative)
                        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                        title_x = left + (right - left) // 2
                        title_y = top + 10  # Position approximative de la barre de titre
                        
                        # Sauvegarder la position actuelle de la souris
                        old_pos = win32api.GetCursorPos()
                        
                        # Déplacer la souris et simuler un clic
                        win32api.SetCursorPos((title_x, title_y))
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                        
                        # Restaurer la position de la souris
                        win32api.SetCursorPos(old_pos)

                        # Essayer SetForegroundWindow après le clic
                        win32gui.SetForegroundWindow(hwnd)
                    except (OSError, AttributeError) as e:
                        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Error simulating click: {e}", ErrorSeverity.LOW)
                    
                    # Détacher notre thread si nécessaire
                    if attached:
                        try:
                            ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, False)
                        except (OSError, AttributeError) as e:
                            error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to detach thread input: {e}", ErrorSeverity.LOW)
                    
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec BringWindowToTop et technique avancée")
                        return True
                except Exception as e:
                    print(f"Erreur BringWindowToTop: {e}")
                
                # Méthode 4: Utiliser PostMessage pour envoyer un message d'activation
                try:
                    print("Tentative avec PostMessage")
                    
                    # Envoyer un message WM_SYSCOMMAND avec SC_RESTORE pour restaurer la fenêtre
                    win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
                    time.sleep(0.1)
                    
                    # Envoyer un message WM_ACTIVATE pour activer la fenêtre
                    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
                    time.sleep(0.1)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée avec PostMessage")
                        return True
                except Exception as e:
                    print(f"Erreur PostMessage: {e}")
                
                # Méthode 5: Cliquer sur la barre de titre de la fenêtre
                try:
                    print("Tentative avec clic sur la barre de titre")
                    # Obtenir les coordonnées de la fenêtre
                    left, top, width, height = fenetre_trouvee['position']
                    
                    if width > 0 and height > 0:
                        # Sauvegarder la position actuelle de la souris
                        current_x, current_y = pyautogui.position()
                        
                        # Calculer la position de la barre de titre (plus précis que le centre)
                        title_x = left + (width // 2)
                        title_y = top + 15  # Environ 15 pixels depuis le haut
                        
                        # Utiliser SetCursorPos et mouse_event (plus discret que pyautogui)
                        ctypes.windll.user32.SetCursorPos(title_x, title_y)
                        time.sleep(0.1)
                        
                        # Simuler un clic gauche
                        ctypes.windll.user32.mouse_event(
                            0x0002,  # MOUSEEVENTF_LEFTDOWN
                            0, 0, 0, 0
                        )
                        time.sleep(0.05)
                        ctypes.windll.user32.mouse_event(
                            0x0004,  # MOUSEEVENTF_LEFTUP
                            0, 0, 0, 0
                        )
                        
                        time.sleep(0.1)
                        
                        # Restaurer la position de la souris
                        ctypes.windll.user32.SetCursorPos(current_x, current_y)
                        
                        # Vérifier si la fenêtre est maintenant active
                        active_hwnd = win32gui.GetForegroundWindow()
                        if active_hwnd == hwnd:
                            print("Fenêtre activée avec clic sur la barre de titre")
                            return True
                except Exception as e:
                    print(f"Erreur clic sur la barre de titre: {e}")
                
                # Méthode 6: Utiliser Win+T pour naviguer dans la barre des tâches
                try:
                    print("Tentative avec Win+T (navigation barre des tâches)")
                    
                    # Définir les constantes pour SendInput
                    KEYEVENTF_KEYDOWN = 0x0000
                    KEYEVENTF_KEYUP = 0x0002
                    VK_LWIN = 0x5B  # Touche Windows gauche
                    VK_T = 0x54     # Touche T
                    
                    # Créer une structure d'entrée clavier
                    class KEYBDINPUT(ctypes.Structure):
                        _fields_ = [
                            ("wVk", ctypes.c_ushort),
                            ("wScan", ctypes.c_ushort),
                            ("dwFlags", ctypes.c_ulong),
                            ("time", ctypes.c_ulong),
                            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
                        ]
                    
                    class INPUT(ctypes.Structure):
                        _fields_ = [
                            ("type", ctypes.c_ulong),
                            ("ki", KEYBDINPUT),
                            ("padding", ctypes.c_ubyte * 8)
                        ]
                    
                    # Appuyer sur Win+T pour activer la barre des tâches
                    win_down = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYDOWN, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(win_down), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    t_down = INPUT(1, KEYBDINPUT(VK_T, 0, KEYEVENTF_KEYDOWN, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(t_down), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    t_up = INPUT(1, KEYBDINPUT(VK_T, 0, KEYEVENTF_KEYUP, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(t_up), ctypes.sizeof(INPUT))
                    time.sleep(0.05)
                    
                    # Relâcher Win
                    win_up = INPUT(1, KEYBDINPUT(VK_LWIN, 0, KEYEVENTF_KEYUP, 0, None))
                    ctypes.windll.user32.SendInput(1, ctypes.byref(win_up), ctypes.sizeof(INPUT))
                    
                    # Naviguer dans la barre des tâches (max 10 fois)
                    for _ in range(10):
                        # Appuyer sur Tab pour naviguer
                        pyautogui.press('tab')
                        time.sleep(0.1)
                        
                        # Appuyer sur Entrée pour sélectionner
                        pyautogui.press('enter')
                        time.sleep(0.2)
                        
                        # Vérifier si nous sommes sur la bonne fenêtre
                        active_hwnd = win32gui.GetForegroundWindow()
                        if active_hwnd == hwnd:
                            print("Fenêtre activée via Win+T et navigation")
                            return True
                        
                        # Vérifier si nous sommes sur une fenêtre de la même application
                        active_app, _, _ = get_active_application()
                        if active_app.lower() == fenetre_trouvee['process_name'].lower():
                            print("Application activée via Win+T (fenêtre différente)")
                            return True
                        
                        # Revenir à la barre des tâches
                        pyautogui.hotkey('win', 't')
                        time.sleep(0.1)
                except Exception as e:
                    print(f"Erreur Win+T: {e}")
                
                # Méthode 7: Utiliser Alt+Espace puis R (Restaurer) ou M (Déplacer)
                try:
                    print("Tentative avec Alt+Espace (menu système)")
                    
                    # Appuyer sur Alt+Espace pour ouvrir le menu système
                    pyautogui.hotkey('alt', 'space')
                    time.sleep(0.1)
                    
                    # Appuyer sur R pour Restaurer
                    pyautogui.press('r')
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Espace, R")
                        return True
                    
                    # Si ça n'a pas fonctionné, essayer avec M pour Déplacer
                    pyautogui.hotkey('alt', 'space')
                    time.sleep(0.1)
                    pyautogui.press('m')
                    time.sleep(0.1)
                    
                    # Appuyer sur une flèche puis Entrée pour confirmer
                    pyautogui.press('right')
                    time.sleep(0.1)
                    pyautogui.press('enter')
                    time.sleep(0.2)
                    
                    # Vérifier si la fenêtre est maintenant active
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Espace, M")
                        return True
                except Exception as e:
                    print(f"Erreur Alt+Espace: {e}")
                
                # Si toutes les méthodes ont échoué mais que nous avons trouvé la fenêtre
                print("Fenêtre trouvée mais impossible de l'activer avec les méthodes directes")
                
                # Dernière tentative: utiliser Alt+Tab une seule fois
                try:
                    print("Tentative avec Alt+Tab simple")
                    # Simuler Alt+Tab une seule fois
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.2)
                    
                    # Vérifier si nous sommes sur la bonne fenêtre ou application
                    active_hwnd = win32gui.GetForegroundWindow()
                    if active_hwnd == hwnd:
                        print("Fenêtre activée via Alt+Tab simple")
                        return True
                    
                    # Vérifier si nous sommes sur une fenêtre de la même application
                    active_app, _, _ = get_active_application()
                    if active_app.lower() == fenetre_trouvee['process_name'].lower():
                        print("Application activée via Alt+Tab simple (fenêtre différente)")
                        return True
                except Exception as e:
                    print(f"Erreur Alt+Tab simple: {e}")
                
                return False
            
            # Si aucune fenêtre n'est trouvée, essayer d'ouvrir l'application
            print(f"Aucune fenêtre trouvée pour '{recherche}', tentative d'ouverture")
            
            # Méthode 1: Utiliser WScript.Shell.AppActivate
            try:
                print(f"Essai de la méthode WScript.Shell.AppActivate pour {recherche}")
                result = subprocess.run(["powershell", "-Command", 
                                       f"(New-Object -ComObject WScript.Shell).AppActivate('{recherche}')"],
                                       capture_output=True, text=True)
                
                # Vérifier si la commande a réussi
                if "True" in result.stdout:
                    print(f"Méthode WScript.Shell.AppActivate réussie pour {recherche}")
                    return True
            except Exception as e:
                print(f"Erreur avec WScript.Shell.AppActivate: {e}")
            
            # Méthode 2: Utiliser la recherche Windows pour ouvrir l'application
            try:
                print(f"Tentative d'ouverture via la recherche Windows pour {recherche}")
                
                # Méthode 1: Utiliser directement la touche Windows (méthode la plus rapide et discrète)
                pyautogui.press('win')
                time.sleep(0.3)
                
                # Taper le nom de l'application
                pyautogui.write(recherche)
                time.sleep(0.5)
                
                # Appuyer sur Entrée pour ouvrir la première suggestion
                pyautogui.press('enter')
                time.sleep(1)
                
                # Vérifier si une nouvelle fenêtre correspondante est maintenant active
                app_name, window_title, exe_path = get_active_application()
                if (recherche_lower in app_name.lower() or 
                    recherche_lower in window_title.lower()):
                    print(f"Application {recherche} ouverte via touche Windows")
                    return True
                
                # Méthode supprimée: Win+R n'est plus utilisé comme demandé
                
                # Méthode 3: Essayer de lancer directement via subprocess (silencieux)
                # shell=False pour éviter l'injection de commandes via recherche
                try:
                    subprocess.Popen(recherche, shell=False)
                    time.sleep(1)
                    
                    # Vérifier si une nouvelle fenêtre correspondante est maintenant active
                    app_name, window_title, exe_path = get_active_application()
                    if (recherche_lower in app_name.lower() or
                        recherche_lower in window_title.lower()):
                        print(f"Application {recherche} ouverte via subprocess")
                        return True
                except (subprocess.SubprocessError, FileNotFoundError, OSError, AttributeError) as e:
                    error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to open app via subprocess: {e}", ErrorSeverity.LOW)
                
                return False
            except Exception as e:
                print(f"Erreur lors de l'ouverture via la recherche Windows: {e}")
                return False
            
        elif os_type == 'mac':
            # Méthode macOS
            script = f'''
            tell application "{recherche}"
                activate
            end tell
            '''
            try:
                subprocess.run(["osascript", "-e", script], capture_output=True)
                return True
            except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to activate macOS app: {e}", ErrorSeverity.LOW)
                return False
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser wmctrl pour activer la fenêtre
                result = subprocess.run(["wmctrl", "-a", recherche], capture_output=True)
                return result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to activate Linux window: {e}", ErrorSeverity.LOW)
                return False
        
        return False
    except Exception as e:
        error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Error in basculer_vers_fenetre: {e}", ErrorSeverity.MEDIUM)
        return False

def basculer_vers_application(nom_app):
    """
    Bascule vers une application spécifique si elle est ouverte (fonction de compatibilité)
    Utilise la nouvelle fonction basculer_vers_fenetre
    """
    print(f"Appel de basculer_vers_application avec {nom_app}")
    
    # Utiliser la nouvelle fonction plus robuste
    return basculer_vers_fenetre(nom_app, par_titre=True, par_process=True, exact=False)
