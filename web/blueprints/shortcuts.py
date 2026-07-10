"""Blueprint for custom voice shortcut routes.

Extracted verbatim from ``web_interface.py``. Only the decorators changed
(``@app.*`` -> ``@bp.*``); route bodies are unchanged.
"""

import traceback

from flask import Blueprint, request, jsonify
from error_handler import ErrorCategory, ErrorSeverity
from web.state import add_log, get_error_handler, get_error_types

bp = Blueprint('shortcuts', __name__)

@bp.get('/get_custom_shortcuts')
def get_custom_shortcuts_route():
    """Récupère les raccourcis vocaux personnalisés"""
    try:
        # Importer le module de base de données
        from database_manager import get_custom_shortcuts

        # Récupérer un type d'action spécifique si demandé
        action_type = request.args.get('action_type', None)

        # Récupérer les raccourcis
        shortcuts = get_custom_shortcuts(action_type=action_type)

        return jsonify({
            "success": True,
            "shortcuts": shortcuts
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des raccourcis personnalisés: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_custom_shortcuts"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/add_custom_shortcut')
def add_custom_shortcut_route():
    """Ajoute un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        from database_manager import save_custom_shortcut

        data = request.get_json()
        name = data.get('name')
        voice_command = data.get('voice_command')
        action_type = data.get('action_type')
        action_data = data.get('action_data')

        print(f"Tentative d'ajout de raccourci personnalisé: nom='{name}', commande='{voice_command}'")

        if not name or not voice_command or not action_type or not action_data:
            return jsonify({"success": False, "error": "Tous les champs sont requis"})

        # Valider le type d'action contre une allowlist (anti-RCE)
        from shortcuts_database import ALLOWED_ACTION_TYPES
        if action_type not in ALLOWED_ACTION_TYPES:
            return jsonify({
                "success": False,
                "error": f"Type d'action non autorisé: {action_type}. "
                         f"Types valides: {', '.join(sorted(ALLOWED_ACTION_TYPES))}"
            })

        # Sauvegarder le raccourci
        shortcut_id = save_custom_shortcut(name, voice_command, action_type, action_data)

        if shortcut_id:
            add_log(f"Raccourci personnalisé '{name}' ajouté avec la commande '{voice_command}'", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id,
                "name": name,
                "voice_command": voice_command
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de l'ajout du raccourci. La commande vocale '{voice_command}' existe peut-être déjà."
            })
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/add_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/update_custom_shortcut')
def update_custom_shortcut_route():
    """Met à jour un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        from database_manager import update_custom_shortcut

        data = request.get_json()
        shortcut_id = data.get('id')
        name = data.get('name')
        voice_command = data.get('voice_command')
        action_type = data.get('action_type')
        action_data = data.get('action_data')

        if not shortcut_id:
            return jsonify({"success": False, "error": "ID du raccourci non spécifié"})

        # Valider le type d'action contre une allowlist (anti-RCE)
        if action_type is not None:
            from shortcuts_database import ALLOWED_ACTION_TYPES
            if action_type not in ALLOWED_ACTION_TYPES:
                return jsonify({
                    "success": False,
                    "error": f"Type d'action non autorisé: {action_type}. "
                             f"Types valides: {', '.join(sorted(ALLOWED_ACTION_TYPES))}"
                })

        # Mettre à jour le raccourci
        success = update_custom_shortcut(
            shortcut_id,
            name=name,
            voice_command=voice_command,
            action_type=action_type,
            action_data=action_data
        )

        if success:
            add_log(f"Raccourci personnalisé mis à jour: ID {shortcut_id}", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de la mise à jour du raccourci. La commande vocale existe peut-être déjà."
            })
    except Exception as e:
        print(f"Erreur lors de la mise à jour d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/update_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/delete_custom_shortcut')
def delete_custom_shortcut_route():
    """Supprime un raccourci vocal personnalisé"""
    try:
        # Importer le module de base de données
        from database_manager import delete_custom_shortcut

        data = request.get_json()
        shortcut_id = data.get('id')

        if not shortcut_id:
            return jsonify({"success": False, "error": "ID du raccourci non spécifié"})

        # Supprimer le raccourci
        success = delete_custom_shortcut(shortcut_id)

        if success:
            add_log(f"Raccourci personnalisé supprimé: ID {shortcut_id}", "info")
            return jsonify({
                "success": True,
                "id": shortcut_id
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de la suppression du raccourci. ID {shortcut_id} non trouvé."
            })
    except Exception as e:
        print(f"Erreur lors de la suppression d'un raccourci personnalisé: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/delete_custom_shortcut"}
        )
        return jsonify({"success": False, "error": str(e)})
