"""
Module d'utilitaires cross-platform pour la gestion des fenêtres et du système
Fournit une interface unifiée pour Windows, macOS et Linux
"""

import platform
import subprocess
from typing import Optional, Dict, Any


class WindowManager:
    """Interface cross-platform pour la gestion des fenêtres"""

    def __init__(self):
        """Initialise le gestionnaire de fenêtres"""
        self.system = platform.system()
        self._init_platform()

    def _init_platform(self):
        """Initialise les bibliothèques spécifiques à la plateforme"""
        self.win32_available = False
        self.nsworkspace_available = False
        self.ewmh_available = False

        if self.system == "Windows":
            try:
                import win32gui
                import win32process
                self.win32gui = win32gui
                self.win32process = win32process
                self.win32_available = True
            except ImportError:
                pass

        elif self.system == "Darwin":  # macOS
            try:
                from AppKit import NSWorkspace
                self.NSWorkspace = NSWorkspace
                self.nsworkspace_available = True
            except ImportError:
                pass

        else:  # Linux
            try:
                import ewmh
                from Xlib import display
                self.ewmh = ewmh
                self.xdisplay = display
                self.ewmh_available = True
            except ImportError:
                pass

    def get_active_window(self) -> Optional[str]:
        """
        Retourne le titre/nom de la fenêtre active

        Returns:
            Le titre de la fenêtre ou None si non disponible
        """
        if self.system == "Windows" and self.win32_available:
            return self._get_active_window_windows()
        elif self.system == "Darwin" and self.nsworkspace_available:
            return self._get_active_window_macos()
        elif self.system == "Linux" and self.ewmh_available:
            return self._get_active_window_linux()
        else:
            return f"Fenêtre {self.system}"

    def _get_active_window_windows(self) -> Optional[str]:
        """Retourne la fenêtre active sur Windows"""
        try:
            hwnd = self.win32gui.GetForegroundWindow()
            return self.win32gui.GetWindowText(hwnd)
        except Exception:
            return "Fenêtre Windows (détail non disponible)"

    def _get_active_window_macos(self) -> Optional[str]:
        """Retourne la fenêtre active sur macOS"""
        try:
            app = self.NSWorkspace.sharedWorkspace().activeApplication()
            return app.get('NSApplicationName', 'Fenêtre macOS')
        except Exception:
            return "Fenêtre macOS"

    def _get_active_window_linux(self) -> Optional[str]:
        """Retourne la fenêtre active sur Linux"""
        try:
            display = self.xdisplay.Display()
            root = display.screen().root
            window = root.get_full_property(
                self.xdisplay.display.intern_atom('_NET_ACTIVE_WINDOW'),
                self.xdisplay.X.AnyPropertyType
            )
            if window:
                return "Fenêtre Linux"
        except Exception:
            pass
        return "Fenêtre Linux"

    def get_window_list(self) -> list:
        """
        Retourne la liste des fenêtres ouvertes

        Returns:
            Liste des titres de fenêtres
        """
        if self.system == "Windows" and self.win32_available:
            return self._get_window_list_windows()
        elif self.system == "Darwin" and self.nsworkspace_available:
            return self._get_window_list_macos()
        elif self.system == "Linux" and self.ewmh_available:
            return self._get_window_list_linux()
        else:
            return []

    def _get_window_list_windows(self) -> list:
        """Retourne la liste des fenêtres sur Windows"""
        windows = []
        try:
            def callback(hwnd, windows_list):
                if self.win32gui.IsWindowVisible(hwnd):
                    title = self.win32gui.GetWindowText(hwnd)
                    if title:
                        windows_list.append(title)
                return True

            self.win32gui.EnumWindows(callback, windows)
        except Exception:
            pass
        return windows

    def _get_window_list_macos(self) -> list:
        """Retourne la liste des fenêtres sur macOS"""
        windows = []
        try:
            running_apps = self.NSWorkspace.sharedWorkspace().runningApplications()
            for app in running_apps:
                app_name = app.get('NSApplicationName', '')
                if app_name:
                    windows.append(app_name)
        except Exception:
            pass
        return windows

    def _get_window_list_linux(self) -> list:
        """Retourne la liste des fenêtres sur Linux"""
        windows = []
        try:
            # Utiliser wmctrl si disponible
            result = subprocess.run(
                ['wmctrl', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line:
                        # Extraire le titre de la fenêtre
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows.append(parts[3])
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return windows

    def set_foreground_window(self, window_title: str) -> bool:
        """
        Met une fenêtre au premier plan

        Args:
            window_title: Titre de la fenêtre

        Returns:
            True si succès, False sinon
        """
        if self.system == "Windows" and self.win32_available:
            return self._set_foreground_window_windows(window_title)
        elif self.system == "Darwin":
            return self._set_foreground_window_macos(window_title)
        elif self.system == "Linux":
            return self._set_foreground_window_linux(window_title)
        return False

    def _set_foreground_window_windows(self, window_title: str) -> bool:
        """Met une fenêtre au premier plan sur Windows"""
        try:
            def callback(hwnd, params):
                title, hwnd_list = params
                if self.win32gui.IsWindowVisible(hwnd):
                    current_title = self.win32gui.GetWindowText(hwnd)
                    if window_title.lower() in current_title.lower():
                        hwnd_list.append(hwnd)
                return True

            hwnd_list = []
            self.win32gui.EnumWindows(callback, (window_title, hwnd_list))

            if hwnd_list:
                self.win32gui.SetForegroundWindow(hwnd_list[0])
                return True
        except Exception:
            pass
        return False

    def _set_foreground_window_macos(self, window_title: str) -> bool:
        """Met une fenêtre au premier plan sur macOS"""
        try:
            # Utiliser osascript pour activer l'application
            script = f'tell application "System Events" to set frontmost of every process whose name is "{window_title}" to true'
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _set_foreground_window_linux(self, window_title: str) -> bool:
        """Met une fenêtre au premier plan sur Linux"""
        try:
            # Utiliser wmctrl
            result = subprocess.run(
                ['wmctrl', '-a', window_title],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def minimize_window(self, window_title: str) -> bool:
        """
        Minimise une fenêtre

        Args:
            window_title: Titre de la fenêtre

        Returns:
            True si succès, False sinon
        """
        # Implémentation simplifiée - à compléter selon les besoins
        return False

    def maximize_window(self, window_title: str) -> bool:
        """
        Maximise une fenêtre

        Args:
            window_title: Titre de la fenêtre

        Returns:
            True si succès, False sinon
        """
        # Implémentation simplifiée - à compléter selon les besoins
        return False


class SystemInfo:
    """Informations système cross-platform"""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """
        Retourne les informations système

        Returns:
            Dictionnaire avec les informations système
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    @staticmethod
    def get_memory_info() -> Dict[str, float]:
        """
        Retourne les informations sur la mémoire

        Returns:
            Dictionnaire avec la mémoire totale et disponible en GB
        """
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                "total_gb": mem.total / (1024 ** 3),
                "available_gb": mem.available / (1024 ** 3),
                "percent_used": mem.percent,
            }
        except ImportError:
            return {"total_gb": 0, "available_gb": 0, "percent_used": 0}

    @staticmethod
    def get_disk_info(path: str = "/") -> Dict[str, float]:
        """
        Retourne les informations sur l'espace disque

        Args:
            path: Chemin à analyser

        Returns:
            Dictionnaire avec l'espace total et disponible en GB
        """
        try:
            import psutil
            disk = psutil.disk_usage(path)
            return {
                "total_gb": disk.total / (1024 ** 3),
                "free_gb": disk.free / (1024 ** 3),
                "percent_used": disk.percent,
            }
        except ImportError:
            return {"total_gb": 0, "free_gb": 0, "percent_used": 0}


# Instances globales pour faciliter l'utilisation
_window_manager = None
_system_info = None


def get_window_manager() -> WindowManager:
    """Retourne l'instance singleton du gestionnaire de fenêtres"""
    global _window_manager
    if _window_manager is None:
        _window_manager = WindowManager()
    return _window_manager


def get_system_info() -> SystemInfo:
    """Retourne l'instance singleton des infos système"""
    global _system_info
    if _system_info is None:
        _system_info = SystemInfo()
    return _system_info


if __name__ == "__main__":
    # Tests
    print("=== Test WindowManager ===")
    wm = WindowManager()
    print(f"Fenêtre active: {wm.get_active_window()}")
    print(f"Nombre de fenêtres: {len(wm.get_window_list())}")

    print("\n=== Test SystemInfo ===")
    sys_info = SystemInfo.get_system_info()
    print(f"Système: {sys_info['system']} {sys_info['release']}")
    print(f"Processeur: {sys_info['processor']}")

    mem_info = SystemInfo.get_memory_info()
    print(f"Mémoire: {mem_info['available_gb']:.2f} GB / {mem_info['total_gb']:.2f} GB")
