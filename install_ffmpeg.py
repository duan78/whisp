"""
Script d'installation de ffmpeg pour l'assistant vocal Whisp
"""

import os
import sys
import platform
import subprocess
import shutil
import zipfile
import urllib.request

def get_ffmpeg_url():
    """Retourne l'URL de téléchargement de ffmpeg en fonction du système d'exploitation"""
    system = platform.system()
    if system == "Windows":
        return "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    elif system == "Darwin":  # macOS
        return "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
    else:  # Linux
        return None  # Installation via le gestionnaire de paquets

def install_ffmpeg_windows(download_url):
    """Installe ffmpeg sur Windows"""
    print("Téléchargement de ffmpeg...")
    
    # Créer un dossier temporaire
    temp_dir = os.path.join(os.path.expanduser("~"), "ffmpeg_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Télécharger le fichier zip
    zip_path = os.path.join(temp_dir, "ffmpeg.zip")
    urllib.request.urlretrieve(download_url, zip_path)
    
    print("Extraction des fichiers...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Trouver le dossier bin contenant les exécutables
    bin_dir = None
    for root, dirs, files in os.walk(temp_dir):
        if "ffmpeg.exe" in files:
            bin_dir = root
            break
    
    if not bin_dir:
        print("Impossible de trouver ffmpeg.exe dans l'archive téléchargée.")
        return False
    
    # Créer le dossier de destination
    dest_dir = os.path.join(os.path.expanduser("~"), "ffmpeg", "bin")
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copier les fichiers exécutables
    for file in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
        if os.path.exists(os.path.join(bin_dir, file)):
            shutil.copy2(os.path.join(bin_dir, file), os.path.join(dest_dir, file))
    
    # Ajouter au PATH
    user_path = os.environ.get("PATH", "")
    if dest_dir not in user_path:
        print(f"Ajout de {dest_dir} au PATH...")
        # Cette commande modifie le PATH pour la session en cours
        os.environ["PATH"] = dest_dir + os.pathsep + user_path
        
        # Pour une modification permanente, on utilise setx (Windows uniquement)
        subprocess.run(["setx", "PATH", f"{dest_dir};%PATH%"], shell=True)
    
    # Nettoyer les fichiers temporaires
    shutil.rmtree(temp_dir)
    
    print("ffmpeg a été installé avec succès!")
    return True

def install_ffmpeg_macos():
    """Installe ffmpeg sur macOS"""
    try:
        # Vérifier si Homebrew est installé
        subprocess.run(["brew", "--version"], check=True, stdout=subprocess.PIPE)
        
        # Installer ffmpeg via Homebrew
        print("Installation de ffmpeg via Homebrew...")
        subprocess.run(["brew", "install", "ffmpeg"], check=True)
        
        print("ffmpeg a été installé avec succès!")
        return True
    except subprocess.CalledProcessError:
        print("Homebrew n'est pas installé. Installation de Homebrew...")
        try:
            # Installer Homebrew
            install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            subprocess.run(install_cmd, shell=True, check=True)
            
            # Installer ffmpeg
            print("Installation de ffmpeg via Homebrew...")
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
            
            print("ffmpeg a été installé avec succès!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de l'installation: {e}")
            return False

def install_ffmpeg_linux():
    """Installe ffmpeg sur Linux"""
    try:
        # Détecter la distribution
        if os.path.exists("/etc/debian_version"):
            # Debian/Ubuntu
            print("Installation de ffmpeg via apt...")
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
        elif os.path.exists("/etc/fedora-release"):
            # Fedora
            print("Installation de ffmpeg via dnf...")
            subprocess.run(["sudo", "dnf", "install", "-y", "ffmpeg"], check=True)
        elif os.path.exists("/etc/arch-release"):
            # Arch Linux
            print("Installation de ffmpeg via pacman...")
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"], check=True)
        else:
            print("Distribution Linux non reconnue. Veuillez installer ffmpeg manuellement.")
            return False
        
        print("ffmpeg a été installé avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'installation: {e}")
        return False

def main():
    """Fonction principale"""
    print("=== Installation de ffmpeg pour Whisp Assistant ===")
    
    system = platform.system()
    
    # Vérifier si ffmpeg est déjà installé
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg est déjà installé sur votre système.")
        return
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffmpeg n'est pas installé ou n'est pas dans le PATH.")
    
    if system == "Windows":
        url = get_ffmpeg_url()
        if url:
            install_ffmpeg_windows(url)
        else:
            print("Impossible de déterminer l'URL de téléchargement pour votre système.")
    elif system == "Darwin":  # macOS
        install_ffmpeg_macos()
    elif system == "Linux":
        install_ffmpeg_linux()
    else:
        print(f"Système d'exploitation non pris en charge: {system}")
        print("Veuillez installer ffmpeg manuellement.")

if __name__ == "__main__":
    main()
