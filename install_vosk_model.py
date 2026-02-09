"""
Script de téléchargement et installation d'un modèle Vosk français
Alternative à PyAudio pour la reconnaissance vocale
"""

import os
import sys
import zipfile
import urllib.request
from pathlib import Path


def download_file(url: str, dest_path: str, description: str = "fichier"):
    """
    Telecharge un fichier avec barre de progression

    Args:
        url: URL du fichier a telecharger
        dest_path: Chemin de destination
        description: Description du fichier (pour la progression)
    """
    print(f"[DOWNLOAD] Telechargement de {description}...")

    def report_progress(block_num, block_size, total_size):
        """Affiche la progression du telechargement"""
        downloaded = block_num * block_size
        percent = min(100, (downloaded / total_size) * 100) if total_size > 0 else 0
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\r   Progression: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
              end='', flush=True)

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print()  # Nouvelle ligne apres la progression
        print(f"[OK] Telechargement termine: {dest_path}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Erreur lors du telechargement: {e}")
        return False


def extract_zip(zip_path: str, dest_dir: str):
    """
    Extrait un fichier ZIP

    Args:
        zip_path: Chemin du fichier ZIP
        dest_dir: Répertoire de destination
    """
    print(f"[EXTRACT] Extraction de {zip_path}...")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

        print(f"[OK] Extraction terminée: {dest_dir}")
        return True
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'extraction: {e}")
        return False


def install_vosk_model(model_name: str = "vosk-model-small-fr-0.22"):
    """
    Télécharge et installe un modèle Vosk

    Args:
        model_name: Nom du modèle à installer
    """
    # URL du modèle (modèle français léger ~50MB)
    base_url = "https://alphacephei.com/vosk/models"
    model_url = f"{base_url}/{model_name}.zip"

    # Répertoires
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    zip_path = models_dir / f"{model_name}.zip"
    model_path = models_dir / model_name

    # Vérifier si le modèle est déjà installé
    if model_path.exists():
        print(f"[OK] Le modèle {model_name} est déjà installé dans {model_path}")
        return str(model_path)

    # Télécharger le modèle
    if not download_file(model_url, str(zip_path), f"modèle {model_name}"):
        return None

    # Extraire le modèle
    if not extract_zip(str(zip_path), str(models_dir)):
        return None

    # Supprimer le fichier ZIP
    try:
        os.remove(zip_path)
        print(f"[DELETE]  Fichier ZIP supprimé")
    except:
        pass

    print(f"\n[SUCCESS] Modèle {model_name} installé avec succès !")
    print(f"[LOCATION] Emplacement: {model_path.absolute()}")

    return str(model_path)


def main():
    """Fonction principale"""
    print("="*70)
    print("  Installation du modèle Vosk pour la reconnaissance vocale française")
    print("="*70)
    print()

    # Modèles disponibles
    models = {
        "1": {
            "name": "vosk-model-small-fr-0.22",
            "description": "Modèle français léger (~50 MB) - Recommandé",
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"
        },
        "2": {
            "name": "vosk-model-fr-0.22",
            "description": "Modèle français complet (~1.2 GB) - Plus précis",
            "url": "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"
        }
    }

    print("Modèles disponibles:")
    print()
    for key, model in models.items():
        print(f"  {key}. {model['description']}")
    print()

    # Choisir le modèle
    choice = input("Choisissez un modèle (1 par défaut): ").strip() or "1"

    if choice not in models:
        print("[ERROR] Choix invalide")
        return 1

    selected_model = models[choice]

    print()
    print(f"Installation de: {selected_model['name']}")
    print()

    # Installer le modèle
    model_path = install_vosk_model(selected_model['name'])

    if model_path:
        print()
        print("="*70)
        print("[OK] Installation réussie !")
        print("="*70)
        print()
        print("Le modèle est prêt à être utilisé.")
        print()
        print("Pour tester la reconnaissance vocale:")
        print("  python test_vosk_stt.py")
        print()
        print("Pour utiliser dans l'application Whisp:")
        print("  - Le modèle sera détecté automatiquement")
        print("  - Ou spécifiez le chemin dans la configuration")
        print()
        return 0
    else:
        print()
        print("="*70)
        print("[ERROR] Échec de l'installation")
        print("="*70)
        print()
        print("Vous pouvez télécharger le modèle manuellement:")
        print(f"  {selected_model['url']}")
        print()
        print("Et extraire le ZIP dans le dossier 'models/'")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
