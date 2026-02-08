"""
Module de configuration du logging structuré pour Whisp Assistant
Fournit un système de logging centralisé avec rotation des fichiers
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Formatter pour ajouter des couleurs aux logs console"""

    # Codes ANSI pour les couleurs
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Ajouter la couleur au niveau de log
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Formater
        result = super().format(record)

        # Restaurer le levelname original
        record.levelname = levelname

        return result


def setup_logging(
    log_level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configure le logging pour toute l'application

    Args:
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si True, logger dans un fichier
        log_to_console: Si True, logger dans la console
        max_file_size: Taille maximale des fichiers de log en octets
        backup_count: Nombre de fichiers de backup à conserver
        log_dir: Répertoire pour les logs (défaut: ~/.whisp/logs)

    Returns:
        Le logger racine configuré
    """

    # Créer le dossier de logs
    if log_dir is None:
        log_dir = Path.home() / ".whisp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configurer le format
    # Format détaillé: timestamp | niveau | logger | message
    detailed_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    simple_format = '%(levelname)-8s | %(message)s'

    date_format = '%Y-%m-%d %H:%M:%S'

    # Créer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Supprimer les handlers existants pour éviter les doublons
    root_logger.handlers.clear()

    # Handler console avec couleurs
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        # Utiliser le formatter coloré si supporté
        if sys.stdout.isatty():  # Terminal interactif
            console_formatter = ColoredFormatter(
                detailed_format,
                datefmt=date_format
            )
        else:
            console_formatter = logging.Formatter(
                detailed_format,
                datefmt=date_format
            )

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Handler fichier avec rotation
    if log_to_file:
        # Fichier principal (tous les niveaux)
        file_handler = RotatingFileHandler(
            log_dir / f"whisp_{logging.getLevelName(log_level)}.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)

        file_formatter = logging.Formatter(
            detailed_format,
            datefmt=date_format
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Fichier d'erreurs (ERROR et CRITICAL uniquement)
        error_handler = RotatingFileHandler(
            log_dir / "whisp_errors.log",
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)

        error_formatter = logging.Formatter(
            detailed_format,
            datefmt=date_format
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # Logger pour les timings et performance
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger avec le nom spécifié

    Args:
        name: Nom du logger (généralement __name__ du module)

    Returns:
        Logger configuré
    """
    return logging.getLogger(name)


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Décorateur pour logger les appels de fonction

    Args:
        logger: Logger à utiliser (si None, utilise le logger racine)

    Usage:
        @log_function_call()
        def ma_fonction(arg1, arg2):
            pass
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = logger or logging.getLogger(func.__module__)
            _logger.debug(f"Appel de {func.__name__} avec args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                _logger.debug(f"{func.__name__} terminé avec succès")
                return result
            except Exception as e:
                _logger.error(f"{func.__name__} a échoué: {e}", exc_info=True)
                raise

        return wrapper

    return decorator


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """
    Log une exception avec contexte

    Args:
        logger: Logger à utiliser
        exception: Exception à logger
        context: Contexte additionnel
    """
    logger.error(f"Exception: {context}", exc_info=exception)


# =============================================================================
# INITIALISATION AUTOMATIQUE
# =============================================================================

# Créer le logger par défaut
default_logger = setup_logging()

# Logger spécifique pour Whisp
whisp_logger = get_logger("whisp")


# =============================================================================
# FONCTIONS D'AIDE
# ==============================================================================

def set_log_level(level: int):
    """
    Change le niveau de log dynamiquement

    Args:
        level: Nouveau niveau de logging
    """
    logging.getLogger().setLevel(level)
    whisp_logger.info(f"Niveau de log changé à: {logging.getLevelName(level)}")


def enable_debug_mode():
    """Active le mode debug (logs détaillés)"""
    set_log_level(logging.DEBUG)
    whisp_logger.debug("Mode debug activé")


def enable_production_mode():
    """Active le mode production (logs WARNING et supérieur)"""
    set_log_level(logging.WARNING)
    whisp_logger.warning("Mode production activé")


if __name__ == "__main__":
    # Tests du système de logging

    print("=== Test du système de logging ===\n")

    # Test de tous les niveaux
    whisp_logger.debug("Message DEBUG")
    whisp_logger.info("Message INFO")
    whisp_logger.warning("Message WARNING")
    whisp_logger.error("Message ERROR")
    whisp_logger.critical("Message CRITICAL")

    # Test avec un logger nommé
    test_logger = get_logger("test_module")
    test_logger.info("Message depuis un module de test")

    # Test du décorateur
    @log_function_call()
    def test_function(x, y):
        return x + y

    result = test_function(5, 3)
    print(f"\nRésultat: {result}")

    # Test d'exception
    try:
        raise ValueError("Test d'exception")
    except Exception as e:
        log_exception(whisp_logger, e, "Test de gestion d'exception")

    print(f"\nFichiers de log créés dans: {Path.home() / '.whisp' / 'logs'}")
