# Script de configuration de l'environnement de développement pour Whisp Assistant (Windows)
# Usage: .\scripts\setup_dev.ps1

Write-Host "🚀 Configuration de l'environnement de développement Whisp Assistant..." -ForegroundColor Green

# Vérifier Python
try {
    $pythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
    Write-Host "✅ Python $pythonVersion détecté" -ForegroundColor Green
} catch {
    Write-Host "❌ Python est requis mais n'est pas installé." -ForegroundColor Red
    exit 1
}

# Créer l'environnement virtuel
if (-not (Test-Path "venv")) {
    Write-Host "📦 Création de l'environnement virtuel..." -ForegroundColor Yellow
    python -m venv venv
}

# Activer l'environnement virtuel
Write-Host "🔧 Activation de l'environnement virtuel..." -ForegroundColor Yellow
& venv\Scripts\Activate.ps1

# Mettre à jour pip
Write-Host "⬆️  Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel

# Installer les dépendances
Write-Host "📚 Installation des dépendances..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Installer pre-commit hooks
Write-Host "🔗 Configuration des hooks pre-commit..." -ForegroundColor Yellow
pre-commit install

# Créer les fichiers de configuration si nécessaire
if (-not (Test-Path "config.env")) {
    Write-Host "📝 Création du fichier de configuration..." -ForegroundColor Yellow
    Copy-Item config.example.env config.env
    Write-Host "✅ Fichier config.env créé. Éditez-le selon vos besoins." -ForegroundColor Green
}

if (-not (Test-Path "api_keys.json")) {
    Write-Host "🔑 Création du fichier de clés API..." -ForegroundColor Yellow
    Copy-Item api_keys.json.example api_keys.json
    Write-Host "✅ Fichier api_keys.json créé. Ajoutez vos clés API." -ForegroundColor Green
}

# Créer les dossiers nécessaires
Write-Host "📁 Création des dossiers de données..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path logs
New-Item -ItemType Directory -Force -Path records
New-Item -ItemType Directory -Force -Path backups
New-Item -ItemType Directory -Force -Path cache

# Vérifier l'installation
Write-Host "🧪 Vérification de l'installation..." -ForegroundColor Yellow
try {
    python -c "
import sys
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
} catch {
    Write-Host "⚠️  Erreur lors de la vérification des modules." -ForegroundColor Yellow
}

# Tests rapides
Write-Host "🧪 Exécution des tests rapides..." -ForegroundColor Yellow
if (Get-Command pytest -ErrorAction SilentlyContinue) {
    try {
        pytest tests\ -v --tb=short -x
    } catch {
        Write-Host "⚠️  Certains tests ont échoué. Vérifiez la configuration." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  pytest non trouvé, saut des tests." -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor White
Write-Host "🎉 Configuration terminée !" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "Prochaines étapes :" -ForegroundColor Cyan
Write-Host "1. Activez l'environnement: venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Configurez vos clés API dans api_keys.json" -ForegroundColor White
Write-Host "3. Adaptez config.env selon vos préférences" -ForegroundColor White
Write-Host "4. Lancez l'assistant: python main.py" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "Documentation: https://docs.whisp-assistant.com" -ForegroundColor Cyan
Write-Host "Support: https://github.com/votre-username/whisp-assistant/issues" -ForegroundColor Cyan