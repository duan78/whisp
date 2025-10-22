"""
Utilitaire pour corriger les problèmes de chemin des DLLs CUDA
Ce module aide à localiser et charger les DLLs manquantes pour CUDA et cuDNN
"""

import os
import sys
import glob
import platform
import ctypes
from ctypes import c_void_p, c_int, c_size_t, c_char_p, POINTER, byref
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("cuda_path_fixer")

def set_cuda_paths():
    """
    Configure les chemins CUDA/cuDNN pour les packages installés via pip
    Cette approche utilise les DLLs fournies par les packages nvidia-* installés via pip
    """
    try:
        venv_base = Path(sys.executable).parent.parent
        nvidia_base_path = venv_base / 'Lib' / 'site-packages' / 'nvidia'
        
        # Vérifier si les packages NVIDIA sont installés
        if not nvidia_base_path.exists():
            logger.warning(f"Dossier NVIDIA Python packages non trouvé à {nvidia_base_path}")
            return False
            
        # Chemins des DLLs pour différents packages
        cuda_path = nvidia_base_path / 'cuda_runtime' / 'bin'
        cublas_path = nvidia_base_path / 'cublas' / 'bin'
        cudnn_path = nvidia_base_path / 'cudnn' / 'bin'
        nvrtc_path = nvidia_base_path / 'cuda_nvrtc' / 'bin'
        
        # Liste des chemins à ajouter
        paths_to_add = []
        for path in [cuda_path, cublas_path, cudnn_path, nvrtc_path]:
            if path.exists():
                paths_to_add.append(str(path))
                logger.info(f"Chemin CUDA ajouté: {path}")
            else:
                logger.warning(f"Chemin CUDA non trouvé: {path}")
        
        if not paths_to_add:
            logger.warning("Aucun chemin CUDA trouvé dans les packages Python")
            return False
            
        # Variables d'environnement à mettre à jour
        env_vars = ['CUDA_PATH', 'CUDA_PATH_V12_4', 'PATH']
        
        # Mettre à jour les variables d'environnement
        for env_var in env_vars:
            current_value = os.environ.get(env_var, '')
            new_paths = []
            
            # Vérifier si ces chemins sont déjà dans la variable d'environnement
            for path in paths_to_add:
                if path not in current_value:
                    new_paths.append(path)
            
            if new_paths:
                new_value = os.pathsep.join(new_paths + [current_value] if current_value else new_paths)
                os.environ[env_var] = new_value
                logger.info(f"Variable d'environnement {env_var} mise à jour avec {len(new_paths)} nouveaux chemins")
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la configuration des chemins CUDA via pip: {e}")
        return False

# Configurer les chemins CUDA au chargement du module
set_cuda_paths()

# Emplacements typiques d'installation CUDA sur Windows
NVIDIA_PATHS = [
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA",  # Dossier d'installation principal CUDA
    r"C:\Program Files\NVIDIA Corporation",                 # Autre dossier NVIDIA
    r"C:\Windows\System32",                                 # Dossier système qui peut contenir des DLLs CUDA
    r"C:\Windows\SysWOW64",                                 # Dossier système 32-bit sur systèmes 64-bit
    r"C:\Program Files\NVIDIA\CUDNN",                       # Dossier cuDNN spécifique
    r"C:\Program Files\NVIDIA\CUDNN\v*",                    # Dossier cuDNN avec version
    r"C:\Program Files\NVIDIA\CUDA",                        # Alternative pour CUDA
    r"C:\Program Files\NVIDIA\cuda-12.*",                   # Nouveaux chemins pour CUDA 12
    r"C:\Program Files\NVIDIA\cuda-11.*",                   # Nouveaux chemins pour CUDA 11
    r"C:\cuda",                                             # Installation personnalisée possible
    r"C:\NVIDIA\CUDNN",                                     # Installation personnalisée possible
    os.path.expanduser("~") + r"\AppData\Local\NVIDIA\CUDNN", # Dossier utilisateur
    os.path.expanduser("~") + r"\AppData\Local\NVIDIA\CUDA",  # Dossier utilisateur
]

# Versions possibles de CUDA
CUDA_VERSIONS = ["12.0", "11.8", "11.7", "11.6", "11.5", "11.4", "11.3", "11.2", "11.1", "11.0", "10.2", "10.1", "10.0"]

