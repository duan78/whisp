"""
Module de chargement paresseux (lazy loading) pour améliorer le temps de démarrage
"""

import importlib
import threading
import time
import sys
from functools import wraps

# Dictionnaire pour suivre les modules en cours de chargement
_loading_modules = {}
_loaded_modules = {}

def lazy_import(module_name, as_name=None):
    """
    Importe un module de manière paresseuse (uniquement lors de la première utilisation)
    
    Args:
        module_name: Nom du module à importer
        as_name: Nom à utiliser pour le module (comme dans 'import X as Y')
    
    Returns:
        Un proxy qui chargera le module lors de la première utilisation
    """
    name = as_name or module_name
    
    class LazyModule:
        def __getattr__(self, attr):
            # Vérifier si le module est déjà en cours de chargement
            if module_name in _loading_modules:
                loader_thread = _loading_modules[module_name].get("thread")
                if loader_thread == threading.get_ident():
                    # Chargé par le MÊME thread : véritable récursion.
                    # Au lieu de lever une exception, retourner un objet factice pour certains modules critiques
                    if module_name == "speech_recognition" and attr == "Recognizer":
                        print(f"Récursion détectée pour {module_name}.{attr}, utilisation d'un import direct")
                        import speech_recognition as sr_direct
                        return getattr(sr_direct, attr)
                    else:
                        raise ImportError(f"Détection de récursion lors du chargement de {module_name}.{attr}")

                # Chargé par un AUTRE thread : simple accès concurrent —
                # attendre la fin du chargement au lieu de lever une erreur.
                deadline = time.time() + 60.0
                while module_name in _loading_modules and time.time() < deadline:
                    time.sleep(0.05)
                if module_name in sys.modules and not isinstance(sys.modules[module_name], LazyModule):
                    return getattr(sys.modules[module_name], attr)
                # Timeout ou échec : tenter un import direct (l'import lock de
                # CPython sérialise les importations concurrentes)
                module = importlib.import_module(module_name)
                return getattr(module, attr)

            if module_name not in sys.modules or isinstance(sys.modules[module_name], LazyModule):
                print(f"Chargement paresseux du module: {module_name}")
                try:
                    # Marquer le module comme en cours de chargement
                    _loading_modules[module_name] = {
                        "thread": threading.get_ident(),
                        "start": time.time(),
                    }

                    # Importer le module
                    module = importlib.import_module(module_name)

                    # Remplacer le proxy par le vrai module dans sys.modules
                    sys.modules[name] = module

                    # Marquer le module comme chargé
                    start = _loading_modules.pop(module_name)["start"]
                    _loaded_modules[module_name] = time.time() - start

                    return getattr(module, attr)
                except Exception as e:
                    # S'assurer que le module n'est plus marqué comme en cours de chargement
                    _loading_modules.pop(module_name, None)
                    print(f"Erreur lors du chargement paresseux de {module_name}: {e}")
                    raise
            else:
                # Le module est déjà chargé, accéder à l'attribut
                return getattr(sys.modules[module_name], attr)
    
    # Créer une instance du proxy
    lazy_module = LazyModule()
    
    # Enregistrer le proxy dans sys.modules
    sys.modules[name] = lazy_module
    
    return lazy_module

def background_load(module_name):
    """
    Charge un module en arrière-plan
    
    Args:
        module_name: Nom du module à charger
    """
    def load_module():
        try:
            print(f"Chargement en arrière-plan du module: {module_name}")
            start_time = time.time()
            importlib.import_module(module_name)
            duration = time.time() - start_time
            print(f"Module {module_name} chargé en {duration:.2f}s")
        except Exception as e:
            print(f"Erreur lors du chargement en arrière-plan de {module_name}: {e}")
    
    thread = threading.Thread(target=load_module, daemon=True)
    thread.start()
    return thread

def lazy_function(func):
    """
    Décorateur pour charger une fonction de manière paresseuse
    
    Args:
        func: Fonction à charger paresseusement
    
    Returns:
        Une fonction wrapper qui chargera la vraie fonction lors du premier appel
    """
    # Stocker les informations sur la fonction
    module_name = func.__module__
    func_name = func.__name__
    _real_func = [None]  # Utiliser une liste pour pouvoir modifier la référence
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Si la fonction n'a pas encore été chargée, la charger
        if _real_func[0] is None:
            try:
                print(f"Chargement paresseux de la fonction: {module_name}.{func_name}")
                module = importlib.import_module(module_name)
                _real_func[0] = getattr(module, func_name)
            except Exception as e:
                print(f"Erreur lors du chargement paresseux de {module_name}.{func_name}: {e}")
                raise
        
        # Appeler la vraie fonction
        return _real_func[0](*args, **kwargs)
    
    return wrapper

def get_loading_stats():
    """
    Retourne des statistiques sur les modules chargés
    
    Returns:
        Un dictionnaire avec les statistiques de chargement
    """
    return {
        "loading": _loading_modules,
        "loaded": _loaded_modules
    }
