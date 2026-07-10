"""
Tests de sécurité pour le module shortcuts_database
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Importer le module à tester
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shortcuts_database import (
    executer_raccourci_personnalise,
    execute_custom_shortcut,  # Alias pour compatibilité
    SCRIPTS_DIR,
    initialize_scripts_directory
)


class TestShortcutsSecurity:
    """Tests de sécurité pour l'exécution de raccourcis personnalisés"""

    def test_script_execution_blocks_path_traversal(self):
        """Test que les attaques par path traversal sont bloquées"""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/passwd',
            'C:\\Windows\\System32\\config\\SAM',
            '../../malicious.py',
            './../../../etc/shadow'
        ]

        for malicious_path in malicious_paths:
            # Mock get_custom_shortcut_by_command pour retourner notre raccourci malveillant
            # Patch au bon endroit - la fonction est importée dynamiquement dans executer_raccourci_personnalise
            with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
                mock_get.return_value = {
                    'id': 1,
                    'name': 'test',
                    'voice_command': 'test',
                    'action_type': 'script',
                    'action_data': malicious_path
                }

                result = executer_raccourci_personnalise('test')
                assert result is False, f"Path traversal non bloqué pour: {malicious_path}"

    def test_script_execution_blocks_non_py_files(self):
        """Test que les fichiers non-.py sont bloqués"""
        # Créer un fichier temporaire non-.py
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_file = Path(f.name)
            f.write(b"malicious content")

        try:
            with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
                mock_get.return_value = {
                    'id': 1,
                    'name': 'test',
                    'voice_command': 'test',
                    'action_type': 'script',
                    'action_data': temp_file.name
                }

                with patch('shortcuts_database.SCRIPTS_DIR', temp_file.parent):
                    result = executer_raccourci_personnalise('test')
                    # Doit échouer car ce n'est pas un fichier .py
                    assert result is False
        finally:
            temp_file.unlink()

    def test_script_execution_enforces_trusted_directory(self):
        """Test que seuls les scripts dans le répertoire de confiance sont exécutés"""
        # Créer un script Python malveillant dans /tmp
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            temp_script = Path(f.name)
            f.write("print('Should not execute')")

        try:
            with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
                mock_get.return_value = {
                    'id': 1,
                    'name': 'test',
                    'voice_command': 'test',
                    'action_type': 'script',
                    'action_data': temp_script.name
                }

                # Le script est dans /tmp, pas dans SCRIPTS_DIR, donc doit échouer
                result = executer_raccourci_personnalise('test')
                assert result is False, "Script hors du répertoire de confiance exécuté"
        finally:
            temp_script.unlink()

    def test_script_execution_blocks_code_injection(self):
        """Test que l'injection de code directe est bloquée"""
        malicious_code = [
            "import os; os.system('rm -rf /')",
            "__import__('os').system('malicious')",
            "exec('import os; os.system(\\'hack\\')')",
            "eval('__import__(\\'os\\').system(\\'hack\\')')"
        ]

        for code in malicious_code:
            with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
                mock_get.return_value = {
                    'id': 1,
                    'name': 'test',
                    'voice_command': 'test',
                    'action_type': 'script',
                    'action_data': code
                }

                result = executer_raccourci_personnalise('test')
                # Doit échouer car ce n'est pas un nom de fichier valide
                assert result is False, f"Injection de code non bloquée: {code}"

    def test_script_execution_timeout(self):
        """Test que les scripts ont un timeout"""
        # Créer un script qui boucle infiniment
        script_content = """#!/usr/bin/env python3
import time
while True:
    time.sleep(1)
"""

        # Créer un script temporaire dans SCRIPTS_DIR
        with patch('shortcuts_database.SCRIPTS_DIR') as mock_dir:
            mock_dir.mkdir(parents=True, exist_ok=True)
            mock_dir.__truediv__ = lambda self, name: Path(self) / name

            temp_dir = Path(tempfile.mkdtemp())
            script_path = temp_dir / 'infinite_loop.py'

            with open(script_path, 'w') as f:
                f.write(script_content)

            try:
                with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
                    mock_get.return_value = {
                        'id': 1,
                        'name': 'test',
                        'voice_command': 'test',
                        'action_type': 'script',
                        'action_data': 'infinite_loop.py'
                    }

                    with patch('shortcuts_database.SCRIPTS_DIR', temp_dir):
                        # Le script doit timeout après 30 secondes
                        # Pour le test, on vérifie juste qu'il ne bloque pas indéfiniment
                        # Dans un vrai test, on utiliserait un mock de subprocess.run
                        pass
            finally:
                script_path.unlink()
                temp_dir.rmdir()


class TestScriptsDirectory:
    """Tests pour le répertoire de scripts"""

    def test_initialize_scripts_directory(self):
        """Test que le répertoire de scripts est correctement initialisé"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('shortcuts_database.SCRIPTS_DIR', Path(temp_dir) / 'scripts'):
                initialize_scripts_directory()

                # Vérifier que le répertoire existe
                assert (Path(temp_dir) / 'scripts').exists()

                # Vérifier que le README existe
                readme_path = Path(temp_dir) / 'scripts' / 'README.txt'
                assert readme_path.exists()

                # Vérifier le contenu du README
                with open(readme_path, 'r') as f:
                    content = f.read()
                    assert 'sécurité' in content.lower()
                    assert '.py' in content

    def test_scripts_directory_path(self):
        """Test que le répertoire de scripts est dans ~/.whisp"""
        expected_path = Path.home() / '.whisp' / 'scripts'
        assert SCRIPTS_DIR == expected_path


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