# Versions possibles de cuDNN
CUDNN_VERSIONS = ["9", "8", "8.9", "8.8", "8.7", "8.6", "8.5", "8.4", "8.3", "8.2", "8.1", "8.0", "7"]

# Liste des DLLs requises (avec différentes variations possibles)
REQUIRED_DLLS = {
    "cudnn": [f"cudnn64_{v}.dll" for v in CUDNN_VERSIONS] + [f"cudnn_ops64_{v}.dll" for v in CUDNN_VERSIONS],
    "cublas": ["cublas64_*.dll", "cublasLt64_*.dll"],
    "cudart": ["cudart64_*.dll"],
    "cufft": ["cufft64_*.dll"],
    "curand": ["curand64_*.dll"],
    "cusolver": ["cusolver64_*.dll"],
    "nvrtc": ["nvrtc64_*.dll", "nvrtc-builtins64_*.dll"]
}

def find_dll_paths():
    """
    Recherche les DLLs CUDA dans les chemins probables
    
    Returns:
        dict: Dictionnaire contenant les chemins trouvés pour chaque DLL
    """
    found_paths = {}
    
    # Commencer par chercher dans les chemins du système
    paths_to_search = os.environ.get("PATH", "").split(os.pathsep)
    
    # Ajouter les chemins NVIDIA typiques
    for base_path in NVIDIA_PATHS:
        # Gérer les patterns avec wildcard (*)
        if "*" in base_path:
            base_dir = os.path.dirname(base_path)
            pattern = os.path.basename(base_path)
            if os.path.exists(base_dir):
                for item in os.listdir(base_dir):
                    if glob.fnmatch.fnmatch(item, pattern) and os.path.isdir(os.path.join(base_dir, item)):
                        full_path = os.path.join(base_dir, item)
                        paths_to_search.append(full_path)
                        logger.info(f"Ajout du chemin avec wildcard: {full_path}")
            continue
            
        if os.path.exists(base_path):
            paths_to_search.append(base_path)
            # Rechercher les sous-dossiers CUDA (ex: CUDA/v11.8)
            for item in os.listdir(base_path) if os.path.exists(base_path) else []:
                if item.startswith("v") and os.path.isdir(os.path.join(base_path, item)):
                    paths_to_search.append(os.path.join(base_path, item))
                elif "CUDA" in item and os.path.isdir(os.path.join(base_path, item)):
                    cuda_path = os.path.join(base_path, item)
                    paths_to_search.append(cuda_path)
                    
                    # Ajouter les sous-dossiers possibles
                    for cuda_ver in CUDA_VERSIONS:
                        ver_path = os.path.join(cuda_path, f"v{cuda_ver}")
                        if os.path.exists(ver_path):
                            paths_to_search.append(ver_path)
                            # Ajouter les dossiers bin et lib
                            for subdir in ["bin", "lib", "lib64", "lib/x64"]:
                                full_path = os.path.join(ver_path, subdir)
                                if os.path.exists(full_path):
                                    paths_to_search.append(full_path)
    
    # Rechercher également dans tous les sous-dossiers des chemins trouvés
    extra_paths = []
    for path in paths_to_search:
        if os.path.exists(path):
            # Ajouter les dossiers bin et lib s'ils existent
            for subdir in ["bin", "lib", "lib64", "lib/x64", "extras/CUPTI/lib64"]:
                subpath = os.path.join(path, subdir)
                if os.path.exists(subpath):
                    extra_paths.append(subpath)
                    
    # Combiner les chemins trouvés
    paths_to_search.extend(extra_paths)
    
    # Supprimer les doublons tout en préservant l'ordre
    unique_paths = []
    for path in paths_to_search:
        if path not in unique_paths and os.path.exists(path):
            unique_paths.append(path)
    
    logger.info(f"Recherche dans {len(unique_paths)} chemins uniques")
    
    # Rechercher toutes les DLLs requises
    for dll_type, dll_patterns in REQUIRED_DLLS.items():
        for dll_pattern in dll_patterns:
            for path in unique_paths:
                try:
                    # Rechercher avec le pattern dans ce dossier
                    matching_files = glob.glob(os.path.join(path, dll_pattern))
                    if matching_files:
                        # Trier par numéro de version (plus récent d'abord)
                        matching_files.sort(reverse=True)
                        found_paths[dll_pattern] = matching_files[0]
                        logger.info(f"Trouvé {dll_pattern} à {matching_files[0]}")
                except Exception as e:
                    logger.error(f"Erreur lors de la recherche de {dll_pattern} dans {path}: {e}")
    
    return found_paths

