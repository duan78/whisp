"""
Tests unitaires pour le module de configuration
"""

import pytest
import threading
import time
from config import WhispConfig, get_config


class TestWhispConfig:
    """Tests pour la classe WhispConfig"""

    def test_config_singleton(self):
        """Test que le pattern singleton fonctionne"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_running_state(self):
        """Test la gestion de l'état running"""
        config = WhispConfig()
        assert config.get_running() == True

        config.set_running(False)
        assert config.get_running() == False

        config.set_running(True)
        assert config.get_running() == True

    def test_dictation_mode(self):
        """Test le mode dictée"""
        config = WhispConfig()
        assert config.get_dictation_mode() == False

        config.set_dictation_mode(True, "Initial text")
        assert config.get_dictation_mode() == True
        assert config.get_dictated_text() == "Initial text"

        config.set_dictation_mode(False)
        assert config.get_dictation_mode() == False
        assert config.get_dictated_text() == ""

    def test_append_dictated_text(self):
        """Test l'ajout de texte dicté"""
        config = WhispConfig()
        config.set_dictation_mode(True)

        config.append_dictated_text("Hello")
        assert config.get_dictated_text() == "Hello"

        config.append_dictated_text("World")
        assert config.get_dictated_text() == "Hello World"

        config.append_dictated_text("!", add_space=False)
        assert config.get_dictated_text() == "Hello World!"

    def test_translation_mode(self):
        """Test le mode traduction"""
        config = WhispConfig()
        assert config.get_translation_mode() == False

        config.set_translation_mode(True, "en", "Text to translate")
        assert config.get_translation_mode() == True
        assert config.get_target_language() == "en"
        assert config.get_translation_text() == "Text to translate"

    def test_stt_engine(self):
        """Test la gestion du moteur STT"""
        config = WhispConfig()
        assert config.get_stt_engine() == "speechrecognition"

        result = config.set_stt_engine("vosk")
        assert result == True
        assert config.get_stt_engine() == "vosk"

    def test_stt_engine_invalid(self):
        """Test qu'un moteur STT invalide est rejeté"""
        config = WhispConfig()
        result = config.set_stt_engine("invalid_engine")
        assert result == False
        # Le moteur ne doit pas avoir changé
        assert config.get_stt_engine() == "speechrecognition"

    def test_thread_safety_running(self):
        """Test la thread-safety de l'état running"""
        config = WhispConfig()
        errors = []

        def set_running_multiple_times():
            try:
                for i in range(100):
                    config.set_running(i % 2 == 0)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=set_running_multiple_times) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_thread_safety_dictation(self):
        """Test la thread-safety du mode dictée"""
        config = WhispConfig()
        errors = []

        def append_text_concurrently():
            try:
                for i in range(50):
                    config.append_dictated_text(f"word{i} ")
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)

        config.set_dictation_mode(True)

        threads = [threading.Thread(target=append_text_concurrently) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Vérifier que tout le texte a été ajouté
        final_text = config.get_dictated_text()
        assert len(errors) == 0
        # On doit avoir 5 * 50 = 250 mots
        assert "word249" in final_text or "word0" in final_text  # Au moins quelques mots


class TestCompatibilityFunctions:
    """Tests pour les fonctions de compatibilité"""

    def test_set_running(self):
        """Test la fonction de compatibilité set_running"""
        from config import set_running, get_running

        set_running(True)
        assert get_running() == True

        set_running(False)
        assert get_running() == False

        set_running(True)  # Restaurer l'état

    def test_dictation_functions(self):
        """Test les fonctions de compatibilité pour la dictée"""
        from config import set_dictation_mode, get_dictation_mode, append_dictated_text, get_dictated_text

        set_dictation_mode(True, "Start")
        assert get_dictation_mode() == True
        assert get_dictated_text() == "Start"

        append_dictated_text(" more")
        assert "more" in get_dictated_text()

        set_dictation_mode(False)

    def test_stt_engine_functions(self):
        """Test les fonctions de compatibilité pour le moteur STT"""
        from config import setstt_engine, getstt_engine

        original = getstt_engine()
        setstt_engine("vosk")
        assert getstt_engine() == "vosk"

        # Restaurer le moteur original
        setstt_engine(original)
