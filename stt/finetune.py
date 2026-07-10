"""
Pipeline de fine-tuning: sauvegarde d'échantillons audio et génération
de datasets au format Hugging Face.
"""
import os
import json
import wave
import time

try:
    import numpy as np
except ImportError:
    np = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


def save_audio_for_fine_tuning(audio_data, recognized_text, stt_engine, audio_format="wav", sample_rate=16000):
    """
    Sauvegarde l'audio et le texte reconnu pour un fine tuning ultérieur
    dans un format compatible avec Hugging Face Datasets

    Args:
        audio_data: Données audio à sauvegarder (bytes, AudioData, numpy array ou file-like)
        recognized_text: Texte reconnu
        stt_engine: Moteur STT utilisé (speechrecognition, whisper, vosk, whisper_ct2)
        audio_format: Format d'enregistrement (wav par défaut)
        sample_rate: Taux d'échantillonnage pour les données audio brutes (16000 par défaut)
    """
    if not recognized_text or len(recognized_text.strip()) == 0:
        return False  # Ne pas enregistrer si le texte est vide

    try:
        # Créer le dossier records s'il n'existe pas
        records_dir = os.path.join(os.getcwd(), "records")
        os.makedirs(records_dir, exist_ok=True)

        # Créer un sous-dossier pour chaque moteur
        engine_dir = os.path.join(records_dir, stt_engine)
        os.makedirs(engine_dir, exist_ok=True)

        # Créer un sous-dossier pour les splits de Hugging Face (par défaut tout dans train)
        split = "train"  # Pourrait être paramétré ou calculé (ex: 80% train, 10% validation, 10% test)
        split_dir = os.path.join(engine_dir, split)
        os.makedirs(split_dir, exist_ok=True)

        # Générer un nom de fichier unique basé sur l'horodatage
        timestamp = int(time.time())
        filename_base = f"{timestamp}_{stt_engine}"
        audio_path = os.path.join(split_dir, f"{filename_base}.{audio_format}")
        text_path = os.path.join(split_dir, f"{filename_base}.txt")

        # Chemin relatif pour le dataset
        rel_audio_path = os.path.join(stt_engine, split, f"{filename_base}.{audio_format}")

        # Variables pour les métadonnées
        audio_duration = None
        audio_sample_rate = sample_rate
        audio_sample_width = 2  # 16 bits par défaut

        # Convertir et sauvegarder l'audio dans un format approprié
        if isinstance(audio_data, sr.AudioData):
            # Pour les objets AudioData de SpeechRecognition
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(audio_data.sample_width)
                wf.setframerate(audio_data.sample_rate)
                wf.writeframes(audio_data.frame_data)
            audio_duration = len(audio_data.frame_data) / (audio_data.sample_rate * audio_data.sample_width)
            audio_sample_rate = audio_data.sample_rate
            audio_sample_width = audio_data.sample_width
        elif isinstance(audio_data, str) and os.path.exists(audio_data):
            # Pour les chemins de fichiers
            with open(audio_data, 'rb') as src_file:
                with open(audio_path, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            # Tenter d'obtenir la durée audio
            try:
                with wave.open(audio_data, 'rb') as wf:
                    audio_duration = wf.getnframes() / wf.getframerate()
                    audio_sample_rate = wf.getframerate()
                    audio_sample_width = wf.getsampwidth()
            except Exception:
                pass
        elif isinstance(audio_data, bytes):
            # Pour les données audio brutes en bytes
            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            audio_duration = len(audio_data) / (sample_rate * 2)
        elif isinstance(audio_data, np.ndarray):
            # Pour les tableaux numpy
            if audio_data.dtype == np.float32:
                # Convertir les flottants en int16
                audio_data = (audio_data * 32767).astype(np.int16)

            with wave.open(audio_path, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            audio_duration = len(audio_data) / sample_rate

        # Sauvegarder le texte reconnu
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(recognized_text)

        # Créer un fichier JSON avec les métadonnées pour le fine-tuning
        metadata = {
            "audio_file": os.path.basename(audio_path),
            "text": recognized_text,
            "engine": stt_engine,
            "timestamp": timestamp,
            "duration": audio_duration,
            "sample_rate": audio_sample_rate,
            "sample_width": audio_sample_width,
            "split": split
        }

        # Enregistrer les métadonnées
        json_path = os.path.join(split_dir, f"{filename_base}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Mettre à jour le fichier metadata.jsonl global (format compatible HF)
        metadata_entry = {
            "path": rel_audio_path,
            "audio": {
                "path": rel_audio_path,
                "array": None,  # Non stocké dans le JSON
                "sampling_rate": audio_sample_rate
            },
            "sentence": recognized_text,
            "transcription": recognized_text,
            "engine": stt_engine,
            "duration": audio_duration,
            "timestamp": timestamp,
            "split": split
        }

        metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")

        # Ajouter l'entrée au fichier jsonl (1 JSON par ligne)
        with open(metadata_jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metadata_entry, ensure_ascii=False) + "\n")

        # Mettre à jour ou créer le fichier dataset_info.json si nécessaire
        dataset_info_path = os.path.join(records_dir, "dataset_info.json")
        if not os.path.exists(dataset_info_path):
            dataset_info = {
                "description": "Dataset d'enregistrements audio pour fine-tuning de modèles de reconnaissance vocale",
                "citation": "",
                "homepage": "",
                "license": "",
                "features": {
                    "path": {"dtype": "string", "id": None, "_type": "Value"},
                    "audio": {
                        "dtype": "dict",
                        "id": None,
                        "_type": "Audio",
                        "sampling_rate": 16000
                    },
                    "sentence": {"dtype": "string", "id": None, "_type": "Value"},
                    "transcription": {"dtype": "string", "id": None, "_type": "Value"},
                    "engine": {"dtype": "string", "id": None, "_type": "Value"},
                    "duration": {"dtype": "float32", "id": None, "_type": "Value"},
                    "timestamp": {"dtype": "int64", "id": None, "_type": "Value"},
                    "split": {"dtype": "string", "id": None, "_type": "Value"}
                },
                "splits": {
                    "train": {"name": "train", "num_bytes": 0, "num_examples": 0},
                    "validation": {"name": "validation", "num_bytes": 0, "num_examples": 0},
                    "test": {"name": "test", "num_bytes": 0, "num_examples": 0}
                }
            }
            with open(dataset_info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement pour fine tuning: {e}")
        return False

def normalize_text(text_input):
    # Vérifier si c'est une liste ou un tuple
    if isinstance(text_input, (list, tuple)):
        # Prendre le premier élément s'il existe
        if text_input and len(text_input) > 0:
            text_input = text_input[0]
        else:
            text_input = ""

    # S'assurer que c'est bien une chaîne de caractères
    if not isinstance(text_input, str):
        text_input = str(text_input)

    return text_input

def generate_huggingface_dataset():
    """
    Génère un dataset compatible avec Hugging Face à partir des enregistrements existants

    Returns:
        bool: True si le dataset a été généré avec succès
    """
    try:
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            print(f"Dossier records non trouvé: {records_dir}")
            return False

        # Vérifier si metadata.jsonl existe déjà
        metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")
        if os.path.exists(metadata_jsonl_path):
            print(f"Le fichier metadata.jsonl existe déjà: {metadata_jsonl_path}")
            # En option, on pourrait régénérer le fichier

        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]
        total_processed = 0

        # Ouvrir le fichier metadata.jsonl en mode écriture (écrase le contenu existant)
        with open(metadata_jsonl_path, 'w', encoding='utf-8') as metadata_file:
            # Pour chaque moteur, parcourir les fichiers JSON
            for engine in engines:
                engine_dir = os.path.join(records_dir, engine)

                # Parcourir récursivement tous les fichiers JSON
                json_files = []
                for root, dirs, files in os.walk(engine_dir):
                    json_files.extend([os.path.join(root, f) for f in files if f.endswith('.json')])

                for json_path in json_files:
                    try:
                        # Charger les métadonnées existantes
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # Déterminer le chemin du fichier audio
                        audio_file = metadata.get("audio_file")
                        audio_path = os.path.join(os.path.dirname(json_path), audio_file)

                        # Vérifier si le fichier audio existe
                        if not os.path.exists(audio_path):
                            print(f"Fichier audio non trouvé: {audio_path}")
                            continue

                        # Déterminer le split (dossier parent immédiat ou "train" par défaut)
                        parent_dir = os.path.basename(os.path.dirname(json_path))
                        split = parent_dir if parent_dir in ["train", "validation", "test"] else "train"

                        # Chemin relatif pour le dataset
                        rel_path = os.path.relpath(audio_path, records_dir)

                        # Créer l'entrée metadata au format Hugging Face
                        metadata_entry = {
                            "path": rel_path,
                            "audio": {
                                "path": rel_path,
                                "array": None,  # Non stocké dans le JSON
                                "sampling_rate": metadata.get("sample_rate", 16000)
                            },
                            "sentence": metadata.get("text", ""),
                            "transcription": metadata.get("text", ""),
                            "engine": metadata.get("engine", engine),
                            "duration": metadata.get("duration", 0),
                            "timestamp": metadata.get("timestamp", 0),
                            "split": split
                        }

                        # Écrire dans le fichier metadata.jsonl
                        metadata_file.write(json.dumps(metadata_entry, ensure_ascii=False) + "\n")
                        total_processed += 1
                    except Exception as e:
                        print(f"Erreur lors du traitement du fichier {json_path}: {e}")
                        continue

        # Créer ou mettre à jour le fichier dataset_info.json
        dataset_info_path = os.path.join(records_dir, "dataset_info.json")
        dataset_info = {
            "description": "Dataset d'enregistrements audio pour fine-tuning de modèles de reconnaissance vocale",
            "citation": "",
            "homepage": "",
            "license": "",
            "features": {
                "path": {"dtype": "string", "id": None, "_type": "Value"},
                "audio": {
                    "dtype": "dict",
                    "id": None,
                    "_type": "Audio",
                    "sampling_rate": 16000
                },
                "sentence": {"dtype": "string", "id": None, "_type": "Value"},
                "transcription": {"dtype": "string", "id": None, "_type": "Value"},
                "engine": {"dtype": "string", "id": None, "_type": "Value"},
                "duration": {"dtype": "float32", "id": None, "_type": "Value"},
                "timestamp": {"dtype": "int64", "id": None, "_type": "Value"},
                "split": {"dtype": "string", "id": None, "_type": "Value"}
            },
            "splits": {
                "train": {"name": "train", "num_bytes": 0, "num_examples": 0},
                "validation": {"name": "validation", "num_bytes": 0, "num_examples": 0},
                "test": {"name": "test", "num_bytes": 0, "num_examples": 0}
            }
        }

        with open(dataset_info_path, 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, ensure_ascii=False, indent=2)

        print(f"Dataset Hugging Face généré avec succès: {total_processed} échantillons")
        return True
    except Exception as e:
        print(f"Erreur lors de la génération du dataset Hugging Face: {e}")
        return False

def split_dataset(train_ratio=0.8, validation_ratio=0.1, test_ratio=0.1):
    """
    Répartit les échantillons existants entre les splits train/validation/test

    Args:
        train_ratio: Proportion d'échantillons pour l'entraînement (0.8 par défaut)
        validation_ratio: Proportion d'échantillons pour la validation (0.1 par défaut)
        test_ratio: Proportion d'échantillons pour le test (0.1 par défaut)

    Returns:
        bool: True si la répartition a été effectuée avec succès
    """
    try:
        # Vérifier que la somme des ratios est égale à 1
        if abs(train_ratio + validation_ratio + test_ratio - 1.0) > 0.001:
            print(f"La somme des ratios doit être égale à 1, reçu: {train_ratio + validation_ratio + test_ratio}")
            return False

        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            print(f"Dossier records non trouvé: {records_dir}")
            return False

        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]

        for engine in engines:
            engine_dir = os.path.join(records_dir, engine)

            # Créer les dossiers de splits s'ils n'existent pas
            train_dir = os.path.join(engine_dir, "train")
            validation_dir = os.path.join(engine_dir, "validation")
            test_dir = os.path.join(engine_dir, "test")

            os.makedirs(train_dir, exist_ok=True)
            os.makedirs(validation_dir, exist_ok=True)
            os.makedirs(test_dir, exist_ok=True)

            # Récupérer tous les ensembles d'échantillons (WAV, TXT, JSON)
            sample_sets = []

            for root, dirs, files in os.walk(engine_dir):
                # Ignorer les dossiers train/validation/test eux-mêmes
                if os.path.basename(root) in ["train", "validation", "test"]:
                    continue

                # Récupérer tous les fichiers JSON à la racine de engine_dir
                json_files = [f for f in files if f.endswith('.json')]

                for json_file in json_files:
                    json_path = os.path.join(root, json_file)
                    base_name = json_file[:-5]  # Enlever l'extension .json

                    # Construire les chemins pour les fichiers WAV et TXT
                    wav_path = os.path.join(root, f"{base_name}.wav")
                    txt_path = os.path.join(root, f"{base_name}.txt")

                    # Vérifier que les fichiers existent
                    if os.path.exists(wav_path) and os.path.exists(txt_path):
                        sample_sets.append((json_path, wav_path, txt_path))

            # Mélanger les échantillons pour une répartition aléatoire
            import random
            random.shuffle(sample_sets)

            # Calculer le nombre d'échantillons pour chaque split
            total_samples = len(sample_sets)
            train_count = int(total_samples * train_ratio)
            validation_count = int(total_samples * validation_ratio)
            # Le reste va dans test

            train_samples = sample_sets[:train_count]
            validation_samples = sample_sets[train_count:train_count + validation_count]
            test_samples = sample_sets[train_count + validation_count:]

            # Déplacer les échantillons dans les dossiers appropriés
            def move_samples(samples, target_dir):
                for json_path, wav_path, txt_path in samples:
                    # Extraire les noms de fichiers
                    json_file = os.path.basename(json_path)
                    wav_file = os.path.basename(wav_path)
                    txt_file = os.path.basename(txt_path)

                    # Définir les chemins cibles
                    target_json = os.path.join(target_dir, json_file)
                    target_wav = os.path.join(target_dir, wav_file)
                    target_txt = os.path.join(target_dir, txt_file)

                    # Déplacer les fichiers
                    import shutil
                    shutil.copy2(json_path, target_json)
                    shutil.copy2(wav_path, target_wav)
                    shutil.copy2(txt_path, target_txt)

                    # Mettre à jour le fichier JSON pour refléter le nouveau split
                    try:
                        with open(target_json, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # Mettre à jour le split
                        metadata["split"] = os.path.basename(target_dir)

                        with open(target_json, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"Erreur lors de la mise à jour du fichier JSON {target_json}: {e}")

            # Déplacer les échantillons
            move_samples(train_samples, train_dir)
            move_samples(validation_samples, validation_dir)
            move_samples(test_samples, test_dir)

            print(f"Split effectué pour {engine}: {len(train_samples)} train, {len(validation_samples)} validation, {len(test_samples)} test")

        # Régénérer le dataset Hugging Face
        generate_huggingface_dataset()

        return True
    except Exception as e:
        print(f"Erreur lors de la répartition du dataset: {e}")
        return False
