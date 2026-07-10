"""Blueprint for command alias routes.

Extracted verbatim from ``web_interface.py``. Only the decorators changed
(``@app.*`` -> ``@bp.*``); route bodies are unchanged.
"""

import traceback

from flask import Blueprint, request, jsonify
from web.state import add_log, get_error_handler, get_error_types

bp = Blueprint('aliases', __name__)

@bp.get('/get_command_aliases')
def get_command_aliases_route():
    """Récupère les alias de commandes"""
    try:
        # Importer le module des alias de commandes
        from command_aliases import command_aliases

        # Récupérer une commande spécifique si demandée
        command = request.args.get('command', None)
        if command:
            aliases = command_aliases.get_aliases_for_command(command)
            return jsonify({
                "success": True,
                "command": command,
                "aliases": aliases
            })

        # Sinon, récupérer tous les alias
        all_aliases = command_aliases.aliases
        print(f"Alias récupérés: {len(all_aliases)} commandes")

        # Convertir le dictionnaire en format plus adapté pour le frontend
        formatted_aliases = {}
        for command, alias_list in all_aliases.items():
            formatted_aliases[command] = sorted(alias_list)

        return jsonify({
            "success": True,
            "aliases": formatted_aliases
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des alias: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/get_command_aliases"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/add_command_alias')
def add_command_alias_route():
    """Ajoute un alias de commande"""
    try:
        from command_aliases import command_aliases

        data = request.get_json()
        command = data.get('command')
        alias = data.get('alias')

        print(f"Tentative d'ajout d'alias: commande='{command}', alias='{alias}'")

        if not command or not alias:
            return jsonify({"success": False, "error": "Commande ou alias non spécifié"})

        # Nettoyer les entrées
        command = command.strip()
        alias = alias.strip()

        # Vérifier si l'alias existe déjà
        if alias in command_aliases.command_lookup:
            existing_command = command_aliases.command_lookup[alias]
            if existing_command != command:
                return jsonify({
                    "success": False,
                    "error": f"L'alias '{alias}' existe déjà pour la commande '{existing_command}'"
                })
            else:
                # L'alias existe déjà pour cette commande, on considère que c'est un succès
                return jsonify({
                    "success": True,
                    "command": command,
                    "alias": alias,
                    "message": "Cet alias existe déjà pour cette commande"
                })

        # Ajouter l'alias
        success = command_aliases.add_alias(command, alias)

        if success:
            add_log(f"Alias '{alias}' ajouté pour la commande '{command}'", "info")
            # Sauvegarder les modifications dans la base de données
            command_aliases.save_to_database()
            return jsonify({
                "success": True,
                "command": command,
                "alias": alias
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de l'ajout de l'alias '{alias}' pour la commande '{command}'"
            })
    except Exception as e:
        print(f"Erreur lors de l'ajout d'un alias: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/add_command_alias"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/remove_command_alias')
def remove_command_alias_route():
    """Supprime un alias de commande"""
    try:
        from command_aliases import command_aliases

        data = request.get_json()
        alias = data.get('alias')

        print(f"Tentative de suppression d'alias: '{alias}'")

        if not alias:
            return jsonify({"success": False, "error": "Alias non spécifié"})

        # Vérifier si l'alias existe
        if alias not in command_aliases.command_lookup:
            return jsonify({
                "success": False,
                "error": f"L'alias '{alias}' n'existe pas"
            })

        # Récupérer la commande associée pour le message de log
        command = command_aliases.command_lookup[alias]

        # Supprimer l'alias
        success = command_aliases.remove_alias(alias)

        if success:
            add_log(f"Alias '{alias}' supprimé pour la commande '{command}'", "info")
            # Sauvegarder les modifications dans la base de données
            command_aliases.save_to_database()
            return jsonify({
                "success": True,
                "alias": alias
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Échec de la suppression de l'alias '{alias}'"
            })
    except Exception as e:
        print(f"Erreur lors de la suppression d'un alias: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/remove_command_alias"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/reload_command_aliases')
def reload_command_aliases_route():
    """Recharge les alias de commandes depuis la base de données"""
    try:
        from command_aliases import command_aliases

        # Recharger les alias depuis la base de données
        success = command_aliases.reload_from_database()

        if success:
            add_log("Alias de commandes rechargés avec succès", "info")
            return jsonify({
                "success": True,
                "message": "Alias rechargés avec succès",
                "count": len(command_aliases.aliases)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec du rechargement des alias"
            })
    except Exception as e:
        print(f"Erreur lors du rechargement des alias: {str(e)}")
        traceback.print_exc()
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/reload_command_aliases"}
        )
        return jsonify({"success": False, "error": str(e)})
