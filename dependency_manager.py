"""
Module de gestion des dépendances pour l'assistant vocal Whisp
"""

import os
import sys
import subprocess
import importlib
import platform
from typing import Dict, List, Tuple, Optional
import json
import logging

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyManager:
    """Classe pour gérer les dépendances du projet Whisp"""

    def __init__(self):
        """Initialisation du gestionnaire de dépendances"""
        self.os_type = platform.system()
        self.python_version = sys.version_info
        self.project_root = os.path.dirname(os.path.abspath(__file__))

        # Définition des dépendances par catégorie
        self.dependencies = {
            "core": [
                "pyautogui>=0.9.54",
                "SpeechRecognition>=3.10.0",
                "pyttsx3>=2.91",
                "gTTS>=2.5.0",
                "pygame>=2.5.0",
                "flask>=3.0.0",
                "flask-cors>=4.0.0",
                "numpy>=1.26.0,<2.0.0",
                "scipy>=1.11.0",
                "Pillow>=10.0.0",
                "cryptography>=41.0.0",
                "psutil>=5.9.0",
                "keyboard>=0.13.5",
                "plyer>=2.1.0",
                "requests>=2.31.0",
                "python-dotenv>=1.0.0",
                "colorama>=0.4.6",
                "typing-extensions>=4.8.0",
                "sounddevice>=0.4.6",  # Backend audio recommandé (cross-platform)
                "vosk>=0.3.45",  # Reconnaissance vocale offline
            ],
            "stt": [
                "faster-whisper>=0.9.0",
            ],
            "tts": [
                "TTS>=0.22.0",
            ],
            "ai": [
                "mistralai>=1.9.0",
                "openai>=1.0.0",
            ],
            "dev": [
                "pytest>=7.4.0",
                "pytest-cov>=4.1.0",
                "black>=23.0.0",
                "mypy>=1.5.0",
            ],
        }

        # Dépendances optionnelles avec alternatives
        self.optional_dependencies = {
            "audio_backend": [
                # "pyaudio>=0.2.13",  # Alternative (non recommandé, difficile à installer)
            ],
            "ml": [
                "numba>=0.59.0",
                "scikit-learn>=1.3.0",
            ],
        }

    def check_installed(self, package_name: str) -> bool:
        """Vérifie si un package est installé"""
        try:
            importlib.import_module(package_name.replace("-", "_").lower())
            return True
        except ImportError:
            return False

    def install_package(self, package: str, upgrade: bool = False) -> Tuple[bool, str]:
        """Installe un package via pip"""
        try:
            cmd = [sys.executable, "-m", "pip", "install"]
            if upgrade:
                cmd.append("--upgrade")
            cmd.append(package)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max par package
            )

            if result.returncode == 0:
                return True, f"Package {package} installed successfully"
            else:
                return False, f"Failed to install {package}: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, f"Timeout installing {package}"
        except Exception as e:
            return False, f"Error installing {package}: {str(e)}"

    def install_category(self, category: str, upgrade: bool = False) -> Dict[str, Tuple[bool, str]]:
        """Installe tous les packages d'une catégorie"""
        if category not in self.dependencies:
            return {}

        results = {}
        for package in self.dependencies[category]:
            success, message = self.install_package(package, upgrade)
            results[package] = (success, message)
            logger.info(message)

        return results

    def install_all(self, categories: Optional[List[str]] = None, upgrade: bool = False) -> Dict[str, Dict[str, Tuple[bool, str]]]:
        """Installe les dépendances de plusieurs catégories"""
        if categories is None:
            categories = ["core"]  # Par défaut, installer que le core

        results = {}
        for category in categories:
            if category in self.dependencies:
                results[category] = self.install_category(category, upgrade)

        return results

    def check_dependencies(self, category: Optional[str] = None) -> Dict[str, bool]:
        """Vérifie les dépendances installées"""
        if category and category in self.dependencies:
            packages = self.dependencies[category]
        else:
            # Vérifier toutes les dépendances core
            packages = self.dependencies.get("core", [])

        status = {}
        for package in packages:
            # Extraire le nom du package sans la version
            package_name = package.split(">=")[0].split("==")[0].split(">")[0].split("<")[0]
            package_name = package_name.replace("-", "_").lower()

            # Cas particuliers
            if package_name == "speechrecognition":
                package_name = "speech_recognition"
            elif package_name == "gtts":
                package_name = "gtts"
            elif package_name == "pyttsx3":
                package_name = "pyttsx3"
            elif package_name == "flask_cors":
                package_name = "flask_cors"

            status[package] = self.check_installed(package_name)

        return status

    def get_missing_dependencies(self, category: str = "core") -> List[str]:
        """Retourne la liste des dépendances manquantes"""
        status = self.check_dependencies(category)
        return [pkg for pkg, installed in status.items() if not installed]

    def print_status(self):
        """Affiche le statut des dépendances core"""
        print("\n=== Statut des dependances ===\n")
        status = self.check_dependencies("core")

        installed_count = sum(1 for _, is_installed in status.items() if is_installed)
        total_count = len(status)

        for package, is_installed in status.items():
            status_str = "[OK] Installe" if is_installed else "[X] Manquant"
            print(f"  {package}: {status_str}")

        print(f"\nTotal: {installed_count}/{total_count} packages installes")

        missing = self.get_missing_dependencies("core")
        if missing:
            print(f"\nPackages manquants: {', '.join(missing)}")
            print("\nPour installer les dependances manquantes:")
            print("  pip install -r requirements.txt")

# Instance globale du gestionnaire
_dependency_manager = None

def get_dependency_manager() -> DependencyManager:
    """Retourne l'instance du gestionnaire de dépendances"""
    global _dependency_manager
    if _dependency_manager is None:
        _dependency_manager = DependencyManager()
    return _dependency_manager

if __name__ == "__main__":
    dm = get_dependency_manager()
    dm.print_status()
