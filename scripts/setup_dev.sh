#!/bin/bash

# Script de configuration de l'environnement de développement pour Whisp Assistant
# Usage: bash scripts/setup_dev.sh

set -e

echo "🚀 Configuration de l'environnement de développement Whisp Assistant..."

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 est requis mais n'est pas installé."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION détecté"

# Créer l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate

# Mettre à jour pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip setuptools wheel

# Installer les dépendances
echo "📚 Installation des dépendances..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Installer pre-commit hooks
echo "🔗 Configuration des hooks pre-commit..."
pre-commit install

# Créer les fichiers de configuration si nécessaire
if [ ! -f "config.env" ]; then
    echo "📝 Création du fichier de configuration..."
    cp config.example.env config.env
    echo "✅ Fichier config.env créé. Éditez-le selon vos besoins."
fi

if [ ! -f "api_keys.json" ]; then
    echo "🔑 Création du fichier de clés API..."
    cp api_keys.json.example api_keys.json
    echo "✅ Fichier api_keys.json créé. Ajoutez vos clés API."
fi

# Créer les dossiers nécessaires
echo "📁 Création des dossiers de données..."
mkdir -p logs
mkdir -p records
mkdir -p backups
mkdir -p cache

# Vérifier l'installation
echo "🧪 Vérification de l'installation..."
python -c "
try:
    import speech_recognition_module
    print('✅ Module STT OK')
except ImportError as e:
    print(f'❌ Erreur STT: {e}')

try:
    import tts_module
    print('✅ Module TTS OK')
except ImportError as e:
    print(f'❌ Erreur TTS: {e}')

try:
    import web_interface
    print('✅ Interface web OK')
except ImportError as e:
    print(f'❌ Erreur interface web: {e}')
"

# Tests rapides
echo "🧪 Exécution des tests rapides..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short -x || echo "⚠️  Certains tests ont échoué. Vérifiez la configuration."
else
    echo "⚠️  pytest non trouvé, saut des tests."
fi

echo ""
echo "🎉 Configuration terminée !"
echo ""
echo "Prochaines étapes :"
echo "1. Activez l'environnement: source venv/bin/activate"
echo "2. Configurez vos clés API dans api_keys.json"
echo "3. Adaptez config.env selon vos préférences"
echo "4. Lancez l'assistant: python main.py"
echo ""
echo "Documentation: https://docs.whisp-assistant.com"
echo "Support: https://github.com/votre-username/whisp-assistant/issues"