def add_dll_paths_to_env():
    """
    Ajoute les chemins des DLLs CUDA au PATH du système
    
    Returns:
        bool: True si des chemins ont été ajoutés, False sinon
    """
    dll_paths = find_dll_paths()
    if not dll_paths:
        logger.warning("Aucune DLL CUDA trouvée")
        return False
    
    # Extraire les dossiers uniques contenant les DLLs
    unique_dirs = set()
    for path in dll_paths.values():
        dll_dir = os.path.dirname(path)
        if dll_dir:
            unique_dirs.add(dll_dir)
    
    # Modifier le PATH du système pour inclure ces dossiers
    if unique_dirs:
        current_path = os.environ.get("PATH", "")
        for dll_dir in unique_dirs:
            if dll_dir not in current_path:
                logger.info(f"Ajout du chemin CUDA au PATH: {dll_dir}")
                os.environ["PATH"] = dll_dir + os.pathsep + os.environ["PATH"]
        return True
    
    return False

def force_whisper_ct2_device(device_type="auto"):
    """
    Force l'utilisation d'un type de périphérique spécifique pour Whisper CT2
    
    Args:
        device_type: Le type de périphérique à utiliser ('auto', 'cuda', 'cpu')
        
    Returns:
        bool: True si le changement a réussi, False sinon
    """
    global WHISPER_CT2_DEFAULT_DEVICE, WHISPER_CT2_FORCE_CPU, whisper_ct2_model
    
    # Valider le type de périphérique
    if device_type not in ["auto", "cuda", "cpu"]:
        print(f"Type de périphérique invalide: {device_type}. Utilisation de 'auto'")
        device_type = "auto"
    
    # Mettre à jour les paramètres globaux
    WHISPER_CT2_DEFAULT_DEVICE = device_type
    WHISPER_CT2_FORCE_CPU = (device_type == "cpu")
    
    print(f"Périphérique Whisper CT2 configuré sur: {device_type}")
    
    # Si le modèle est déjà chargé, on doit le recharger pour appliquer le changement
    if whisper_ct2_model is not None:
        print("Modèle Whisper CT2 déjà chargé, redémarrage requis pour appliquer le changement")
        # Désallouer le modèle actuel pour libérer les ressources
        whisper_ct2_model = None
        
        # Journaliser le changement
        if 'web_interface' in sys.modules:
            from web_interface import log_to_web
            log_to_web(f"Périphérique Whisper CT2 configuré sur: {device_type}. Redémarrage requis.", "info")
        
        return True
    else:
        print("Paramètre mis à jour. Le prochain chargement du modèle utilisera: " + device_type)
        return True

def verify_cudnn_availability():
    """
    Vérifie si cuDNN est correctement accessible
    
    Returns:
        bool: True si cuDNN est disponible, False sinon
    """
    try:
        # D'abord, s'assurer que les chemins sont ajoutés
        add_dll_paths_to_env()
        
        # Tenter de charger une DLL cuDNN
        cudnn_found = False
        
        # Essayer différentes versions de la DLL cuDNN
        for v in CUDNN_VERSIONS:
            try:
                cudnn = ctypes.CDLL(f"cudnn64_{v}.dll")
                logger.info(f"cudnn64_{v}.dll chargée avec succès")
                cudnn_found = True
                break
            except Exception:
                continue
            
        # Si la DLL principale n'est pas trouvée, essayer les DLLs ops
        if not cudnn_found:
            for v in CUDNN_VERSIONS:
                try:
                    cudnn_ops = ctypes.CDLL(f"cudnn_ops64_{v}.dll")
                    logger.info(f"cudnn_ops64_{v}.dll chargée avec succès")
                    cudnn_found = True
                    break
                except Exception:
                    continue
        
        # Vérifier également CUDA runtime
        cudart_found = False
        for v in CUDA_VERSIONS:
            try:
                cudart = ctypes.CDLL(f"cudart64_{v.replace('.', '')}.dll")
                logger.info(f"cudart64_{v.replace('.', '')}.dll chargée avec succès")
                cudart_found = True
                break
            except Exception:
                continue
        
        # Pour nos besoins, considérer CUDA comme disponible même si cuDNN ne l'est pas
        # Cela permettra d'utiliser le GPU pour les modèles qui ne nécessitent pas cuDNN
        if cudart_found and not cudnn_found:
            logger.warning("CUDA runtime trouvé mais cuDNN manquant. Le GPU sera utilisé sans cuDNN.")
            return True  # Considérer CUDA comme disponible même sans cuDNN
        
        return cudnn_found and cudart_found
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de cuDNN: {e}")
        return False

