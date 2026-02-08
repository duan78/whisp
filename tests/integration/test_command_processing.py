"""
Tests d'intégration pour le traitement des commandes
"""

import pytest
from input_validation import InputValidator, ValidationError
from system_commands import executer_commande_systeme


class TestCommandProcessingIntegration:
    """Tests d'intégration pour le flux complet de traitement des commandes"""

    def test_safe_command_execution(self):
        """Test l'exécution d'une commande sûre"""
        result = executer_commande_systeme("quelle heure est-il")
        assert "Il est" in result

    def test_dangerous_command_rejection(self):
        """Test qu'une commande dangereuse est rejetée"""
        result = executer_commande_systeme("ouvre notepad && rm -rf /")
        assert "non autorisée" in result.lower() or "erreur" in result.lower()

    def test_path_traversal_rejection(self):
        """Test qu'une commande avec traversal est rejetée"""
        result = executer_commande_systeme("ouvre ../../../etc/passwd")
        # Soit la validation le bloque, soit la commande n'est pas reconnue
        assert "non autorisée" in result.lower() or "non reconnue" in result.lower() or "erreur" in result.lower()

    def test_command_validation_chain(self):
        """Test la chaîne complète de validation"""
        validator = InputValidator()

        # Commande sûre
        safe_cmd = "ouvre notepad"
        validated = validator.validate_command(safe_cmd)
        assert validated == safe_cmd

        # Vérifier que l'application est dans la whitelist
        app_name = validator.extract_app_name(safe_cmd)
        assert app_name in validator.allowed_commands

    def test_max_length_enforcement(self):
        """Test que les commandes trop longues sont rejetées"""
        validator = InputValidator()
        long_command = "a" * 2000

        with pytest.raises(ValidationError):
            validator.validate_command(long_command)
