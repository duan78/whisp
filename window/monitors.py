"""Fonctions de gestion des écrans multiples (détection et déplacement de fenêtres entre écrans)."""

from window._common import *  # noqa: F401,F403  (imports partagés + error_handler + SITES_POPULAIRES)

# Fonctions pour la gestion des écrans multiples adaptées à chaque OS
def get_monitor_count():
    """Obtient le nombre d'écrans connectés"""
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Méthode Windows
            user32 = ctypes.WinDLL('user32')
            user32.GetSystemMetrics.restype = ctypes.c_int
            SM_CMONITORS = 80  # Nombre d'écrans
            return user32.GetSystemMetrics(SM_CMONITORS)
        
        elif os_type == 'mac':
            # Méthode macOS
            try:
                import Quartz
                displays = Quartz.CGGetActiveDisplayList(10, None, None)[1]
                return len(displays) if displays else 1
            except (ImportError, AttributeError):
                # Méthode alternative avec subprocess
                result = subprocess.run(["system_profiler", "SPDisplaysDataType"], 
                                      capture_output=True, text=True)
                # Compter les occurrences de "Display Type" dans la sortie
                return result.stdout.count("Display Type") or 1
        
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser xrandr pour obtenir les écrans
                result = subprocess.run(["xrandr", "--listmonitors"],
                                      capture_output=True, text=True)
                # La première ligne contient le nombre d'écrans (ex: "Monitors: 2")
                first_line = result.stdout.strip().split('\n')[0]
                count = int(first_line.split(':')[1].strip())
                return count
            except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"xrandr method failed: {e}", ErrorSeverity.LOW)
                # Méthode alternative
                try:
                    import Xlib.display
                    d = Xlib.display.Display()
                    screen_count = d.screen_count()
                    return screen_count
                except (ImportError, AttributeError, OSError) as e2:
                    error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Xlib method failed: {e2}", ErrorSeverity.LOW)
                    return 1
        
        else:
            return 1
    
    except Exception as e:
        print(f"Erreur lors de la détection du nombre d'écrans: {e}")
        return 1

def deplacer_fenetre_vers_ecran(ecran_cible):
    """Déplace la fenêtre active vers l'écran spécifié"""
    os_type = get_os_type()
    
    try:
        # Obtenir le nombre d'écrans
        nb_ecrans = get_monitor_count()
        
        if nb_ecrans < 2:
            return "Un seul écran détecté"
        
        # Vérifier que l'écran cible est valide
        if ecran_cible < 1 or ecran_cible > nb_ecrans:
            return f"Écran {ecran_cible} non valide. {nb_ecrans} écrans disponibles."
        
        if os_type == 'windows':
            # Méthode Windows
            # Obtenir la fenêtre active
            if is_windows():
                hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            # Méthode plus fiable pour déplacer les fenêtres entre écrans
            if ecran_cible == 1:  # Écran principal
                # Utiliser Win+Shift+Flèche gauche pour déplacer vers l'écran principal
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('left')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
                # Répéter pour s'assurer que la fenêtre est bien sur l'écran principal
                time.sleep(0.5)
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('left')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
            elif ecran_cible == 2:  # Deuxième écran
                # Utiliser Win+Shift+Flèche droite pour déplacer vers l'écran secondaire
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
            elif ecran_cible == 3:  # Troisième écran (si disponible)
                # Déplacer d'abord vers le deuxième écran
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
                
                # Puis vers le troisième écran
                time.sleep(0.5)
                pyautogui.keyDown('win')
                time.sleep(0.2)
                pyautogui.keyDown('shift')
                time.sleep(0.2)
                pyautogui.press('right')
                time.sleep(0.2)
                pyautogui.keyUp('shift')
                time.sleep(0.2)
                pyautogui.keyUp('win')
            
            # Maximiser la fenêtre sur le nouvel écran (optionnel)
            time.sleep(0.5)
            pyautogui.keyDown('win')
            time.sleep(0.2)
            pyautogui.press('up')
            time.sleep(0.2)
            pyautogui.keyUp('win')
            
        elif os_type == 'mac':
            # Méthode macOS
            # Sur macOS, on peut utiliser AppleScript pour déplacer les fenêtres
            try:
                # Obtenir les dimensions des écrans
                script = '''
                tell application "System Events"
                    set screenBounds to bounds of every desktop
                    return screenBounds
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                
                # Déplacer la fenêtre active vers l'écran cible
                # Note: Cette approche est simplifiée et peut nécessiter des ajustements
                if ecran_cible == 1:
                    script = '''
                    tell application "System Events"
                        set frontWindow to first window of (first process whose frontmost is true)
                        set position of frontWindow to {0, 0}
                    end tell
                    '''
                elif ecran_cible == 2:
                    script = '''
                    tell application "System Events"
                        set frontWindow to first window of (first process whose frontmost is true)
                        set screenWidth to item 3 of bounds of desktop 1
                        set position of frontWindow to {screenWidth + 50, 50}
                    end tell
                    '''
                
                subprocess.run(["osascript", "-e", script], capture_output=True)
            except Exception as e:
                return f"Erreur lors du déplacement de la fenêtre sur macOS: {str(e)}"
            
        elif os_type == 'linux':
            # Méthode Linux
            # Sur Linux, on peut utiliser wmctrl pour déplacer les fenêtres
            try:
                # Obtenir l'ID de la fenêtre active
                result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True, text=True)
                window_id = result.stdout.strip()
                
                # Obtenir les informations sur les écrans
                result = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True)
                
                # Déplacer la fenêtre vers l'écran cible
                if ecran_cible == 1:
                    # Déplacer vers le premier écran (généralement à la position 0,0)
                    subprocess.run(["wmctrl", "-i", "-r", window_id, "-e", "0,0,0,-1,-1"])
                elif ecran_cible == 2:
                    # Déplacer vers le deuxième écran (position approximative)
                    # Note: Cette approche est simplifiée et peut nécessiter des ajustements
                    subprocess.run(["wmctrl", "-i", "-r", window_id, "-e", "0,1920,0,-1,-1"])
            except Exception as e:
                return f"Erreur lors du déplacement de la fenêtre sur Linux: {str(e)}"
        
        return f"Fenêtre déplacée vers l'écran {ecran_cible}"
    except Exception as e:
        return f"Erreur lors du déplacement de la fenêtre: {str(e)}"
