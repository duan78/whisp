#!/usr/bin/env python3
"""
Script de test pour valider les optimisations Numba dans Whisp Assistant
Teste les gains de performance et la compatibilité des modules optimisés
"""

import time
import numpy as np
import sys
import traceback
from typing import List, Dict
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_audio_optimization():
    """Test les optimisations de traitement audio."""
    print("\n" + "="*60)
    print("🎤 TEST DES OPTIMISATIONS AUDIO (NUMBA)")
    print("="*60)

    try:
        from audio_optimization import (
            normalize_audio_numba,
            apply_window_numba,
            reduce_noise_numba,
            calculate_rms_numba,
            detect_silence_numba,
            audio_optimizer
        )

        # Génération de données audio test
        print("📊 Génération des données audio de test...")
        sample_rates = [16000, 22050, 44100]
        durations = [1.0, 2.0, 5.0]  # secondes

        results = {}

        for sample_rate in sample_rates:
            for duration in durations:
                n_samples = int(sample_rate * duration)

                # Audio signal with noise
                audio_data = np.random.randn(n_samples).astype(np.float32)
                audio_data += 0.1 * np.random.randn(n_samples).astype(np.float32)  # Add noise

                print(f"\n🔍 Test: {sample_rate}Hz, {duration}s ({n_samples} samples)")

                # Test 1: Normalisation
                start_time = time.time()
                normalized = normalize_audio_numba(audio_data)
                norm_time = time.time() - start_time
                print(f"   ✅ Normalisation: {norm_time:.4f}s")

                # Test 2: Fenêtrage
                start_time = time.time()
                windowed = apply_window_numba(audio_data, 'hann')
                window_time = time.time() - start_time
                print(f"   ✅ Fenêtrage: {window_time:.4f}s")

                # Test 3: Réduction de bruit
                start_time = time.time()
                denoised = reduce_noise_numba(audio_data)
                denoise_time = time.time() - start_time
                print(f"   ✅ Réduction bruit: {denoise_time:.4f}s")

                # Test 4: Calcul RMS
                start_time = time.time()
                rms = calculate_rms_numba(audio_data)
                rms_time = time.time() - start_time
                print(f"   ✅ Calcul RMS: {rms_time:.4f}s (valeur: {rms:.6f})")

                # Test 5: Détection de silence
                start_time = time.time()
                is_silence = detect_silence_numba(audio_data, threshold=0.01)
                silence_time = time.time() - start_time
                print(f"   ✅ Détection silence: {silence_time:.4f}s (résultat: {is_silence})")

                # Test 6: Pipeline complet
                start_time = time.time()
                processed = audio_optimizer.process_audio_chunk(audio_data, sample_rate)
                pipeline_time = time.time() - start_time
                print(f"   ✅ Pipeline complet: {pipeline_time:.4f}s")

                # Stockage des résultats
                key = f"{sample_rate}Hz_{duration}s"
                results[key] = {
                    'samples': n_samples,
                    'normalization': norm_time,
                    'windowing': window_time,
                    'denoising': denoise_time,
                    'rms_calculation': rms_time,
                    'silence_detection': silence_time,
                    'pipeline': pipeline_time
                }

        # Test de performance par échantillon
        print(f"\n📈 Performance par échantillon:")
        for key, result in results.items():
            samples = result['samples']
            pipeline_ms = (result['pipeline'] * 1000) / samples * 1000  # ms per million samples
            print(f"   {key}: {pipeline_ms:.3f}ms/M échantillons")

        # Statistiques de l'optimiseur
        stats = audio_optimizer.get_performance_stats()
        print(f"\n📊 Statistiques de l'optimiseur audio:")
        for stat, value in stats.items():
            print(f"   {stat}: {value}")

        print(f"\n✅ Tests audio terminés avec succès!")
        return True

    except Exception as e:
        print(f"❌ Erreur dans les tests audio: {e}")
        traceback.print_exc()
        return False

