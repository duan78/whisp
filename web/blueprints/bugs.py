"""Blueprint for bug ticket management routes.

Extracted verbatim from ``web_interface.py``. Only the decorators changed
(``@app.*`` -> ``@bp.*``); route bodies are unchanged.
"""

from flask import Blueprint, request, jsonify
from web.state import add_log, get_error_handler, get_error_types, get_bug_tracker

bp = Blueprint('bugs', __name__)

# Routes pour la gestion des tickets de bugs
@bp.get('/api/bug_tickets')
def get_bug_tickets():
    """Récupère tous les tickets de bugs"""
    try:
        tickets = get_bug_tracker().get_all_tickets()
        return jsonify({
            "success": True,
            "tickets": tickets
        })
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/api/bug_tickets"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.get('/api/bug_tickets/<ticket_id>')
def get_bug_ticket(ticket_id):
    """Récupère un ticket spécifique"""
    try:
        ticket = get_bug_tracker().get_ticket(ticket_id)
        if ticket:
            return jsonify({
                "success": True,
                "ticket": ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/api/bug_tickets')
def create_bug_ticket():
    """Crée un nouveau ticket de bug"""
    try:
        data = request.get_json()

        # Vérifier les champs requis
        required_fields = ["title", "description", "category", "priority"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Champ requis manquant: {field}"
                }), 400

        # Créer le ticket
        ticket = get_bug_tracker().create_ticket(
            title=data["title"],
            description=data["description"],
            steps=data.get("steps", ""),
            category=data["category"],
            priority=data["priority"]
        )

        add_log(f"Nouveau ticket de bug créé: {ticket['title']}", "info")

        return jsonify({
            "success": True,
            "ticket": ticket
        }), 201
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": "/api/bug_tickets"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.put('/api/bug_tickets/<ticket_id>')
def update_bug_ticket(ticket_id):
    """Met à jour un ticket existant"""
    try:
        data = request.get_json()

        # Vérifier si le ticket existe
        ticket = get_bug_tracker().get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404

        # Mettre à jour le ticket
        success = get_bug_tracker().update_ticket(ticket_id, **data)

        if success:
            add_log(f"Ticket de bug mis à jour: {ticket_id}", "info")
            updated_ticket = get_bug_tracker().get_ticket(ticket_id)
            return jsonify({
                "success": True,
                "ticket": updated_ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la mise à jour du ticket"
            }), 400
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.post('/api/bug_tickets/<ticket_id>/comments')
def add_bug_ticket_comment(ticket_id):
    """Ajoute un commentaire à un ticket"""
    try:
        data = request.get_json()

        # Vérifier si le ticket existe
        ticket = get_bug_tracker().get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404

        # Vérifier le champ requis
        if "text" not in data:
            return jsonify({
                "success": False,
                "error": "Champ requis manquant: text"
            }), 400

        # Ajouter le commentaire
        success = get_bug_tracker().add_comment(ticket_id, data["text"])

        if success:
            add_log(f"Commentaire ajouté au ticket: {ticket_id}", "info")
            updated_ticket = get_bug_tracker().get_ticket(ticket_id)
            return jsonify({
                "success": True,
                "ticket": updated_ticket
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de l'ajout du commentaire"
            }), 400
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}/comments"}
        )
        return jsonify({"success": False, "error": str(e)})

@bp.delete('/api/bug_tickets/<ticket_id>')
def delete_bug_ticket(ticket_id):
    """Supprime un ticket"""
    try:
        # Vérifier si le ticket existe
        ticket = get_bug_tracker().get_ticket(ticket_id)
        if not ticket:
            return jsonify({
                "success": False,
                "error": "Ticket non trouvé"
            }), 404

        # Supprimer le ticket
        success = get_bug_tracker().delete_ticket(ticket_id)

        if success:
            add_log(f"Ticket de bug supprimé: {ticket_id}", "info")
            return jsonify({
                "success": True
            })
        else:
            return jsonify({
                "success": False,
                "error": "Échec de la suppression du ticket"
            }), 400
    except Exception as e:
        get_error_handler().handle_error(
            e,
            category=ErrorCategory.WEB_INTERFACE,
            severity=ErrorSeverity.LOW,
            context={"route": f"/api/bug_tickets/{ticket_id}"}
        )
        return jsonify({"success": False, "error": str(e)})
