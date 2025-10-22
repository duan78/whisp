"""
Module de validation des entrées utilisateur
"""

import re
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from flask import request, jsonify

class ValidationError(Exception):
    """Exception pour les erreurs de validation"""
    pass

class InputValidator:
    """Classe pour valider les entrées utilisateur"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 500) -> str:
        """Nettoie et valide une chaîne de caractères"""
        if not isinstance(value, str):
            raise ValidationError("La valeur doit être une chaîne de caractères")
        
        # Supprimer les espaces au début et à la fin
        value = value.strip()
        
        # Limiter la longueur
        if len(value) > max_length:
            raise ValidationError(f"La chaîne ne doit pas dépasser {max_length} caractères")
        
        # Supprimer les caractères de contrôle dangereux
        value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        return value
    
    @staticmethod
    def validate_api_key(key: str) -> str:
        """Valide une clé API"""
        # Nettoyer la chaîne
        key = InputValidator.sanitize_string(key, max_length=200)
        
        # Vérifier le format (alphanumérique avec tirets et underscores)
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', key):
            raise ValidationError("Format de clé API invalide")
        
        # Vérifier la longueur minimale
        if len(key) < 10:
            raise ValidationError("La clé API est trop courte")
        
        return key
    
    @staticmethod
    def validate_command(command: str) -> str:
        """Valide une commande vocale"""
        command = InputValidator.sanitize_string(command, max_length=1000)
        
        # Supprimer les commandes potentiellement dangereuses
        dangerous_patterns = [
            r';\s*rm\s+-rf',
            r';\s*del\s+/s',
            r'>\s*/dev/null',
            r'&&\s*curl',
            r'wget\s+.*\|',
            r'\$\(',
            r'`.*`',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValidationError("Commande potentiellement dangereuse détectée")
        
        return command
    
    @staticmethod
    def validate_file_path(path: str) -> str:
        """Valide un chemin de fichier"""
        path = InputValidator.sanitize_string(path, max_length=500)
        
        # Empêcher les traversées de répertoire
        if '..' in path or path.startswith('/etc') or path.startswith('/sys'):
            raise ValidationError("Chemin de fichier non autorisé")
        
        # Vérifier les caractères autorisés
        if not re.match(r'^[a-zA-Z0-9_\-\./\\: ]+$', path):
            raise ValidationError("Caractères non autorisés dans le chemin")
        
        return path
    
    @staticmethod
    def validate_stt_engine(engine: str) -> str:
        """Valide le choix du moteur STT"""
        valid_engines = ["speechrecognition", "nemo", "whisper", "vosk", "whisper_ct2"]
        
        engine = InputValidator.sanitize_string(engine, max_length=50).lower()
        
        if engine not in valid_engines:
            raise ValidationError(f"Moteur STT invalide. Choix possibles: {', '.join(valid_engines)}")
        
        return engine
    
    @staticmethod
    def validate_tts_engine(engine: str) -> str:
        """Valide le choix du moteur TTS"""
        valid_engines = ["pyttsx3", "gtts", "coqui", "piper"]
        
        engine = InputValidator.sanitize_string(engine, max_length=50).lower()
        
        if engine not in valid_engines:
            raise ValidationError(f"Moteur TTS invalide. Choix possibles: {', '.join(valid_engines)}")
        
        return engine
    
    @staticmethod
    def validate_alias(alias_data: Dict[str, str]) -> Dict[str, str]:
        """Valide les données d'un alias"""
        if not isinstance(alias_data, dict):
            raise ValidationError("Les données d'alias doivent être un dictionnaire")
        
        required_fields = ['alias', 'command']
        for field in required_fields:
            if field not in alias_data:
                raise ValidationError(f"Champ requis manquant: {field}")
        
        # Valider l'alias
        alias = InputValidator.sanitize_string(alias_data['alias'], max_length=100)
        if not re.match(r'^[a-zA-Z0-9_\- ]+$', alias):
            raise ValidationError("L'alias contient des caractères non autorisés")
        
        # Valider la commande
        command = InputValidator.validate_command(alias_data['command'])
        
        return {
            'alias': alias,
            'command': command,
            'description': InputValidator.sanitize_string(
                alias_data.get('description', ''), 
                max_length=500
            )
        }
    
    @staticmethod
    def validate_json_input(schema: Dict[str, Any]) -> callable:
        """Décorateur pour valider les entrées JSON selon un schéma"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not request.is_json:
                    return jsonify({'error': 'Content-Type doit être application/json'}), 400
                
                data = request.get_json()
                
                # Valider selon le schéma
                validated_data = {}
                for field, validator in schema.items():
                    if field not in data and validator.get('required', False):
                        return jsonify({'error': f'Champ requis manquant: {field}'}), 400
                    
                    if field in data:
                        try:
                            # Appliquer le validateur
                            if 'validator' in validator:
                                validated_data[field] = validator['validator'](data[field])
                            else:
                                validated_data[field] = data[field]
                        except ValidationError as e:
                            return jsonify({'error': f'Erreur de validation pour {field}: {str(e)}'}), 400
                
                # Passer les données validées à la fonction
                request.validated_data = validated_data
                return func(*args, **kwargs)
            
            return wrapper
        return decorator

# Validateurs pour les routes Flask
def validate_api_key_request():
    """Valide une requête de mise à jour de clé API"""
    return InputValidator.validate_json_input({
        'type': {
            'required': True,
            'validator': lambda x: InputValidator.sanitize_string(x, 20)
        },
        'key': {
            'required': True,
            'validator': InputValidator.validate_api_key
        }
    })

def validate_command_request():
    """Valide une requête de commande"""
    return InputValidator.validate_json_input({
        'command': {
            'required': True,
            'validator': InputValidator.validate_command
        }
    })

def validate_config_request():
    """Valide une requête de configuration"""
    return InputValidator.validate_json_input({
        'stt_engine': {
            'required': False,
            'validator': InputValidator.validate_stt_engine
        },
        'tts_engine': {
            'required': False,
            'validator': InputValidator.validate_tts_engine
        }
    })