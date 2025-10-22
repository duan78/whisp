"""
Module d'optimisation des performances audio avec Numba JIT
Contient les fonctions de traitement audio optimisées pour Whisp Assistant
"""
import numpy as np
from numba import jit, prange, float32, int32
import logging

logger = logging.getLogger(__name__)

# Optimisations Numba pour le traitement audio
@jit(nopython=True, cache=True, fastmath=True)
def normalize_audio_numba(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalise les données audio pour éviter les pics et optimiser la reconnaissance.

    Args:
        audio_data: Données audio brutes (numpy array)

    Returns:
        Données audio normalisées
    """
    if len(audio_data) == 0:
        return audio_data

    # Calcul du max et min de manière optimisée
    max_val = np.max(np.abs(audio_data))

    if max_val > 0:
        # Normalisation optimisée
        return audio_data / max_val
    else:
        return audio_data

@jit(nopython=True, cache=True, fastmath=True)
def apply_window_numba(audio_data: np.ndarray, window_type: str = 'hann') -> np.ndarray:
    """
    Applique une fenêtre de Hamming/Hann à l'audio pour réduire les artefacts.

    Args:
        audio_data: Données audio
        window_type: Type de fenêtre ('hann', 'hamming')

    Returns:
        Données audio avec fenêtrage appliqué
    """
    n = len(audio_data)
    if n == 0:
        return audio_data

    # Création de la fenêtre optimisée
    if window_type == 'hann':
        window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(n) / (n - 1)))
    else:  # hamming
        window = 0.54 - 0.46 * np.cos(2.0 * np.pi * np.arange(n) / (n - 1))

    return audio_data * window

@jit(nopython=True, cache=True, fastmath=True)
def reduce_noise_numba(audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
    """
    Réduction de bruit simple par seuillage optimisé.

    Args:
        audio_data: Données audio
        threshold: Seuil de détection du bruit

    Returns:
        Données audio avec bruit réduit
    """
    # Seuillage optimisé avec Numba
    audio_filtered = np.where(np.abs(audio_data) < threshold, 0.0, audio_data)
    return audio_filtered

@jit(nopython=True, cache=True, fastmath=True)
def calculate_rms_numba(audio_data: np.ndarray) -> float:
    """
    Calcule le RMS (Root Mean Square) de l'audio de manière optimisée.

    Args:
        audio_data: Données audio

    Returns:
        Valeur RMS
    """
    if len(audio_data) == 0:
        return 0.0

    return np.sqrt(np.mean(audio_data ** 2))

@jit(nopython=True, cache=True, fastmath=True)
def detect_silence_numba(audio_data: np.ndarray, threshold: float = 0.01, min_duration: int = 100) -> bool:
    """
    Détecte les silences dans l'audio de manière optimisée.

    Args:
        audio_data: Données audio
        threshold: Seuil de détection du silence
        min_duration: Durée minimale du silence en échantillons

    Returns:
        True si silence détecté
    """
    if len(audio_data) < min_duration:
        return False

    # Calcul RMS par fenêtres glissantes
    window_size = min(min_duration, len(audio_data))
    rms = calculate_rms_numba(audio_data[:window_size])

    return rms < threshold

@jit(nopython=True, cache=True, fastmath=True, parallel=True)
def resample_audio_numba(audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
    """
    Rééchantillonnage audio optimisé avec Numba.

    Args:
        audio_data: Données audio originales
        original_rate: Taux d'échantillonnage original
        target_rate: Taux d'échantillonnage cible

    Returns:
        Données audio rééchantillonnées
    """
    if original_rate == target_rate:
        return audio_data

    # Calcul du ratio de rééchantillonnage
    ratio = float32(target_rate) / float32(original_rate)
    new_length = int32(len(audio_data) * ratio)

    if new_length <= 0:
        return audio_data

    # Rééchantillonnage linéaire optimisé
    resampled = np.zeros(new_length, dtype=audio_data.dtype)

    for i in prange(new_length):
        original_index = i / ratio
        if original_index < len(audio_data) - 1:
            idx_low = int32(original_index)
            idx_high = idx_low + 1
            fraction = original_index - idx_low

            # Interpolation linéaire
            resampled[i] = (audio_data[idx_low] * (1.0 - fraction) +
                           audio_data[idx_high] * fraction)
        else:
            resampled[i] = audio_data[-1]

    return resampled

@jit(nopython=True, cache=True, fastmath=True)
def apply_high_pass_filter_numba(audio_data: np.ndarray, cutoff_freq: float = 80.0, sample_rate: float = 16000.0) -> np.ndarray:
    """
    Filtre passe-haut simple pour éliminer les basses fréquences (bruit de fond).

    Args:
        audio_data: Données audio
        cutoff_freq: Fréquence de coupure
        sample_rate: Taux d'échantillonnage

    Returns:
        Données audio filtrées
    """
    if len(audio_data) < 2:
        return audio_data

    # Calcul du coefficient du filtre
    RC = 1.0 / (2.0 * np.pi * cutoff_freq)
    dt = 1.0 / sample_rate
    alpha = dt / (RC + dt)

    # Application du filtre passe-haut
    filtered = np.zeros_like(audio_data)
    filtered[0] = audio_data[0]

    for i in range(1, len(audio_data)):
        filtered[i] = alpha * (filtered[i-1] + audio_data[i] - audio_data[i-1])

    return filtered

@jit(nopython=True, cache=True, fastmath=True)
def calculate_audio_features_numba(audio_data: np.ndarray, sample_rate: float = 16000.0) -> tuple:
    """
    Calcule des caractéristiques audio de manière optimisée.

    Args:
        audio_data: Données audio
        sample_rate: Taux d'échantillonnage

    Returns:
        Tuple (rms, zcr, spectral_centroid) caractéristiques audio
    """
    if len(audio_data) == 0:
        return (0.0, 0.0, 0.0)

    # RMS (Root Mean Square)
    rms = calculate_rms_numba(audio_data)

    # Zero Crossing Rate
    zcr = np.mean(np.abs(np.diff(np.sign(audio_data))))

    # Spectral centroid approximation (énergie pondérée)
    fft_data = np.fft.fft(audio_data)
    magnitude = np.abs(fft_data[:len(fft_data)//2])
    freqs = np.fft.fftfreq(len(audio_data), 1.0/sample_rate)[:len(fft_data)//2]

    if np.sum(magnitude) > 0:
        spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
    else:
        spectral_centroid = 0.0

    return (rms, zcr, spectral_centroid)

# Classe d'optimisation audio
class AudioOptimizer:
    """Classe principale pour l'optimisation des traitements audio avec Numba."""

    def __init__(self):
        self.enabled = True
        self.cache_hits = 0
        self.processing_time_saved = 0.0

    def process_audio_chunk(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Pipeline complet de traitement audio optimisé.

        Args:
            audio_data: Données audio brutes
            sample_rate: Taux d'échantillonnage

        Returns:
            Données audio traitées et optimisées
        """
        if not self.enabled or len(audio_data) == 0:
            return audio_data

        try:
            # Pipeline d'optimisation
            processed = audio_data.astype(np.float32)

            # 1. Normalisation
            processed = normalize_audio_numba(processed)

            # 2. Application fenêtre
            processed = apply_window_numba(processed, 'hann')

            # 3. Réduction de bruit
            processed = reduce_noise_numba(processed)

            # 4. Filtre passe-haut
            processed = apply_high_pass_filter_numba(processed, 80.0, sample_rate)

            return processed

        except Exception as e:
            logger.warning(f"Erreur optimisation audio: {e}")
            return audio_data

    def is_speech_detected(self, audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Détection optimisée de parole dans l'audio.

        Args:
            audio_data: Données audio
            threshold: Seuil de détection

        Returns:
            True si parole détectée
        """
        if not self.enabled or len(audio_data) == 0:
            return True  # Fallback safe

        try:
            # Détection par caractéristiques audio
            rms, zcr, _ = calculate_audio_features_numba(audio_data)

            # Logique de détection simplifiée mais efficace
            return (rms > threshold and
                   not detect_silence_numba(audio_data, threshold, 100))

        except Exception as e:
            logger.warning(f"Erreur détection parole: {e}")
            return True  # Fallback safe

    def get_performance_stats(self) -> dict:
        """Retourne les statistiques de performance."""
        return {
            'enabled': self.enabled,
            'cache_hits': self.cache_hits,
            'processing_time_saved': f"{self.processing_time_saved:.2f}s",
            'optimizations_available': [
                'normalize_audio_numba',
                'apply_window_numba',
                'reduce_noise_numba',
                'calculate_rms_numba',
                'detect_silence_numba',
                'resample_audio_numba',
                'apply_high_pass_filter_numba',
                'calculate_audio_features_numba'
            ]
        }

# Instance globale pour l'optimisation audio
audio_optimizer = AudioOptimizer()

def optimize_audio_processing(audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
    """
    Fonction pratique pour optimiser le traitement audio.

    Args:
        audio_data: Données audio à optimiser
        sample_rate: Taux d'échantillonnage

    Returns:
        Données audio optimisées
    """
    return audio_optimizer.process_audio_chunk(audio_data, sample_rate)

def is_speech_active(audio_data: np.ndarray, threshold: float = 0.01) -> bool:
    """
    Fonction pratique pour détecter la présence de parole.

    Args:
        audio_data: Données audio à analyser
        threshold: Seuil de détection

    Returns:
        True si parole active détectée
    """
    return audio_optimizer.is_speech_detected(audio_data, threshold)