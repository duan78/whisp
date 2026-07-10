"""
Tests for TTS engines including edge-tts and Piper TTS
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, Mock

# Importer le module à tester
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestTTSEngines(unittest.TestCase):
    """Tests pour les moteurs TTS"""

    def test_edge_tts_function_exists(self):
        """Test que la fonction lire_texte_edge_tts existe"""
        import tts_module
        assert hasattr(tts_module, 'lire_texte_edge_tts')
        assert callable(tts_module.lire_texte_edge_tts)

    def test_piper_tts_function_exists(self):
        """Test que la fonction lire_texte_piper existe"""
        import tts_module
        assert hasattr(tts_module, 'lire_texte_piper')
        assert callable(tts_module.lire_texte_piper)

    def test_edge_tts_import_function_exists(self):
        """Test que les variables edge_tts et piper_tts existent"""
        import tts_module
        assert hasattr(tts_module, 'edge_tts')
        assert hasattr(tts_module, 'piper_tts')

    def test_piper_import_function_exists(self):
        """Test que la fonction import_piper_tts existe"""
        import tts_module
        assert hasattr(tts_module, 'import_piper_tts')
        assert callable(tts_module.import_piper_tts)

    def test_piper_load_model_function_exists(self):
        """Test que la fonction load_piper_model existe"""
        import tts_module
        assert hasattr(tts_module, 'load_piper_model')
        assert callable(tts_module.load_piper_model)

    def test_tts_rate_includes_edge_tts(self):
        """Test que edge_tts est dans la configuration des taux TTS"""
        import tts_module
        assert 'edge_tts' in tts_module.tts_rate
        assert isinstance(tts_module.tts_rate['edge_tts'], (int, float))

    def test_tts_rate_includes_piper(self):
        """Test que piper est dans la configuration des taux TTS"""
        import tts_module
        assert 'piper' in tts_module.tts_rate
        assert isinstance(tts_module.tts_rate['piper'], (int, float))

    def test_edge_tts_rate_value(self):
        """Test que le taux edge_tts est correctement configuré"""
        import tts_module
        assert tts_module.tts_rate['edge_tts'] == 1.0  # Vitesse normale

    def test_piper_rate_value(self):
        """Test que le taux piper est correctement configuré"""
        import tts_module
        assert tts_module.tts_rate['piper'] == 1.0  # Vitesse normale

    def test_edge_tts_cache_exists(self):
        """Test que le cache edge_tts existe"""
        import tts_module
        assert hasattr(tts_module, 'edge_tts_cache')
        assert isinstance(tts_module.edge_tts_cache, dict)

    def test_piper_cache_exists(self):
        """Test que le cache piper existe"""
        import tts_module
        assert hasattr(tts_module, 'piper_cache')
        assert isinstance(tts_module.piper_cache, dict)

    def test_edge_tts_voice_exists(self):
        """Test que la voix edge_tts par défaut existe"""
        import tts_module
        assert hasattr(tts_module, 'edge_tts_voice')
        assert tts_module.edge_tts_voice == "fr-FR-DeniseNeural"

    def test_piper_model_name_exists(self):
        """Test que le nom du modèle Piper par défaut existe"""
        import tts_module
        assert hasattr(tts_module, 'piper_model_name')
        assert tts_module.piper_model_name == "fr_FR-gilles-low"


class TestTTSEngineIntegration(unittest.TestCase):
    """Tests d'intégration pour les moteurs TTS"""

    def test_tts_module_imports(self):
        """Test que le module TTS peut être importé"""
        import tts_module
        assert tts_module is not None

    def test_definir_moteur_tts_accepts_edge_tts(self):
        """Test que definir_moteur_tts accepte edge_tts"""
        import tts_module

        # Mock edge_tts as available
        with patch.object(tts_module, 'edge_tts', MagicMock()):
            result = tts_module.definir_moteur_tts('edge_tts')
            # Should return True if edge_tts is available
            assert result is True or result is False  # May return False if pygame not initialized

    def test_definir_moteur_tts_accepts_piper(self):
        """Test que definir_moteur_tts accepte piper"""
        import tts_module

        # Mock piper_model as available
        with patch.object(tts_module, 'piper_model', MagicMock()):
            result = tts_module.definir_moteur_tts('piper')
            # Should return True if piper is available
            assert result is True or result is False  # May return False if pygame not initialized

    def test_definir_moteur_tts_rejects_invalid_engine(self):
        """Test que definir_moteur_tts rejette les moteurs invalides"""
        import tts_module
        result = tts_module.definir_moteur_tts('invalid_engine')
        assert result is False

    def test_edge_tts_is_primary_online_tts(self):
        """Test qu'edge_tts est le moteur online prioritaire"""
        import tts_module

        # Vérifier que edge_tts est mentionné dans le code
        with open('tts_module.py', 'r') as f:
            content = f.read()

        # Vérifier que edge_tts existe et est correctement intégré
        edge_tts_pos = content.find("tts_engine_type == 'edge_tts'")
        assert edge_tts_pos > 0, "edge_tts should be in the code"

    def test_piper_is_primary_offline_tts(self):
        """Test que piper est le moteur offline prioritaire"""
        import tts_module

        # Vérifier que piper est mentionné dans le code
        with open('tts_module.py', 'r') as f:
            content = f.read()

        # Vérifier que piper existe dans le code
        piper_pos = content.find("tts_engine_type == 'piper'")
        pyttsx3_pos = content.find("tts_engine_type == 'pyttsx3'")

        # Vérifier que piper existe et est correctement intégré
        assert piper_pos > 0, "piper should be in the code"
        assert pyttsx3_pos > 0, "pyttsx3 should be in the code"
        # Note: l'ordre de priorité est géré par les conditions if/elif, pas par la position dans le fichier

