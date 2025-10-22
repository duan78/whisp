"""
Module de gestion des tickets de bugs pour l'assistant Whisp
"""
import time
import json
import uuid
from datetime import datetime
from database_manager import ensure_connection

class BugTracker:
    """Gestionnaire de tickets de bugs"""
    
    def __init__(self):
        """Initialise le gestionnaire de tickets"""
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialise la table des tickets dans la base de données"""
        @ensure_connection
        def init_db(conn):
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS bug_tickets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                steps TEXT,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                comments TEXT
            )
            ''')
            conn.commit()
        
        init_db()
    
    def create_ticket(self, title, description, steps="", category="other", priority="medium"):
        """
        Crée un nouveau ticket de bug
        
        Args:
            title: Titre du bug
            description: Description détaillée
            steps: Étapes pour reproduire
            category: Catégorie du bug
            priority: Priorité (low, medium, high)
            
        Returns:
            dict: Le ticket créé
        """
        @ensure_connection
        def create_ticket_db(conn):
            ticket_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bug_tickets 
                (id, title, description, steps, category, priority, status, created_at, updated_at, comments) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ticket_id, title, description, steps, category, priority, "open", now, now, "[]")
            )
            conn.commit()
            
            return {
                "id": ticket_id,
                "title": title,
                "description": description,
                "steps": steps,
                "category": category,
                "priority": priority,
                "status": "open",
                "created_at": now,
                "updated_at": now,
                "comments": []
            }
        
        return create_ticket_db()
    
    def get_all_tickets(self):
        """
        Récupère tous les tickets de bugs
        
        Returns:
            list: Liste des tickets
        """
        @ensure_connection
        def get_tickets_db(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bug_tickets ORDER BY created_at DESC")
            rows = cursor.fetchall()
            
            tickets = []
            for row in rows:
                ticket = dict(row)
                # Convertir les commentaires de JSON à liste Python
                ticket["comments"] = json.loads(ticket["comments"])
                tickets.append(ticket)
            
            return tickets
        
        return get_tickets_db()
    
    def get_ticket(self, ticket_id):
        """
        Récupère un ticket spécifique
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            dict: Le ticket ou None s'il n'existe pas
        """
        @ensure_connection
        def get_ticket_db(conn):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bug_tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            
            if row:
                ticket = dict(row)
                # Convertir les commentaires de JSON à liste Python
                ticket["comments"] = json.loads(ticket["comments"])
                return ticket
            
            return None
        
        return get_ticket_db()
    
    def update_ticket(self, ticket_id, **kwargs):
        """
        Met à jour un ticket existant
        
        Args:
            ticket_id: ID du ticket
            **kwargs: Champs à mettre à jour
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        @ensure_connection
        def update_ticket_db(conn):
            # Vérifier si le ticket existe
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bug_tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            # Préparer les champs à mettre à jour
            allowed_fields = ["title", "description", "steps", "category", "priority", "status"]
            updates = {}
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates[field] = value
            
            if not updates:
                return False
            
            # Ajouter la date de mise à jour
            updates["updated_at"] = datetime.now().isoformat()
            
            # Construire la requête SQL
            set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
            values = list(updates.values())
            values.append(ticket_id)
            
            # Exécuter la mise à jour
            cursor.execute(
                f"UPDATE bug_tickets SET {set_clause} WHERE id = ?",
                values
            )
            conn.commit()
            
            return cursor.rowcount > 0
        
        return update_ticket_db()
    
    def add_comment(self, ticket_id, comment_text):
        """
        Ajoute un commentaire à un ticket
        
        Args:
            ticket_id: ID du ticket
            comment_text: Texte du commentaire
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        @ensure_connection
        def add_comment_db(conn):
            # Récupérer les commentaires actuels
            cursor = conn.cursor()
            cursor.execute("SELECT comments FROM bug_tickets WHERE id = ?", (ticket_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            comments = json.loads(row["comments"])
            
            # Ajouter le nouveau commentaire
            new_comment = {
                "id": str(uuid.uuid4()),
                "text": comment_text,
                "created_at": datetime.now().isoformat()
            }
            comments.append(new_comment)
            
            # Mettre à jour le ticket
            cursor.execute(
                "UPDATE bug_tickets SET comments = ?, updated_at = ? WHERE id = ?",
                (json.dumps(comments), datetime.now().isoformat(), ticket_id)
            )
            conn.commit()
            
            return cursor.rowcount > 0
        
        return add_comment_db()
    
    def delete_ticket(self, ticket_id):
        """
        Supprime un ticket
        
        Args:
            ticket_id: ID du ticket
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        @ensure_connection
        def delete_ticket_db(conn):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bug_tickets WHERE id = ?", (ticket_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        
        return delete_ticket_db()

# Instance singleton du gestionnaire de tickets
bug_tracker = BugTracker()
