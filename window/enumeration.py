"""Listage des fenêtres et applications actuellement ouvertes."""

from window._common import *  # noqa: F401,F403  (imports partagés + error_handler)

def obtenir_fenetres_ouvertes():
    """Obtient la liste des fenêtres actuellement ouvertes avec leurs informations"""
    os_type = get_os_type()
    fenetres = []
    
    try:
        if os_type == 'windows':
            # Méthode Windows avec win32gui
            import win32gui
            import win32process
            import psutil
            
            def enum_windows_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    
                    # Ignorer certaines fenêtres système
                    if window_title and not window_title.startswith("Default IME") and not window_title == "Program Manager":
                        try:
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
                                
                                # Obtenir les coordonnées de la fenêtre
                                try:
                                    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                                    width = right - left
                                    height = bottom - top
                                except (OSError, AttributeError, win32gui.error) as e:
                                    error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Failed to get window rect: {e}", ErrorSeverity.LOW)
                                    left, top, width, height = 0, 0, 0, 0
                                
                                # Ajouter les informations de la fenêtre
                                results.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': process_name.lower(),
                                    'pid': pid,
                                    'exe_path': exe_path,
                                    'position': (left, top, width, height)
                                })
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                # Ajouter avec des informations limitées
                                results.append({
                                    'hwnd': hwnd,
                                    'title': window_title,
                                    'process_name': "unknown",
                                    'pid': pid,
                                    'exe_path': "",
                                    'position': (0, 0, 0, 0)
                                })
                        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError, AttributeError) as e:
                            error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"Error enumerating windows: {e}", ErrorSeverity.LOW)
            
            windows_list = []
            win32gui.EnumWindows(enum_windows_callback, windows_list)
            
            # Trier les fenêtres par titre pour faciliter la recherche
            windows_list.sort(key=lambda x: x['title'].lower())
            
            return windows_list
        
        elif os_type == 'mac':
            # Méthode macOS - à implémenter
            return []
            
        elif os_type == 'linux':
            # Méthode Linux - à implémenter
            return []
            
        else:
            return []
            
    except Exception as e:
        print(f"Erreur lors de l'obtention des fenêtres ouvertes: {e}")
        return []

def obtenir_applications_ouvertes():
    """Obtient la liste des applications actuellement ouvertes"""
    os_type = get_os_type()
    applications = []
    
    try:
        if os_type == 'windows':
            # Utiliser la fonction obtenir_fenetres_ouvertes pour obtenir des informations plus détaillées
            fenetres = obtenir_fenetres_ouvertes()
            
            # Extraire les noms d'applications uniques
            app_names = set()
            for fenetre in fenetres:
                if fenetre['process_name'] and fenetre['process_name'] != "unknown":
                    app_names.add(fenetre['process_name'])
            
            applications = list(app_names)
            
            # Si aucune fenêtre n'est trouvée, utiliser la méthode tasklist comme fallback
            if not applications:
                result = subprocess.run(["tasklist", "/FO", "CSV"], capture_output=True, text=True, encoding='cp850')
                
                # Analyser la sortie pour extraire les noms des applications
                for line in result.stdout.splitlines()[1:]:  # Ignorer l'en-tête
                    if '","' in line:
                        parts = line.split('","')
                        if len(parts) >= 1:
                            app_name = parts[0].strip('"')
                            # Nettoyer le nom (enlever l'extension .exe)
                            if app_name.lower().endswith('.exe'):
                                app_name = app_name[:-4]
                            applications.append(app_name)
            
        elif os_type == 'mac':
            # Méthode macOS
            script = '''
            tell application "System Events"
                set appList to name of every process where background only is false
            end tell
            '''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            
            # Analyser la sortie
            if result.stdout:
                applications = [app.strip() for app in result.stdout.split(',')]
                
        elif os_type == 'linux':
            # Méthode Linux
            try:
                # Utiliser wmctrl pour lister les fenêtres
                result = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True)
                
                # Analyser la sortie
                for line in result.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 4:
                        # Le nom de l'application est généralement après le 3ème champ
                        app_name = ' '.join(parts[3:])
                        applications.append(app_name)
            except (subprocess.SubprocessError, FileNotFoundError, OSError, ValueError, IndexError) as e:
                error_handler.log_error(ErrorCategory.WINDOW_MANAGEMENT, f"wmctrl method failed: {e}", ErrorSeverity.LOW)
                # Méthode alternative
                result = subprocess.run(["ps", "-e", "-o", "comm="], capture_output=True, text=True)
                applications = [line.strip() for line in result.stdout.splitlines()]
        
        # Filtrer les doublons et les entrées vides
        applications = list(set([app for app in applications if app]))
        
        return applications
    
    except Exception as e:
        print(f"Erreur lors de l'obtention des applications ouvertes: {e}")
        return []
