"""
Configuration pytest pour les tests Whisp Assistant
"""

import pytest
import sys
from pathlib import Path

# Ajouter le parent au path pour importer les modules
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


@pytest.fixture
def mock_config():
    """Configuration de test"""
    from config import WhispConfig
    config = WhispConfig()
    config.running = True
    config.stt_engine = "speechrecognition"
    config.tts_engine = "gtts"
    return config


@pytest.fixture
def mock_validator():
    """Validateur de test"""
    from input_validation import InputValidator
    return InputValidator()


@pytest.fixture
def sample_audio_input():
    """Input audio simulé"""
    return b"fake audio data for testing"


@pytest.fixture
def sample_commands():
    """Commandes de test"""
    return {
        "safe": "ouvre notepad",
        "with_injection": "ouvre notepad && rm -rf /",
        "with_path_traversal": "ouvre ../../etc/passwd",
    }


@pytest.fixture
def temp_log_dir(tmp_path):
    """Répertoire temporaire pour les logs de test"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir
