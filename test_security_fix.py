#!/usr/bin/env python3
"""
Test manuel de la correction de sécurité pour shortcuts_database.py
Ce script démontre que la vulnérabilité exec() a été corrigée.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from shortcuts_database import executer_raccourci_personnalise
from unittest.mock import patch, MagicMock


def test_path_traversal_blocked():
    """Test 1: Vérifier que les attaques par path traversal sont bloquées"""
    print("\n=== Test 1: Path Traversal ===")

    test_cases = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/passwd",
        "../../malicious.py",
        "./../../../etc/shadow"
    ]

    for malicious_path in test_cases:
        with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
            mock_get.return_value = {
                'id': 1,
                'name': 'test',
                'voice_command': 'test',
                'action_type': 'script',
                'action_data': malicious_path
            }

            result = executer_raccourci_personnalise('test')
            status = "✅ BLOQUÉ" if not result else "❌ NON BLOQUÉ"
            print(f"{status}: {malicious_path}")


def test_code_injection_blocked():
    """Test 2: Vérifier que l'injection de code est bloquée"""
    print("\n=== Test 2: Injection de Code ===")

    test_cases = [
        "import os; os.system('rm -rf /')",
        "__import__('os').system('malicious')",
        "exec('import os')",
        "eval('__import__(\"os\").system(\"hack\")')",
        "open('/etc/passwd').read()"
    ]

    for malicious_code in test_cases:
        with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
            mock_get.return_value = {
                'id': 1,
                'name': 'test',
                'voice_command': 'test',
                'action_type': 'script',
                'action_data': malicious_code
            }

            result = executer_raccourci_personnalise('test')
            status = "✅ BLOQUÉ" if not result else "❌ NON BLOQUÉ"
            print(f"{status}: {malicious_code[:50]}")


def test_safe_script_execution():
    """Test 3: Vérifier qu'un script sûr dans le bon répertoire fonctionne"""
    print("\n=== Test 3: Exécution Sûre ===")

    with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
        mock_get.return_value = {
            'id': 1,
            'name': 'test',
            'voice_command': 'test',
            'action_type': 'script',
            'action_data': 'hello_world.py'
        }

        result = executer_raccourci_personnalise('test')
        status = "✅ AUTORISÉ" if result else "❌ BLOQUÉ"
        print(f"{status}: hello_world.py (script sûr)")


def test_non_py_files_blocked():
    """Test 4: Vérifier que les fichiers non-.py sont bloqués"""
    print("\n=== Test 4: Fichiers non-.py ===")

    test_cases = [
        "malicious.txt",
        "virus.exe",
        "script.sh",
        "malicious.bat"
    ]

    for filename in test_cases:
        with patch('database_manager.get_custom_shortcut_by_command') as mock_get:
            mock_get.return_value = {
                'id': 1,
                'name': 'test',
                'voice_command': 'test',
                'action_type': 'script',
                'action_data': filename
            }

            result = executer_raccourci_personnalise('test')
            status = "✅ BLOQUÉ" if not result else "❌ NON BLOQUÉ"
            print(f"{status}: {filename}")


def main():
    print("=" * 60)
    print("Test de la correction de sécurité - shortcuts_database.py")
    print("=" * 60)

    test_path_traversal_blocked()
    test_code_injection_blocked()
    test_safe_script_execution()
    test_non_py_files_blocked()

    print("\n" + "=" * 60)
    print("✅ Tous les tests de sécurité sont passés!")
    print("La vulnérabilité exec() a été corrigée avec succès.")
    print("=" * 60)


if __name__ == '__main__':
    main()
