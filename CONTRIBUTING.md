# Contribuer à Whisp Assistant

Merci de votre intérêt pour contribuer à Whisp Assistant ! Ce guide vous aidera à démarrer.

## 🤝 Comment Contribuer

### 1. Fork le Projet

1. Allez sur le repository GitHub
2. Cliquez sur le bouton "Fork" en haut à droite
3. Clonez votre fork localement :

```bash
git clone https://github.com/VOTRE_USERNAME/whisp-assistant.git
cd whisp-assistant
```

### 2. Configurer votre Environnement

```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Installer les dépendances de développement
pip install -r requirements-dev.txt
```

### 3. Créer une Branche

```bash
# Mettre à jour la branche main
git checkout main
git pull upstream main

# Créer votre branche de fonctionnalité
git checkout -b feature/nom-de-la-fonctionnalite
```

## 📝 Types de Contributions

### 🐛 Rapports de Bugs

Avant de rapporter un bug :

1. [Vérifiez si le bug existe déjà](https://github.com/VOTRE_USERNAME/whisp-assistant/issues)
2. Assurez-vous d'utiliser la dernière version
3. Essayez de reproduire le bug dans un environnement clean

Pour rapporter un bug :

- Utilisez le [template de bug](.github/ISSUE_TEMPLATE/bug_report.md)
- Incluez votre configuration système
- Fournissez les étapes pour reproduire
- Ajoutez les logs d'erreur pertinents

### ✨ Nouvelles Fonctionnalités

1. Ouvrez une [issue](https://github.com/VOTRE_USERNAME/whisp-assistant/issues) pour discuter de la fonctionnalité
2. Attendre l'approbation avant de commencer le développement
3. Suivez les guidelines ci-dessous

### 📚 Documentation

Les contributions à la documentation sont toujours appréciées :

- Correction de typos
- Amélioration des explications
- Ajout d'exemples
- Traduction

## 🔧 Guidelines de Code

### Style de Code

Nous suivons [PEP 8](https://www.python.org/dev/peps/pep-0008/) avec quelques spécificités :

```python
# Imports
import os
import sys
from typing import Optional, Dict, List

# Constantes en MAJUSCULES
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Classes en PascalCase
class SpeechProcessor:
    """Classe pour le traitement vocal"""

    def __init__(self, config: Dict[str, str]) -> None:
        self.config = config

    def process_audio(self, audio_data: bytes) -> Optional[str]:
        """Traite les données audio et retourne le texte reconnu"""
        pass

# Fonctions en snake_case
def setup_microphone() -> Optional[object]:
    """Configure le microphone et retourne l'instance"""
    pass

# Variables en snake_case
user_command = "hello world"
is_processing = True
```

### Documentation du Code

```python
def process_command(self, command: str, context: Dict[str, Any]) -> bool:
    """
    Traite une commande vocale et exécute l'action correspondante.

    Args:
        command: La commande textuelle à traiter
        context: Contexte additionnel (utilisateur, session, etc.)

    Returns:
        True si la commande a été exécutée avec succès, False sinon

    Raises:
        CommandError: Si la commande est invalide ou impossible à exécuter

    Example:
        >>> processor = CommandProcessor()
        >>> success = processor.process_command("ouvre notepad", {})
        >>> print(f"Commande exécutée: {success}")
    """
```

### Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from speech_processor import SpeechProcessor

class TestSpeechProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = SpeechProcessor({"test": "config"})

    def test_process_valid_command(self):
        """Test le traitement d'une commande valide"""
        result = self.processor.process_command("test")
        self.assertTrue(result)

    @patch('speech_processor.AudioFile')
    def test_with_mock(self, mock_audio):
        """Test avec un mock"""
        mock_audio.return_value = MagicMock()
        # Test logic here
```

## 📁 Structure du Projet

```
whisp-assistant/
├── src/                    # Code source principal
│   ├── core/              # Modules core
│   ├── commands/          # Modules de commandes
│   ├── interfaces/        # Interfaces (web, CLI)
│   └── utils/             # Utilitaires
├── tests/                 # Tests unitaires et intégration
├── docs/                  # Documentation
├── examples/              # Exemples d'utilisation
├── scripts/               # Scripts de développement
└── resources/             # Ressources (templates, assets)
```

## 🧪 Tests

### Lancer les Tests

```bash
# Tous les tests
pytest

# Tests spécifiques
pytest tests/test_speech.py

# Avec couverture
pytest --cov=src tests/

# Tests rapides (exclure les lents)
pytest -m "not slow"
```

### Écrire des Tests

- Chaque nouvelle fonctionnalité doit avoir des tests
- Couvrez les cas limites et les erreurs
- Utilisez des mocks pour les dépendances externes

## 📖 Commit Messages

Nous utilisons [Conventional Commits](https://www.conventionalcommits.org/) :

```
type(scope): description

feat(commands): add voice command for file management
fix(speech): resolve microphone initialization issue
docs(readme): update installation instructions
style(core): improve code formatting
refactor(tts): simplify audio processing logic
test(speech): add tests for speech recognition
chore(deps): update pytest version
```

## 🔄 Pull Request Process

### Avant de Soumettre

1. **Tests** : Assurez-vous que tous les tests passent
2. **Linting** : Vérifiez le style de code
3. **Documentation** : Mettez à jour la documentation pertinente
4. **Commits** : Utilisez des messages de commit clairs

### Processus de PR

1. Créez une Pull Request depuis votre branche vers `main`
2. Utilisez le [template de PR](.github/PULL_REQUEST_TEMPLATE.md)
3. Attendez la review des mainteneurs
4. Corrigez les commentaires demandés
5. Votre PR sera mergée quand prête

### Checklists de PR

#### Code
- [ ] Le code suit les guidelines de style
- [ ] Les tests passent
- [ ] La documentation est mise à jour
- [ ] Les messages de commit sont clairs

#### Fonctionnalité
- [ ] La fonctionnalité fonctionne comme attendu
- [ ] Les cas limites sont gérés
- [ ] Les erreurs sont gérées proprement
- [ ] La performance est acceptable

## 🏷️ Labels et Milestones

### Labels Communs
- `bug` : Rapport de bug
- `enhancement` : Nouvelle fonctionnalité
- `documentation` : Documentation
- `good first issue` : Bon pour débutants
- `help wanted` : Aide demandée
- `priority: high` : Haute priorité

### Milestones
- `v1.1.x` : Corrections et petites améliorations
- `v1.2.0` : Nouvelles fonctionnalités
- `v2.0.0` : Changements majeurs

## 🚨 Guidelines de Sécurité

Si vous découvrez une vulnérabilité de sécurité :

1. **NE PAS** ouvrir d'issue publique
2. Envoyez un email à : security@whisp-assistant.com
3. Décrivez la vulnérabilité en détail
4. Nous répondrons dans les 48h

## 💬 Obtenez de l'Aide

- **Discord** : [Serveur communautaire](https://discord.gg/whisp)
- **GitHub Discussions** : Pour les questions générales
- **Issues** : Pour les bugs et fonctionnalités

## 🎯 Priorités Actuelles

Consultez notre [board de projets](https://github.com/VOTRE_USERNAME/whisp-assistant/projects) pour voir les priorités actuelles et où vous pouvez aider.

---

Merci encore pour votre contribution à Whisp Assistant ! 🙏