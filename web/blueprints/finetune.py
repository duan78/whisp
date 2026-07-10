"""Blueprint for fine-tuning dataset management routes.

Extracted verbatim from ``web_interface.py``. Only the decorators changed
(``@app.*`` -> ``@bp.*``); route bodies are unchanged.
"""

import os
import json

from flask import Blueprint, request, jsonify

bp = Blueprint('finetune', __name__)

# Routes API pour la gestion des données de fine-tuning

@bp.get('/api/finetune/samples')
def get_finetune_samples():
    """Récupère tous les échantillons pour le fine-tuning"""
    try:
        records_dir = os.path.join(os.getcwd(), "records")
        if not os.path.exists(records_dir):
            return jsonify({"success": False, "error": "Dossier records non trouvé", "samples": []})

        # Récupérer la liste des échantillons
        samples = []

        # Parcourir tous les moteurs
        engines = [d for d in os.listdir(records_dir) if os.path.isdir(os.path.join(records_dir, d))]

        for engine in engines:
            engine_dir = os.path.join(records_dir, engine)

            # Parcourir récursivement tous les fichiers JSON
            for root, dirs, files in os.walk(engine_dir):
                json_files = [f for f in files if f.endswith('.json')]

                for json_file in json_files:
                    json_path = os.path.join(root, json_file)

                    try:
                        # Charger les métadonnées depuis le fichier JSON
                        with open(json_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # Obtenir le chemin du fichier audio
                        audio_file = metadata.get("audio_file")
                        if not audio_file:
                            continue

                        audio_path = os.path.join(os.path.dirname(json_path), audio_file)

                        # Obtenir le chemin du fichier texte (transcription)
                        base_name = os.path.splitext(audio_file)[0]
                        text_file = f"{base_name}.txt"
                        text_path = os.path.join(os.path.dirname(json_path), text_file)

                        # Vérifier que les fichiers existent
                        if not os.path.exists(audio_path) or not os.path.exists(text_path):
                            continue

                        # Lire le contenu du fichier texte
                        with open(text_path, 'r', encoding='utf-8') as f:
                            transcription = f.read().strip()

                        # Déterminer le split (train, validation, test)
                        split_dir = os.path.basename(os.path.dirname(json_path))
                        split = split_dir if split_dir in ["train", "validation", "test"] else "unknown"

                        # Déterminer les chemins relatifs pour le frontend
                        rel_audio_path = os.path.relpath(audio_path, os.getcwd())
                        rel_json_path = os.path.relpath(json_path, os.getcwd())
                        rel_text_path = os.path.relpath(text_path, os.getcwd())

                        # Ajouter l'échantillon à la liste
                        sample = {
                            "id": f"{engine}_{os.path.basename(audio_path)}",
                            "engine": engine,
                            "split": split,
                            "transcription": transcription,
                            "audio_path": rel_audio_path.replace("\\", "/"),
                            "json_path": rel_json_path.replace("\\", "/"),
                            "text_path": rel_text_path.replace("\\", "/"),
                            "timestamp": metadata.get("timestamp", 0),
                            "duration": metadata.get("duration", 0),
                            "metadata": metadata
                        }

                        samples.append(sample)
                    except Exception as e:
                        print(f"Erreur lors du traitement du fichier {json_path}: {e}")
                        continue

        # Tri des échantillons par timestamp (du plus récent au plus ancien)
        samples.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        return jsonify({"success": True, "samples": samples})
    except Exception as e:
        print(f"Erreur lors de la récupération des échantillons: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "samples": []})

@bp.post('/api/finetune/update_transcription')
def update_transcription():
    """Met à jour la transcription d'un échantillon"""
    try:
        data = request.get_json()
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        new_transcription = data.get('transcription')

        if not text_path or not new_transcription or not json_path:
            return jsonify({"success": False, "error": "Paramètres manquants"})

        # Convertir le chemin relatif en chemin absolu
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)

        # Vérifier que les fichiers existent
        if not os.path.exists(abs_text_path) or not os.path.exists(abs_json_path):
            return jsonify({"success": False, "error": "Fichier non trouvé"})

        # Mettre à jour le fichier texte
        with open(abs_text_path, 'w', encoding='utf-8') as f:
            f.write(new_transcription)

        # Mettre à jour les métadonnées dans le fichier JSON
        with open(abs_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Mettre à jour le champ text dans les métadonnées
        metadata['text'] = new_transcription

        with open(abs_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            records_dir = os.path.join(os.getcwd(), "records")
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")

            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Chemin relatif pour l'identification dans le fichier JSONL
                rel_path = os.path.relpath(abs_text_path, records_dir).replace(".txt", os.path.splitext(metadata['audio_file'])[1])

                # Mettre à jour la ligne correspondante
                updated = False
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'].endswith(rel_path.replace(".txt", "")):
                            # Mettre à jour la transcription
                            entry['sentence'] = new_transcription
                            entry['transcription'] = new_transcription
                            # Réécrire la ligne mise à jour
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            updated = True
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)

                if updated:
                    print(f"metadata.jsonl mis à jour pour {rel_path}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été mis à jour

        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue

        return jsonify({"success": True, "message": "Transcription mise à jour avec succès"})
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la transcription: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@bp.post('/api/finetune/delete_sample')
def delete_sample():
    """Supprime un échantillon de données"""
    try:
        data = request.get_json()
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        audio_path = data.get('audio_path')

        if not text_path or not json_path or not audio_path:
            return jsonify({"success": False, "error": "Paramètres manquants"})

        # Convertir les chemins relatifs en chemins absolus
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)
        abs_audio_path = os.path.join(os.getcwd(), audio_path)

        # Vérifier que les fichiers existent
        files_to_delete = []
        for file_path in [abs_text_path, abs_json_path, abs_audio_path]:
            if os.path.exists(file_path):
                files_to_delete.append(file_path)

        if not files_to_delete:
            return jsonify({"success": False, "error": "Aucun fichier à supprimer"})

        # Supprimer les fichiers
        for file_path in files_to_delete:
            os.remove(file_path)
            print(f"Fichier supprimé: {file_path}")

        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            records_dir = os.path.join(os.getcwd(), "records")
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")

            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Chemin relatif pour l'identification dans le fichier JSONL
                rel_path = os.path.relpath(abs_audio_path, records_dir)

                # Filtrer la ligne correspondante
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'] == rel_path:
                            # Ignorer cette ligne
                            print(f"Entrée supprimée de metadata.jsonl: {rel_path}")
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été supprimés

        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue

        return jsonify({
            "success": True,
            "message": f"{len(files_to_delete)} fichiers supprimés avec succès",
            "deleted_files": files_to_delete
        })
    except Exception as e:
        print(f"Erreur lors de la suppression de l'échantillon: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@bp.post('/api/finetune/change_split')
def change_split():
    """Change le split (train/validation/test) d'un échantillon"""
    try:
        data = request.get_json()
        text_path = data.get('text_path')
        json_path = data.get('json_path')
        audio_path = data.get('audio_path')
        new_split = data.get('split')

        if not text_path or not json_path or not audio_path or not new_split:
            return jsonify({"success": False, "error": "Paramètres manquants"})

        if new_split not in ["train", "validation", "test"]:
            return jsonify({"success": False, "error": "Split invalide. Doit être 'train', 'validation' ou 'test'"})

        # Convertir les chemins relatifs en chemins absolus
        abs_text_path = os.path.join(os.getcwd(), text_path)
        abs_json_path = os.path.join(os.getcwd(), json_path)
        abs_audio_path = os.path.join(os.getcwd(), audio_path)

        # Vérifier que les fichiers existent
        for file_path in [abs_text_path, abs_json_path, abs_audio_path]:
            if not os.path.exists(file_path):
                return jsonify({"success": False, "error": f"Fichier non trouvé: {file_path}"})

        # Déterminer le moteur à partir du chemin
        engine = None
        try:
            parts = abs_audio_path.split(os.sep)
            records_index = parts.index("records")
            if records_index < len(parts) - 1:
                engine = parts[records_index + 1]
        except (ValueError, IndexError):
            return jsonify({"success": False, "error": "Impossible de déterminer le moteur à partir du chemin"})

        if not engine:
            return jsonify({"success": False, "error": "Moteur non trouvé dans le chemin"})

        # Construire les nouveaux chemins dans le dossier du split souhaité
        records_dir = os.path.join(os.getcwd(), "records")
        engine_dir = os.path.join(records_dir, engine)
        split_dir = os.path.join(engine_dir, new_split)

        # Créer le dossier du split s'il n'existe pas
        os.makedirs(split_dir, exist_ok=True)

        # Déterminer les nouveaux chemins
        new_audio_path = os.path.join(split_dir, os.path.basename(abs_audio_path))
        new_text_path = os.path.join(split_dir, os.path.basename(abs_text_path))
        new_json_path = os.path.join(split_dir, os.path.basename(abs_json_path))

        # Vérifier si les fichiers existent déjà dans le dossier cible
        for file_path in [new_audio_path, new_text_path, new_json_path]:
            if os.path.exists(file_path):
                return jsonify({
                    "success": False,
                    "error": f"Un fichier portant le même nom existe déjà dans le dossier {new_split}"
                })

        # Déplacer les fichiers
        import shutil
        shutil.move(abs_audio_path, new_audio_path)
        shutil.move(abs_text_path, new_text_path)
        shutil.move(abs_json_path, new_json_path)

        # Mettre à jour le champ split dans le fichier JSON
        with open(new_json_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Mettre à jour le champ split dans les métadonnées
        metadata['split'] = new_split

        with open(new_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Mettre à jour le fichier metadata.jsonl global si présent
        try:
            metadata_jsonl_path = os.path.join(records_dir, "metadata.jsonl")

            if os.path.exists(metadata_jsonl_path):
                # Lire toutes les lignes du fichier
                with open(metadata_jsonl_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Chemin relatif pour l'identification dans le fichier JSONL
                old_rel_path = os.path.relpath(abs_audio_path, records_dir)
                new_rel_path = os.path.relpath(new_audio_path, records_dir)

                # Mettre à jour la ligne correspondante
                updated = False
                with open(metadata_jsonl_path, 'w', encoding='utf-8') as f:
                    for line in lines:
                        entry = json.loads(line)
                        # Vérifier si c'est l'entrée que nous cherchons
                        if 'path' in entry and entry['path'] == old_rel_path:
                            # Mettre à jour le chemin et le split
                            entry['path'] = new_rel_path
                            entry['audio']['path'] = new_rel_path
                            entry['split'] = new_split
                            # Réécrire la ligne mise à jour
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                            updated = True
                        else:
                            # Réécire la ligne inchangée
                            f.write(line)

                if updated:
                    print(f"metadata.jsonl mis à jour pour {old_rel_path} -> {new_rel_path}")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier metadata.jsonl: {e}")
            # Ne pas échouer si cette mise à jour échoue, car les fichiers principaux ont été déplacés

        # Régénérer le dataset Hugging Face
        try:
            from speech_recognition_module import generate_huggingface_dataset
            generate_huggingface_dataset()
        except Exception as e:
            print(f"Erreur lors de la régénération du dataset Hugging Face: {e}")
            # Ne pas échouer si cette régénération échoue

        # Retourner les nouveaux chemins relatifs
        rel_new_audio_path = os.path.relpath(new_audio_path, os.getcwd()).replace("\\", "/")
        rel_new_text_path = os.path.relpath(new_text_path, os.getcwd()).replace("\\", "/")
        rel_new_json_path = os.path.relpath(new_json_path, os.getcwd()).replace("\\", "/")

        return jsonify({
            "success": True,
            "message": f"Échantillon déplacé vers le split {new_split}",
            "new_paths": {
                "audio_path": rel_new_audio_path,
                "text_path": rel_new_text_path,
                "json_path": rel_new_json_path
            }
        })
    except Exception as e:
        print(f"Erreur lors du changement de split: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@bp.post('/api/finetune/regenerate_dataset')
def regenerate_dataset():
    """Régénère le dataset Hugging Face à partir des échantillons existants"""
    try:
        from speech_recognition_module import generate_huggingface_dataset

        success = generate_huggingface_dataset()

        if success:
            return jsonify({
                "success": True,
                "message": "Dataset régénéré avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la régénération du dataset"
            })
    except Exception as e:
        print(f"Erreur lors de la régénération du dataset: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})