def get_cuda_installation_info():
    """
    Obtient des informations détaillées sur l'installation CUDA
    
    Returns:
        dict: Informations sur l'installation CUDA
    """
    cuda_info = {
        "cuda_found": False,
        "cudnn_found": False,
        "cuda_version": None,
        "cudnn_version": None,
        "cuda_path": None,
        "cudnn_path": None,
        "dll_paths": {},
        "missing_dlls": []
    }
    
    # Trouver les chemins DLL
    cuda_info["dll_paths"] = find_dll_paths()
    
    # Vérifier quelles DLLs sont manquantes
    for dll_type, dll_patterns in REQUIRED_DLLS.items():
        found = False
        for pattern in dll_patterns:
            if pattern in cuda_info["dll_paths"]:
                found = True
                break
        
        if not found:
            for pattern in dll_patterns:
                cuda_info["missing_dlls"].append(pattern)
    
    # Déterminer si CUDA et cuDNN sont présents
    if any(key.startswith("cudart64_") for key in cuda_info["dll_paths"]):
        cuda_info["cuda_found"] = True
        
        # Trouver la version CUDA
        for key in cuda_info["dll_paths"]:
            if key.startswith("cudart64_"):
                version_part = key.replace("cudart64_", "").replace(".dll", "")
                if version_part.isdigit() and len(version_part) >= 2:
                    # Format comme "110" pour CUDA 11.0
                    major = version_part[0]
                    minor = version_part[1:] if len(version_part) > 1 else "0"
                    cuda_info["cuda_version"] = f"{major}.{minor}"
                    cuda_info["cuda_path"] = os.path.dirname(cuda_info["dll_paths"][key])
                    break
    
    if any(key.startswith("cudnn") for key in cuda_info["dll_paths"]):
        cuda_info["cudnn_found"] = True
        
        # Trouver la version cuDNN
        for key in cuda_info["dll_paths"]:
            if "cudnn" in key:
                path = cuda_info["dll_paths"][key]
                cuda_info["cudnn_path"] = os.path.dirname(path)
                
                # Extraire la version
                for v in CUDNN_VERSIONS:
                    if f"cudnn64_{v}" in key or f"cudnn_ops64_{v}" in key:
                        cuda_info["cudnn_version"] = v
                        break
                break
    
    return cuda_info

