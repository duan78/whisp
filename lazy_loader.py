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
                # Si le module est en cours de chargement, c'est probablement une récursion
                # Au lieu de lever une exception, retourner un objet factice pour certains modules critiques
                if module_name == "speech_recognition" and attr == "Recognizer":
                    print(f"Récursion détectée pour {module_name}.{attr}, utilisation d'un import direct")
                    import speech_recognition as sr_direct
                    return getattr(sr_direct, attr)
                else:
                    raise ImportError(f"Détection de récursion lors du chargement de {module_name}.{attr}")
                
            if module_name not in sys.modules or isinstance(sys.modules[module_name], LazyModule):
                print(f"Chargement paresseux du module: {module_name}")
                try:
                    # Marquer le module comme en cours de chargement
                    _loading_modules[module_name] = time.time()
                    
                    # Importer le module
                    module = importlib.import_module(module_name)
                    
                    # Remplacer le proxy par le vrai module dans sys.modules
                    sys.modules[name] = module
                    
                    # Marquer le module comme chargé
                    _loaded_modules[module_name] = time.time() - _loading_modules.pop(module_name)
                    
                    return getattr(module, attr)
                except Exception as e:
                    # S'assurer que le module n'est plus marqué comme en cours de chargement
                    if module_name in _loading_modules:
                        _loading_modules.pop(module_name)
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
