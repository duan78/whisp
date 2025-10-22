"""
API endpoints pour la gestion optimisée des données de fine-tuning
"""

from flask import Blueprint, request, jsonify
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict
import time

# Créer le blueprint
finetune_api = Blueprint('finetune_api', __name__)

# Chemin de base pour les enregistrements
RECORDS_PATH = Path(__file__).parent / 'records'

def get_sample_id(sample_path):
    """Génère un ID unique pour un échantillon basé sur son chemin"""
    return str(Path(sample_path).stem)

@finetune_api.route('/api/finetune/batch_update', methods=['POST'])
def batch_update_transcriptions():
    """Met à jour plusieurs transcriptions en une seule requête"""
    try:
        data = request.json
        updates = data.get('updates', [])
        
        if not updates:
            return jsonify({"success": False, "error": "Aucune mise à jour fournie"})
        
        success_count = 0
        errors = []
        
        for update in updates:
            try:
                text_path = update.get('text_path')
                json_path = update.get('json_path')
                transcription = update.get('transcription', '').strip()
                
                if not text_path or not json_path:
                    errors.append(f"Chemins manquants pour une mise à jour")
                    continue
                
                # Mettre à jour le fichier texte
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(transcription)
                
                # Mettre à jour le fichier JSON
                with open(json_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata['transcription'] = transcription
                metadata['last_modified'] = time.time()
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Erreur pour {text_path}: {str(e)}")
        
        # Régénérer le dataset après les mises à jour
        if success_count > 0:
            regenerate_dataset()
        
        return jsonify({
            "success": True,
            "updated": success_count,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@finetune_api.route('/api/finetune/batch_change_split', methods=['POST'])
def batch_change_split():
    """Change le split de plusieurs échantillons en une seule requête"""
    try:
        data = request.json
        updates = data.get('updates', [])
        
        if not updates:
            return jsonify({"success": False, "error": "Aucune mise à jour fournie"})
        
        success_count = 0
        new_paths = []
        errors = []
        
        for update in updates:
            try:
                old_audio = update.get('audio_path')
                old_text = update.get('text_path')
                old_json = update.get('json_path')
                new_split = update.get('split')
                
                if not all([old_audio, old_text, old_json, new_split]):
                    errors.append("Données incomplètes pour un échantillon")
                    continue
                
                # Déterminer les nouveaux chemins
                old_dir = Path(old_audio).parent
                engine = old_dir.parent.name
                new_dir = RECORDS_PATH / engine / new_split
                new_dir.mkdir(parents=True, exist_ok=True)
                
                # Déplacer les fichiers
                for old_path in [old_audio, old_text, old_json]:
                    old_file = Path(old_path)
                    new_file = new_dir / old_file.name
                    
                    if old_file.exists():
                        shutil.move(str(old_file), str(new_file))
                
                success_count += 1
                
                # Ajouter les nouveaux chemins pour la réponse
                base_name = Path(old_audio).stem
                new_paths.append({
                    'id': get_sample_id(old_audio),
                    'audio_path': str(new_dir / f"{base_name}.wav"),
                    'text_path': str(new_dir / f"{base_name}.txt"),
                    'json_path': str(new_dir / f"{base_name}.json")
                })
                
            except Exception as e:
                errors.append(f"Erreur pour un échantillon: {str(e)}")
        
        # Régénérer le dataset après les changements
        if success_count > 0:
            regenerate_dataset()
        
        return jsonify({
            "success": True,
            "changed": success_count,
            "new_paths": new_paths,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@finetune_api.route('/api/finetune/batch_delete', methods=['POST'])
def batch_delete_samples():
    """Supprime plusieurs échantillons en une seule requête"""
    try:
        data = request.json
        samples = data.get('samples', [])
        
        if not samples:
            return jsonify({"success": False, "error": "Aucun échantillon à supprimer"})
        
        success_count = 0
        errors = []
        
        for sample in samples:
            try:
                audio_path = sample.get('audio_path')
                text_path = sample.get('text_path')
                json_path = sample.get('json_path')
                
                # Supprimer les fichiers
                for path in [audio_path, text_path, json_path]:
                    if path and os.path.exists(path):
                        os.remove(path)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Erreur lors de la suppression: {str(e)}")
        
        # Régénérer le dataset après les suppressions
        if success_count > 0:
            regenerate_dataset()
        
        return jsonify({
            "success": True,
            "deleted": success_count,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@finetune_api.route('/api/finetune/export_dataset', methods=['POST'])
def export_dataset():
    """Exporte le dataset dans différents formats"""
    try:
        data = request.json
        format_type = data.get('format', 'huggingface')  # huggingface, csv, json
        include_audio = data.get('include_audio', False)
        
        # TODO: Implémenter l'export dans différents formats
        # Pour l'instant, on retourne juste le chemin du metadata.jsonl
        
        metadata_path = RECORDS_PATH / 'metadata.jsonl'
        
        if not metadata_path.exists():
            regenerate_dataset()
        
        return jsonify({
            "success": True,
            "format": format_type,
            "path": str(metadata_path),
            "message": "Export préparé avec succès"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def regenerate_dataset():
    """Régénère le fichier metadata.jsonl à partir des échantillons"""
    try:
        # Importer la fonction depuis speech_recognition_module
        from speech_recognition_module import generate_huggingface_dataset
        generate_huggingface_dataset()
        return True
    except Exception as e:
        print(f"Erreur lors de la régénération du dataset: {e}")
        return False