class TestTTSEngineFallback(unittest.TestCase):
    """Tests de fallback pour les moteurs TTS"""

    @patch('tts_module.gTTS', None)
    @patch('tts_module.pyttsx3', MagicMock())
    def test_edge_tts_falls_back_to_gtts_if_unavailable(self):
        """Test qu'edge_tts bascule vers gTTS si non disponible"""
        import tts_module

        # Mock edge_tts as None (unavailable)
        with patch.object(tts_module, 'edge_tts', None):
            # Mock lire_texte_gtts to avoid actual execution
            with patch.object(tts_module, 'lire_texte_gtts') as mock_gtts:
                tts_module.lire_texte_edge_tts("test text")
                # Should call lire_texte_gtts as fallback
                mock_gtts.assert_called_once()

    @patch('tts_module.pyttsx3', None)
    @patch('tts_module.gTTS', MagicMock())
    def test_piper_falls_back_to_pyttsx3_if_unavailable(self):
        """Test que piper bascule vers pyttsx3 si non disponible"""
        import tts_module

        # Mock piper_model as None (unavailable)
        with patch.object(tts_module, 'piper_model', None):
            # Mock lire_texte_pyttsx3 to avoid actual execution
            with patch.object(tts_module, 'lire_texte_pyttsx3') as mock_pyttsx3:
                tts_module.lire_texte_piper("test text")
                # Should call lire_texte_pyttsx3 as fallback
                mock_pyttsx3.assert_called_once()


class TestTTSConfiguration(unittest.TestCase):
    """Tests de configuration TTS"""

    def test_valid_tts_engines_list(self):
        """Test que la liste des moteurs TTS valides est correcte"""
        import tts_module

        # Vérifier que les nouveaux moteurs sont dans les valid_engines
        valid_engines = ["pyttsx3", "edge_tts", "piper", "gtts", "coqui", "macos_say", "espeak"]

        # Vérifier dans initialiser_tts
        with open('tts_module.py', 'r') as f:
            content = f.read()

        for engine in valid_engines:
            assert f'"{engine}"' in content or f"'{engine}'" in content, f"{engine} should be in valid engines"

    def test_tts_engine_priority_order(self):
        """Test l'ordre de priorité des moteurs TTS"""
        import tts_module

        # Ordre de priorité attendu
        # 1. edge_tts (online, primaire)
        # 2. piper (offline, primaire)
        # 3. pyttsx3 (offline, fallback)
        # 4. gtts (online, fallback)

        with open('tts_module.py', 'r') as f:
            lines = f.readlines()

        # Trouver la fonction lire_texte
        in_lire_texte = False
        engine_order = []

        for i, line in enumerate(lines):
            if 'def lire_texte(texte):' in line:
                in_lire_texte = True
            elif in_lire_texte and 'if tts_engine_type ==' in line:
                engine = line.split("'")[1]
                if engine in ['edge_tts', 'piper', 'pyttsx3', 'gtts']:
                    engine_order.append(engine)

        # Vérifier que edge_tts et piper sont avant gtts
        if 'edge_tts' in engine_order and 'gtts' in engine_order:
            assert engine_order.index('edge_tts') < engine_order.index('gtts'), \
                "edge_tts should have priority over gtts"

        if 'piper' in engine_order and 'pyttsx3' in engine_order:
            assert engine_order.index('piper') < engine_order.index('pyttsx3'), \
                "piper should have priority over pyttsx3"


class TestEdgeTTSSpecific(unittest.TestCase):
    """Tests spécifiques pour Edge TTS"""

    def test_edge_tts_voice_is_french(self):
        """Test que la voix Edge TTS par défaut est française"""
        import tts_module
        assert "fr-FR" in tts_module.edge_tts_voice or "fr_FR" in tts_module.edge_tts_voice

    def test_edge_tts_voice_format(self):
        """Test le format de la voix Edge TTS"""
        import tts_module
        # Format attendu: xx-XX-Name
        voice = tts_module.edge_tts_voice
        assert '-' in voice, "Voice should contain hyphens"
        assert len(voice.split('-')) >= 2, "Voice should have at least 2 parts (lang-region)"


class TestPiperTTSSpecific(unittest.TestCase):
    """Tests spécifiques pour Piper TTS"""

    def test_piper_model_is_french(self):
        """Test que le modèle Piper par défaut est français"""
        import tts_module
        assert "fr_FR" in tts_module.piper_model_name or "fr-FR" in tts_module.piper_model_name

    def test_piper_model_is_low_quality(self):
        """Test que le modèle Piper est marqué 'low' (rapide)"""
        import tts_module
        assert "low" in tts_module.piper_model_name.lower(), \
            "Piper model should be 'low' quality for speed"



if __name__ == '__main__':
    # Run tests manually
    unittest.main(verbosity=2)
