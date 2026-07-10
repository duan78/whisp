"""Détection de l'application/fenêtre/navigateur actif et du contexte applicatif."""

from window._common import *  # noqa: F401,F403  (imports partagés + error_handler)

def get_active_application():
    """
    Détecte l'application active actuellement
    
    Returns:
        tuple: (nom_application, titre_fenetre)
    """
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Méthode Windows
            import win32gui
            import win32process
            import psutil
            
            # Obtenir le handle de la fenêtre active
            hwnd = win32gui.GetForegroundWindow()
            
            # Obtenir le titre de la fenêtre
            window_title = win32gui.GetWindowText(hwnd)
            
            # Obtenir le PID du processus
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Obtenir le nom de l'exécutable
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                
                # Nettoyer le nom du processus (enlever l'extension .exe)
                if process_name.lower().endswith('.exe'):
                    process_name = process_name[:-4]
                
                # Obtenir le chemin complet de l'exécutable
                try:
                    exe_path = process.exe()
                except (psutil.AccessDenied, AttributeError):
                    exe_path = ""
                
                return (process_name.lower(), window_title, exe_path)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return ("unknown", window_title, "")
                
        elif os_type == 'mac':
            # Méthode macOS
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontWindow to ""
                try
                    tell process frontApp
                        set frontWindow to name of front window
                    end tell
                end try
                return {frontApp, frontWindow}
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.stdout:
                parts = result.stdout.strip().split(', ')
                app_name = parts[0].lower() if parts and len(parts) > 0 else "unknown"
                window_title = parts[1] if parts and len(parts) > 1 else ""
                return (app_name, window_title, "")
            else:
                return ("unknown", "", "")
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser xdotool pour obtenir le nom de la fenêtre active
                window_id = subprocess.run(["xdotool", "getactivewindow"], 
                                         capture_output=True, text=True).stdout.strip()
                
                window_title = subprocess.run(["xdotool", "getwindowname", window_id], 
                                            capture_output=True, text=True).stdout.strip()
                
                # Utiliser wmctrl pour obtenir des informations sur la fenêtre
                wmctrl_output = subprocess.run(["wmctrl", "-l", "-p"], 
                                             capture_output=True, text=True).stdout
                
                # Chercher la ligne correspondant à la fenêtre active
                for line in wmctrl_output.splitlines():
                    if window_id in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            pid = parts[2]
                            # Obtenir le nom du processus à partir du PID
                            process_name = subprocess.run(["ps", "-p", pid, "-o", "comm="], 
                                                        capture_output=True, text=True).stdout.strip()
                            return (process_name.lower(), window_title, "")

                return ("unknown", window_title, "")
            except (subprocess.SubprocessError, FileNotFoundError, OSError, ValueError, IndexError) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Error getting active app on Linux: {e}", ErrorSeverity.LOW)
                return ("unknown", "", "")
        
        else:
            return ("unknown", "", "")
            
    except Exception as e:
        print(f"Erreur lors de la détection de l'application active: {e}")
        return ("unknown", "")

def is_browser_active():
    """
    Vérifie si le navigateur est l'application active
    
    Returns:
        bool: True si un navigateur est actif, False sinon
    """
    app_name, _, _ = get_active_application()
    
    browsers = [
        "chrome", "googlechrome", "google chrome",
        "firefox", "mozilla firefox", 
        "edge", "msedge", "microsoft edge",
        "safari", 
        "opera",
        "brave",
        "vivaldi"
    ]
    
    return any(browser in app_name for browser in browsers)

def get_active_browser():
    """
    Détecte le navigateur actif
    
    Returns:
        str: Nom du navigateur actif ou None
    """
    app_name, _, _ = get_active_application()
    
    if "chrome" in app_name:
        return "chrome"
    elif "firefox" in app_name:
        return "firefox"
    elif "edge" in app_name:
        return "edge"
    elif "safari" in app_name:
        return "safari"
    elif "opera" in app_name:
        return "opera"
    elif "brave" in app_name:
        return "brave"
    elif "vivaldi" in app_name:
        return "vivaldi"
    else:
        return None

def get_active_browser_tab_info():
    """
    Tente de détecter l'URL et le titre de l'onglet actif du navigateur
    
    Returns:
        tuple: (url, title) ou (None, None) si impossible à détecter
    """
    browser = get_active_browser()
    if not browser:
        return (None, None)
    
    os_type = get_os_type()
    
    try:
        if os_type == 'windows':
            # Pour Chrome/Edge sur Windows
            if browser in ["chrome", "edge", "brave"]:
                # Obtenir le titre de la fenêtre qui contient généralement le titre de la page
                _, window_title, _ = get_active_application()
                
                # Le titre de la fenêtre est généralement "Titre de la page - Navigateur"
                page_title = window_title.split(" - ")[0] if " - " in window_title else window_title
                
                # Impossible d'obtenir l'URL directement sans extension de navigateur
                return (None, page_title)
                
            # Pour Firefox sur Windows
            elif browser == "firefox":
                _, window_title, _ = get_active_application()
                page_title = window_title.split(" — ")[0] if " — " in window_title else window_title
                return (None, page_title)
                
        elif os_type == 'mac':
            # Pour Safari sur macOS
            if browser == "safari":
                script = '''
                tell application "Safari"
                    set currentTab to current tab of front window
                    set tabURL to URL of currentTab
                    set tabTitle to name of currentTab
                    return {tabURL, tabTitle}
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                if result.stdout:
                    parts = result.stdout.strip().split(', ')
                    url = parts[0] if parts and len(parts) > 0 else None
                    title = parts[1] if parts and len(parts) > 1 else None
                    return (url, title)
            
            # Pour Chrome sur macOS
            elif browser == "chrome":
                script = '''
                tell application "Google Chrome"
                    set currentTab to active tab of front window
                    set tabURL to URL of currentTab
                    set tabTitle to title of currentTab
                    return {tabURL, tabTitle}
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                if result.stdout:
                    parts = result.stdout.strip().split(', ')
                    url = parts[0] if parts and len(parts) > 0 else None
                    title = parts[1] if parts and len(parts) > 1 else None
                    return (url, title)
                    
            # Pour Firefox sur macOS
            elif browser == "firefox":
                # Firefox est plus difficile à automatiser avec AppleScript
                _, window_title, _ = get_active_application()
                page_title = window_title.split(" — ")[0] if " — " in window_title else window_title
                return (None, page_title)
                
        # Pour Linux, on peut seulement obtenir le titre de la fenêtre
        elif os_type == 'linux':
            _, window_title, _ = get_active_application()
            
            # Différents navigateurs utilisent différents séparateurs
            if " - " in window_title:  # Chrome, Edge
                page_title = window_title.split(" - ")[0]
            elif " — " in window_title:  # Firefox
                page_title = window_title.split(" — ")[0]
            else:
                page_title = window_title
                
            return (None, page_title)
            
        # Par défaut, retourner None, None
        return (None, None)
        
    except Exception as e:
        print(f"Erreur lors de la détection de l'onglet actif: {e}")
        return (None, None)

def detect_application_context():
    """
    Détecte le contexte de l'application active pour adapter les commandes
    
    Returns:
        dict: Informations sur le contexte de l'application
    """
    app_name, window_title, exe_path = get_active_application()
    
    context = {
        "app_name": app_name,
        "window_title": window_title,
        "exe_path": exe_path,
        "is_browser": False,
        "browser_name": None,
        "tab_url": None,
        "tab_title": None,
        "is_meet": False,
        "is_zoom": False,
        "is_teams": False,
        "is_office": False,
        "is_code_editor": False
    }
    
    # Vérifier si c'est un navigateur
    if is_browser_active():
        context["is_browser"] = True
        context["browser_name"] = get_active_browser()
        
        # Obtenir les informations sur l'onglet actif
        tab_url, tab_title = get_active_browser_tab_info()
        context["tab_url"] = tab_url
        context["tab_title"] = tab_title
        
        # Détecter les applications web courantes
        if window_title:
            window_title_lower = window_title.lower()
            
            # Google Meet
            if "meet.google.com" in window_title_lower or "google meet" in window_title_lower:
                context["is_meet"] = True
                
            # Zoom dans le navigateur
            elif "zoom" in window_title_lower and ("meeting" in window_title_lower or "réunion" in window_title_lower):
                context["is_zoom"] = True
                
            # Microsoft Teams dans le navigateur
            elif "teams" in window_title_lower and ("microsoft" in window_title_lower or "meeting" in window_title_lower):
                context["is_teams"] = True
    
    # Applications natives
    else:
        # Microsoft Office
        if any(app in app_name for app in ["word", "excel", "powerpoint", "outlook", "onenote"]):
            context["is_office"] = True
            
        # Éditeurs de code
        elif any(app in app_name for app in ["code", "vscode", "visualstudio", "pycharm", "intellij", 
                                           "eclipse", "atom", "sublime", "notepad++", "vim", "emacs"]):
            context["is_code_editor"] = True
            
        # Applications de visioconférence natives
        elif "zoom" in app_name:
            context["is_zoom"] = True
        elif "teams" in app_name:
            context["is_teams"] = True
    
    return context