def test_math_optimization():
    """Test les optimisations mathématiques."""
    print("\n" + "="*60)
    print("🧮 TEST DES OPTIMISATIONS MATHÉMATIQUES (NUMBA)")
    print("="*60)

    try:
        from math_optimization import (
            cosine_similarity_numba,
            fuzzy_match_score_numba,
            vectorize_text_simple,
            math_optimizer
        )

        # Données de test
        print("📊 Préparation des données de test...")

        # Textes pour les tests
        texts = [
            "ouvre google",
            "ouvre google chrome",
            "ouvre firefox",
            "ferme l'onglet",
            "nouvel onglet",
            "éteins l'ordinateur",
            "redémarre le système",
            "musique classique",
            "volume maximum",
            "aide assistance"
        ]

        # Tests de similarité cosinus
        print(f"\n🔍 Tests de similarité cosinus...")
        vec1 = vectorize_text_simple("ouvre google chrome")
        vec2 = vectorize_text_simple("ouvre firefox")

        start_time = time.time()
        similarity = cosine_similarity_numba(vec1, vec2)
        similarity_time = time.time() - start_time
        print(f"   ✅ Similarité cosinus: {similarity_time:.6f}s (score: {similarity:.4f})")

        # Tests de fuzzy matching
        print(f"\n🔍 Tests de recherche floue...")
        test_pairs = [
            ("ouvre google", "ouvre google chrome"),
            ("musique", "lecture de musique"),
            ("aide", "besoin d'aide"),
            ("éteins", "éteindre l'ordinateur")
        ]

        for pattern, text in test_pairs:
            start_time = time.time()
            score = fuzzy_match_score_numba(pattern, text)
            match_time = time.time() - start_time
            print(f"   ✅ '{pattern}' vs '{text}': {match_time:.6f}s (score: {score:.4f})")

        # Tests de l'optimiseur mathématique
        print(f"\n🔍 Tests de l'optimiseur mathématique...")

        # Test similarité textuelle
        start_time = time.time()
        similarity = math_optimizer.text_similarity("ouvre google", "ouvre google chrome")
        opt_time = time.time() - start_time
        print(f"   ✅ Similarité textuelle optimisée: {opt_time:.6f}s (score: {similarity:.4f})")

        # Test recherche floue
        start_time = time.time()
        matched, score = math_optimizer.fuzzy_match("musique", "jouer de la musique", 0.5)
        fuzzy_opt_time = time.time() - start_time
        print(f"   ✅ Recherche floue optimisée: {fuzzy_opt_time:.6f}s (match: {matched}, score: {score:.4f})")

        # Test statistiques textuelles
        test_text = "Ceci est un texte de test pour évaluer les performances de l'optimisation mathématique avec Numba."
        start_time = time.time()
        stats = math_optimizer.calculate_text_stats(test_text)
        stats_time = time.time() - start_time
        print(f"   ✅ Statistiques textuelles: {stats_time:.6f}s")
        print(f"      Mots: {stats['word_count']}, Phrases: {stats['sentence_count']}")
        print(f"      Longueur moyenne mot: {stats['avg_word_length']:.2f}")
        print(f"      Score complexité: {stats['complexity_score']:.3f}")

        # Statistiques de l'optimiseur
        stats = math_optimizer.get_performance_stats()
        print(f"\n📊 Statistiques de l'optimiseur mathématique:")
        for stat, value in stats.items():
            print(f"   {stat}: {value}")

        print(f"\n✅ Tests mathématiques terminés avec succès!")
        return True

    except Exception as e:
        print(f"❌ Erreur dans les tests mathématiques: {e}")
        traceback.print_exc()
        return False

