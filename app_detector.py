"""
Module de détection d'applications cross-platform
Permet de trouver le chemin des applications de manière automatique sur Windows, macOS et Linux
"""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional, List


class ApplicationDetector:
    """Détecte et localise les applications installées sur le système"""

    def __init__(self):
        """Initialise le détecteur avec les chemins de recherche du système"""
        self.system = platform.system()
        self.search_paths = self._get_search_paths()

    def _get_search_paths(self) -> List[str]:
        """Retourne la liste des chemins de recherche selon l'OS"""
        if self.system == "Windows":
            return [
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                os.path.expanduser("~/AppData/Local"),
                os.path.expanduser("~/AppData/Roaming"),
            ]
        elif self.system == "Darwin":  # macOS
            return [
                "/Applications",
                os.path.expanduser("~/Applications"),
            ]
        else:  # Linux
            return [
                "/usr/bin",
                "/usr/local/bin",
                "/opt",
                os.path.expanduser("~/.local/bin"),
            ]

    def find_application(self, app_name: str) -> Optional[str]:
        """
        Trouve le chemin d'une application de manière cross-platform

        Args:
            app_name: Nom de l'application (ex: "chrome", "pycharm", "notepad")

        Returns:
            Le chemin complet de l'application ou None si non trouvée
        """
        # D'abord, chercher dans le PATH système
        path_in_env = shutil.which(app_name)
        if path_in_env:
            return path_in_env

        # Ensuite, chercher dans les répertoires spécifiques à l'OS
        if self.system == "Windows":
            return self._find_windows_app(app_name)
        elif self.system == "Darwin":
            return self._find_macos_app(app_name)
        else:  # Linux
            return self._find_linux_app(app_name)

    def _find_windows_app(self, app_name: str) -> Optional[str]:
        """Trouve une application sur Windows"""
        # Extensions courantes pour Windows
        extensions = [".exe", ".lnk"]

        # Chercher dans Program Files
        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue

            # Recherche récursive (limitée à 3 niveaux de profondeur)
            for root, dirs, files in os.walk(search_path):
                # Limiter la profondeur
                depth = root[len(search_path):].count(os.sep)
                if depth > 3:
                    dirs[:] = []  # Ne pas descendre plus loin
                    continue

                # Chercher le fichier
                for file in files:
                    file_lower = file.lower()
                    app_name_lower = app_name.lower()

                    # Vérifier avec et sans extension
                    if (file_lower == f"{app_name_lower}.exe" or
                        file_lower == f"{app_name_lower}.lnk" or
                        file_lower == f"{app_name_lower}64.exe" or
                        app_name_lower in file_lower):

                        full_path = os.path.join(root, file)
                        return full_path

        return None

    def _find_macos_app(self, app_name: str) -> Optional[str]:
        """Trouve une application sur macOS"""
        # Sur macOS, les applications sont des .app bundles
        app_name_variants = [
            f"{app_name}.app",
            f"{app_name.capitalize()}.app",
            f"{app_name.title()}.app",
        ]

        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue

            for variant in app_name_variants:
                app_path = os.path.join(search_path, variant)
                if os.path.exists(app_path):
                    # Le binaire est dans Contents/MacOS/
                    binary_path = os.path.join(app_path, "Contents", "MacOS", app_name)
                    if os.path.exists(binary_path):
                        return binary_path
                    return app_path

        return None

    def _find_linux_app(self, app_name: str) -> Optional[str]:
        """Trouve une application sur Linux"""
        # Chercher dans les chemins standards
        for search_path in self.search_paths:
            if not os.path.exists(search_path):
                continue

            # Chercher directement le binaire
            binary_path = os.path.join(search_path, app_name)
            if os.path.exists(binary_path):
                return binary_path

            # Chercher avec les variants de nom courants
            variants = [
                f"{app_name}.sh",
                f"{app_name}.bin",
            ]

            for variant in variants:
                variant_path = os.path.join(search_path, variant)
                if os.path.exists(variant_path):
                    return variant_path

        return None

    def is_installed(self, app_name: str) -> bool:
        """
        Vérifie si une application est installée

        Args:
            app_name: Nom de l'application

        Returns:
            True si l'application est installée, False sinon
        """
        return self.find_application(app_name) is not None

    def get_installed_apps(self, filter_pattern: str = "") -> List[str]:
        """
        Retourne la liste des applications installées (optionnellement filtrées)

        Args:
            filter_pattern: Pattern pour filtrer les résultats (ex: "code" pour éditeurs de code)

        Returns:
            Liste des applications installées
        """
        installed_apps = []

        if self.system == "Windows":
            # Lister les applications depuis Program Files
            for search_path in self.search_paths[:2]:  # Program Files uniquement
                if not os.path.exists(search_path):
                    continue

                try:
                    for item in os.listdir(search_path):
                        item_path = os.path.join(search_path, item)
                        if os.path.isdir(item_path):
                            if not filter_pattern or filter_pattern.lower() in item.lower():
                                installed_apps.append(item)
                except PermissionError:
                    continue

        elif self.system == "Darwin":
            # Lister les applications depuis /Applications
            apps_path = "/Applications"
            if os.path.exists(apps_path):
                for item in os.listdir(apps_path):
                    if item.endswith(".app"):
                        app_name = item.replace(".app", "")
                        if not filter_pattern or filter_pattern.lower() in app_name.lower():
                            installed_apps.append(app_name)

        else:  # Linux
            # Lister les binaires depuis /usr/bin et /usr/local/bin
            for search_path in self.search_paths[:2]:
                if not os.path.exists(search_path):
                    continue

                try:
                    for item in os.listdir(search_path):
                        item_path = os.path.join(search_path, item)
                        if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
                            if not filter_pattern or filter_pattern.lower() in item.lower():
                                installed_apps.append(item)
                except PermissionError:
                    continue

        return sorted(set(installed_apps))


# Instance globale pour faciliter l'utilisation
_detector = None


def get_detector() -> ApplicationDetector:
    """Retourne l'instance singleton du détecteur"""
    global _detector
    if _detector is None:
        _detector = ApplicationDetector()
    return _detector


def find_application(app_name: str) -> Optional[str]:
    """
    Interface simplifiée pour trouver une application

    Args:
        app_name: Nom de l'application

    Returns:
        Le chemin complet ou None
    """
    return get_detector().find_application(app_name)


def is_installed(app_name: str) -> bool:
    """
    Interface simplifiée pour vérifier si une application est installée

    Args:
        app_name: Nom de l'application

    Returns:
        True si installée, False sinon
    """
    return get_detector().is_installed(app_name)


if __name__ == "__main__":
    # Tests
    detector = ApplicationDetector()

    print(f"Système: {detector.system}")
    print(f"Chemins de recherche: {detector.search_paths}")

    # Tester quelques applications courantes
    test_apps = ["chrome", "firefox", "notepad", "code", "pycharm"]

    for app in test_apps:
        path = detector.find_application(app)
        if path:
            print(f"✓ {app}: {path}")
        else:
            print(f"✗ {app}: Non trouvé")