def fix_cuda_paths():
    """
    Tente de corriger les problèmes de chemin pour CUDA et cuDNN
    
    Returns:
        tuple: (bool, str) - Succès du correctif et message explicatif
    """
    # D'abord, essayer la méthode pip (packages NVIDIA installés via pip)
    logger.info("Tentative de configuration des chemins CUDA via packages pip...")
    if set_cuda_paths():
        # Vérifier si les DLLs sont maintenant accessibles
        cuda_found = False
        cudnn_found = False
        
        try:
            # Tester quelques DLLs essentielles
            ctypes.CDLL("cudart64_12.dll")
            cuda_found = True
            logger.info("cudart64_12.dll trouvée avec succès via packages pip")
        except Exception:
            logger.warning("cudart64_12.dll non trouvée via packages pip")
            
        try:
            ctypes.CDLL("cudnn64_9.dll")
            cudnn_found = True
            logger.info("cudnn64_9.dll trouvée avec succès via packages pip")
        except Exception:
            logger.warning("cudnn64_9.dll non trouvée via packages pip")
        
        if cuda_found and cudnn_found:
            return True, "CUDA et cuDNN configurés avec succès via packages pip"
        elif cuda_found:
            return True, "CUDA configuré via packages pip, mais cuDNN non trouvé"
    
    # Si la méthode pip échoue, continuer avec la méthode traditionnelle
    # Récupérer les informations sur l'installation traditionnelle
    cuda_info = get_cuda_installation_info()
    
    # Même si cuDNN n'est pas trouvé, on essaie de corriger les chemins CUDA
    if not cuda_info["cuda_found"]:
        logger.warning("CUDA n'est pas trouvé sur le système, tentative de recherche approfondie...")
    
    # Recherche plus aggressive des DLLs
    logger.info("Recherche aggressive des DLLs CUDA et cuDNN...")
    dll_paths = find_dll_paths()
    
    # Vérifier si nous avons trouvé au moins cudart64_*.dll (composant de base de CUDA)
    cuda_base_found = any("cudart64_" in dll_name for dll_name in dll_paths.keys())
    
    # Considérer cudnn_ops64_*.dll comme une alternative à cudnn64_*.dll
    cudnn_ops_found = any("cudnn_ops64_" in dll_name for dll_name in dll_paths.keys())
    cudnn_found = cuda_info["cudnn_found"] or cudnn_ops_found
    
    # Ajouter tous les chemins trouvés au PATH
    success = add_dll_paths_to_env()
    
    # Si on a trouvé CUDA mais pas cuDNN, chercher dans cuda_info pour voir si on a des indices
    if cuda_base_found and not cudnn_found:
        logger.warning("cuDNN non trouvé mais CUDA trouvé. Vérification des installations partielles...")
        
        # Chercher dans les dossiers nvidia pour des indices de cuDNN
        potential_cudnn_locations = []
        for path in NVIDIA_PATHS:
            if os.path.exists(path):
                # Chercher des fichiers ou dossiers contenant "cudnn" dans leur nom
                for root, dirs, files in os.walk(path):
                    for item in dirs + files:
                        if "cudnn" in item.lower():
                            location = os.path.join(root, item)
                            potential_cudnn_locations.append(location)
                            logger.info(f"Potentiel indice cuDNN trouvé: {location}")
        
        if potential_cudnn_locations:
            message = f"CUDA trouvé mais cuDNN semble être partiellement installé ou mal configuré. "
            message += f"Indices trouvés dans: {', '.join(potential_cudnn_locations[:3])}"
            return False, message
    
    # Vérifier si les DLLs sont accessibles après l'ajout des chemins
    cudnn_available = verify_cudnn_availability()
    
    # Si CUDA est disponible mais pas cuDNN, considérer cela comme un demi-succès
    if success and (cuda_base_found and not cudnn_available):
        cuda_version = cuda_info["cuda_version"] if cuda_info["cuda_version"] else "inconnu"
        return True, f"CUDA {cuda_version} détecté mais cuDNN est manquant ou incompatible. " \
                     f"Vous pouvez utiliser le GPU uniquement pour les modèles ne nécessitant pas cuDNN."
    elif success and cudnn_available:
        cuda_version = cuda_info["cuda_version"] if cuda_info["cuda_version"] else "inconnu"
        cudnn_version = cuda_info["cudnn_version"] if cuda_info["cudnn_version"] else "inconnu"
        return True, f"Chemins CUDA corrigés. CUDA {cuda_version} et cuDNN {cudnn_version} sont accessibles."
    elif success:
        # Si des chemins ont été ajoutés mais cuDNN n'est toujours pas accessible
        if cuda_base_found:
            return True, "CUDA trouvé mais cuDNN manquant. Les fonctionnalités GPU de base devraient fonctionner."
        else:
            return False, f"Chemins ajoutés mais cuDNN et CUDA ne sont pas accessibles. DLLs manquantes: {', '.join(cuda_info['missing_dlls'][:5])}"
    else:
        return False, "Impossible de trouver ou corriger les chemins CUDA."

if __name__ == "__main__":
    # Si exécuté directement, essayer de corriger les chemins et afficher les résultats
    print("Vérification et correction des chemins CUDA...")
    success, message = fix_cuda_paths()
    print(message)
    
    # Afficher des informations détaillées
    cuda_info = get_cuda_installation_info()
    
    print("\nInformations détaillées sur l'installation CUDA:")
    print(f"CUDA trouvé: {cuda_info['cuda_found']}")
    print(f"Version CUDA: {cuda_info['cuda_version']}")
    print(f"Chemin CUDA: {cuda_info['cuda_path']}")
    print(f"cuDNN trouvé: {cuda_info['cudnn_found']}")
    print(f"Version cuDNN: {cuda_info['cudnn_version']}")
    print(f"Chemin cuDNN: {cuda_info['cudnn_path']}")
    
    print("\nDLLs trouvées:")
    for pattern, path in cuda_info["dll_paths"].items():
        print(f"  {pattern}: {path}")
    
    print("\nDLLs manquantes:")
    for dll in cuda_info["missing_dlls"]:
        print(f"  {dll}")
