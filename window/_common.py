"""
En-tête partagé du package de gestion des fenêtres pour l'assistant Whisp.

Ce module concentre les imports, globals et imports conditionnels selon l'OS
qui étaient historiquement placés en tête de ``window_manager.py``.
Les modules thématiques du package font ``from window._common import *``
pour en hériter sans modification de logique.
"""

import pyautogui
import subprocess
import time
import re
import os
import platform
from os_detection import get_os_type, is_windows, is_mac, is_linux
from error_handler import get_error_handler, ErrorCategory, ErrorSeverity

error_handler = get_error_handler()

# Désactiver le fail-safe de PyAutoGUI qui cause des erreurs
# lors du déplacement de la souris vers les coins de l'écran
pyautogui.FAILSAFE = False

# Pour le débogage
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Importations conditionnelles selon l'OS
if is_windows():
    import keyboard
    import ctypes
    from ctypes import wintypes
    try:
        import win32gui
        import win32con
        import win32api
        import win32process
    except ImportError:
        print("Modules win32 non disponibles. Certaines fonctionnalités seront limitées.")
elif is_mac():
    try:
        import Quartz
        import AppKit
    except ImportError:
        print("Modules Quartz et AppKit non disponibles. Certaines fonctionnalités seront limitées.")
elif is_linux():
    try:
        import Xlib.display
        import Xlib.X
    except ImportError:
        print("Module python-xlib non disponible. Certaines fonctionnalités seront limitées.")

# Importer le dictionnaire des sites populaires depuis browser_commands
try:
    from browser_commands import SITES_POPULAIRES
except ImportError:
    # Définir un dictionnaire vide si l'import échoue
    SITES_POPULAIRES = {}