def test_command_optimization():
    """Test les optimisations de traitement des commandes."""
    print("\n" + "="*60)
    print("⚡ TEST DES OPTIMISATIONS DE COMMANDES (NUMBA)")
    print("="*60)

    try:
        from command_optimization import (
            classify_voice_command,
            batch_classify_commands,
            get_command_performance_stats,
            command_optimizer
        )

        # Commandes de test
        test_commands = [
            "ouvre google chrome",
            "ferme l'onglet actuel",
            "éteins l'ordinateur",
            "nouvel onglet",
            "lance la musique",
            "aide-moi s'il te plaît",
            "crée un nouveau dossier",
            "augmente le volume",
            "veille l'ordinateur",
            "traduit ce texte en anglais"
        ]

        print(f"📊 Test de classification individuelle...")
        individual_times = []

        for cmd in test_commands:
            start_time = time.time()
            result = classify_voice_command(cmd, threshold=0.3)
            cmd_time = time.time() - start_time
            individual_times.append(cmd_time)

            print(f"   '{cmd}' -> {result['category']} (conf: {result['confidence']:.3f}, opt: {result['optimized']}) [{cmd_time:.6f}s]")

        # Test de classification en batch
        print(f"\n📊 Test de classification en batch ({len(test_commands)} commandes)...")
        start_time = time.time()
        batch_results = batch_classify_commands(test_commands, threshold=0.3)
        batch_time = time.time() - start_time

        print(f"   ✅ Batch total: {batch_time:.6f}s")
        print(f"   ✅ Moyenne par commande: {batch_time/len(test_commands):.6f}s")

        # Comparaison des performances
        avg_individual = sum(individual_times) / len(individual_times)
        speedup = avg_individual / (batch_time / len(test_commands)) if batch_time > 0 else 0

        print(f"\n📈 Comparaison des performances:")
        print(f"   Temps moyen individuel: {avg_individual:.6f}s")
        print(f"   Temps moyen batch: {batch_time/len(test_commands):.6f}s")
        print(f"   Speedup batch: {speedup:.2f}x")

        # Test de cache
        print(f"\n📊 Test du cache de patterns...")

        # Premier appel (cache miss)
        start_time = time.time()
        result1 = classify_voice_command("ouvre google chrome", threshold=0.3)
        first_time = time.time() - start_time

        # Deuxième appel identique (cache hit)
        start_time = time.time()
        result2 = classify_voice_command("ouvre google chrome", threshold=0.3)
        cached_time = time.time() - start_time

        cache_speedup = first_time / cached_time if cached_time > 0 else 0
        print(f"   ✅ Premier appel: {first_time:.6f}s")
        print(f"   ✅ Appel en cache: {cached_time:.6f}s")
        print(f"   ✅ Speedup cache: {cache_speedup:.2f}x")

        # Statistiques finales
        final_stats = get_command_performance_stats()
        print(f"\n📊 Statistiques finales de l'optimiseur de commandes:")
        for stat, value in final_stats.items():
            print(f"   {stat}: {value}")

        print(f"\n✅ Tests de commandes terminés avec succès!")
        return True

    except Exception as e:
        print(f"❌ Erreur dans les tests de commandes: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """Test d'intégration complet avec tous les modules Numba."""
    print("\n" + "="*60)
    print("🔗 TEST D'INTÉGRATION COMPLET")
    print("="*60)

    try:
        from audio_optimization import audio_optimizer
        from math_optimization import math_optimizer
        from command_optimization import command_optimizer

        # Vérifier que tous les optimiseurs sont activés
        all_enabled = (
            audio_optimizer.enabled and
            math_optimizer.enabled and
            command_optimizer.enabled
        )

        print(f"📊 État des optimiseurs:")
        print(f"   Audio: {'✅ Activé' if audio_optimizer.enabled else '❌ Désactivé'}")
        print(f"   Math: {'✅ Activé' if math_optimizer.enabled else '❌ Désactivé'}")
        print(f"   Commandes: {'✅ Activé' if command_optimizer.enabled else '❌ Désactivé'}")
        print(f"   Global: {'✅ Tous activés' if all_enabled else '⚠️ Certains désactivés'}")

        # Test complet simulé
        print(f"\n📊 Test de flux complet...")

        # 1. Simulation de réception audio
        audio_data = np.random.randn(16000).astype(np.float32)  # 1 seconde à 16kHz
        start_time = time.time()
        processed_audio = audio_optimizer.process_audio_chunk(audio_data)
        audio_time = time.time() - start_time

        # 2. Simulation de reconnaissance (texte simulé)
        recognized_text = "ouvre google chrome"
        start_time = time.time()
        command_result = classify_voice_command(recognized_text)
        command_time = time.time() - start_time

        # 3. Calcul de similarité avec des commandes connues
        start_time = time.time()
        similarity = math_optimizer.text_similarity(recognized_text, "ouvre un navigateur web")
        math_time = time.time() - start_time

        total_time = audio_time + command_time + math_time

        print(f"   ✅ Traitement audio: {audio_time:.6f}s")
        print(f"   ✅ Classification commande: {command_time:.6f}s")
        print(f"   ✅ Calcul similarité: {math_time:.6f}s")
        print(f"   ✅ Temps total: {total_time:.6f}s")

        # Vérification des seuils de performance
        performance_ok = total_time < 0.1  # Moins de 100ms pour le traitement complet
        print(f"\n📈 Performance: {'✅ Acceptable' if performance_ok else '⚠️ À améliorer'} (< 100ms)")

        return all_enabled and performance_ok

    except Exception as e:
        print(f"❌ Erreur dans le test d'intégration: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale des tests."""
    print("🚀 DÉMARRAGE DES TESTS DE PERFORMANCE NUMBA")
    print("Whisp Assistant - Optimisation JIT")
    print("="*60)

    # Vérifier la disponibilité de Numba
    try:
        import numba
        print(f"✅ Numba disponible: version {numba.__version__}")
    except ImportError:
        print("❌ Numba n'est pas installé. Installez-le avec: pip install numba")
        return False

    results = []

    # Exécution des tests
    tests = [
        ("Audio", test_audio_optimization),
        ("Mathématique", test_math_optimization),
        ("Commandes", test_command_optimization),
        ("Intégration", test_integration)
    ]

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Lancement du test {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print(f"Test {test_name}: {'✅ SUCCÈS' if result else '❌ ÉCHEC'}")

    # Résumé final
    print(f"\n{'='*60}")
    print("📋 RÉSUMÉ DES TESTS")
    print("="*60)

    success_count = 0
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"   {test_name}: {status}")
        if result:
            success_count += 1

    print(f"\n📊 Résultats globaux: {success_count}/{len(results)} tests réussis")

    if success_count == len(results):
        print("🎉 TOUS LES TESTS RÉUSSIS! Numba est correctement intégré.")
        print("💡 L'assistant devrait maintenant être plus performant.")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ. Vérifiez la configuration.")

    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)