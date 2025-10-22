"""
Module d'optimisation du traitement des commandes avec Numba JIT
Contient les fonctions de matching et de classification optimisées pour Whisp Assistant
"""
import numpy as np
from numba import jit, prange, float64, int32, boolean
import re
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

# Patterns de commandes optimisés
COMMAND_PATTERNS = {
    'system': ['éteins', 'redémarre', 'verrouille', 'veille', 'reboot', 'shutdown'],
    'browser': ['ouvre', 'ferme', 'nouvel onglet', 'onglet suivant', 'onglet précédent'],
    'development': ['git', 'code', 'compile', 'test', 'debug', 'deploy'],
    'productivity': ['note', 'rappel', 'timer', 'agenda', 'email'],
    'accessibility': ['loupe', 'lecteur', 'contraste', 'zoom', 'voix off'],
    'media': ['musique', 'video', 'pause', 'play', 'volume', 'mute'],
    'files': ['fichier', 'dossier', 'ouvre le fichier', 'crée un dossier', 'supprime'],
    'help': ['aide', 'comment', 'aide-moi', 'explication', 'tuto']
}

@jit(nopython=True, cache=True, fastmath=True)
def pattern_match_score_numba(text_words: np.ndarray, pattern_words: np.ndarray) -> float64:
    """
    Calcule un score de matching entre un texte et un pattern (optimisé Numba).

    Args:
        text_words: Array de mots du texte (en codes numériques)
        pattern_words: Array de mots du pattern (en codes numériques)

    Returns:
        Score de matching entre 0 et 1
    """
    if len(text_words) == 0 or len(pattern_words) == 0:
        return 0.0

    # Calcul des correspondances
    matches = 0
    for pattern_word in pattern_words:
        for text_word in text_words:
            if pattern_word == text_word:
                matches += 1
                break  # Éviter les doubles comptages

    # Score basé sur le nombre de correspondances
    score = float64(matches) / len(pattern_words)

    # Bonus pour l'ordre des mots
    order_bonus = 0.0
    if len(text_words) >= len(pattern_words):
        for i in range(len(pattern_words)):
            if i < len(text_words) and pattern_words[i] == text_words[i]:
                order_bonus += 0.1

    return min(1.0, score + order_bonus)

@jit(nopython=True, cache=True, fastmath=True, parallel=True)
def classify_command_numba(text_words: np.ndarray, pattern_matrix: np.ndarray, pattern_labels: np.ndarray) -> Tuple[int32, float64]:
    """
    Classification de commande optimisée avec Numba en parallèle.

    Args:
        text_words: Array de mots de la commande
        pattern_matrix: Matrice des patterns de commandes
        pattern_labels: Labels des catégories de commandes

    Returns:
        Tuple (index_best_pattern, best_score)
    """
    n_patterns = pattern_matrix.shape[0]
    best_score = 0.0
    best_pattern_idx = -1

    # Parallélisation de l'évaluation des patterns
    scores = np.zeros(n_patterns, dtype=np.float64)

    for i in prange(n_patterns):
        pattern_words = pattern_matrix[i]
        scores[i] = pattern_match_score_numba(text_words, pattern_words)

    # Trouver le meilleur score
    for i in range(n_patterns):
        if scores[i] > best_score:
            best_score = scores[i]
            best_pattern_idx = i

    return int32(best_pattern_idx), float64(best_score)

@jit(nopython=True, cache=True, fastmath=True)
def text_to_numbers_numba(text: str, max_vocab_size: int = 10000) -> np.ndarray:
    """
    Convertit un texte en array de nombres pour Numba (optimisé).

    Args:
        text: Texte à convertir
        max_vocab_size: Taille maximale du vocabulaire

    Returns:
        Array de nombres représentant le texte
    """
    # Simulation de conversion (Numba ne peut pas utiliser les strings directement)
    # En pratique, cette fonction serait appelée avec des données pré-traitées
    words = text.lower().split()

    # Hash simple des mots en nombres
    numbers = np.zeros(len(words), dtype=np.int32)

    for i, word in enumerate(words):
        # Hash simple basé sur les codes ASCII
        hash_value = 0
        for char in word[:10]:  # Limiter pour éviter les dépassements
            hash_value = (hash_value * 31 + ord(char)) % max_vocab_size
        numbers[i] = hash_value

    return numbers

@jit(nopython=True, cache=True, fastmath=True)
def calculate_command_confidence_numba(text_words: np.ndarray, pattern_words: np.ndarray,
                                     min_words_match: int = 1) -> float64:
    """
    Calcule un score de confiance pour la reconnaissance de commande.

    Args:
        text_words: Mots de la commande reconnue
        pattern_words: Mots du pattern de référence
        min_words_match: Nombre minimum de mots à faire correspondre

    Returns:
        Score de confiance entre 0 et 1
    """
    if len(text_words) < min_words_match or len(pattern_words) == 0:
        return 0.0

    # Calcul des correspondances exactes
    exact_matches = 0
    partial_matches = 0

    for pattern_word in pattern_words:
        for text_word in text_words:
            if pattern_word == text_word:
                exact_matches += 1
                break
            # Correspondance partielle (contient)
            elif pattern_word != 0 and text_word != 0:
                # Simplification : utiliser une heuristique basique
                if abs(pattern_word - text_word) < 100:  # Similarité approximative
                    partial_matches += 0.5
                    break

    # Score pondéré
    total_matches = exact_matches + partial_matches
    base_score = total_matches / len(pattern_words)

    # Pénalité si trop peu de mots correspondent
    if exact_matches < min_words_match:
        base_score *= 0.5

    return min(1.0, base_score)

@jit(nopython=True, cache=True, fastmath=True, parallel=True)
def batch_command_classification_numba(commands_array: np.ndarray,
                                     pattern_matrix: np.ndarray,
                                     pattern_labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Classification en batch de plusieurs commandes (optimisée parallèle).

    Args:
        commands_array: Array de commandes à classifier
        pattern_matrix: Matrice des patterns
        pattern_labels: Labels des patterns

    Returns:
        Tuple (predictions_array, confidence_array)
    """
    n_commands = commands_array.shape[0]
    predictions = np.zeros(n_commands, dtype=np.int32)
    confidences = np.zeros(n_commands, dtype=np.float64)

    for i in prange(n_commands):
        command_words = commands_array[i]
        pattern_idx, confidence = classify_command_numba(command_words, pattern_matrix, pattern_labels)

        predictions[i] = pattern_idx
        confidences[i] = confidence

    return predictions, confidences

# Classe d'optimisation des commandes
class CommandOptimizer:
    """Classe principale pour l'optimisation du traitement des commandes avec Numba."""

    def __init__(self):
        self.enabled = True
        self.patterns_cache = {}
        self.performance_stats = {
            'classifications': 0,
            'cache_hits': 0,
            'processing_time_saved': 0.0
        }

        # Préparer les patterns pour Numba
        self._prepare_patterns()

    def _prepare_patterns(self):
        """Prépare les patterns de commandes pour l'optimisation Numba."""
        self.pattern_matrix = []
        self.pattern_labels = []
        self.pattern_names = []

        for category, patterns in COMMAND_PATTERNS.items():
            for pattern in patterns:
                # Convertir les patterns en arrays numériques
                pattern_numbers = text_to_numbers_numba(pattern)
                self.pattern_matrix.append(pattern_numbers)
                self.pattern_labels.append(hash(category) % 1000)  # Label numérique
                self.pattern_names.append(category)

        # Convertir en arrays Numba
        if self.pattern_matrix:
            # Padding pour avoir des matrices uniformes
            max_len = max(len(p) for p in self.pattern_matrix)
            padded_matrix = []

            for pattern in self.pattern_matrix:
                padded = np.zeros(max_len, dtype=np.int32)
                padded[:len(pattern)] = pattern
                padded_matrix.append(padded)

            self.pattern_matrix = np.array(padded_matrix)
            self.pattern_labels = np.array(self.pattern_labels)

    def classify_command(self, text: str, threshold: float = 0.3) -> Dict:
        """
        Classifie une commande vocale de manière optimisée.

        Args:
            text: Texte de la commande
            threshold: Seuil de confiance minimum

        Returns:
            Dictionnaire avec les résultats de classification
        """
        if not self.enabled:
            return self._fallback_classify(text, threshold)

        try:
            # Vérifier le cache
            cache_key = hash(text.lower())
            if cache_key in self.patterns_cache:
                self.performance_stats['cache_hits'] += 1
                return self.patterns_cache[cache_key]

            # Conversion en nombres pour Numba
            text_numbers = text_to_numbers_numba(text.lower())

            # Padding si nécessaire
            if len(self.pattern_matrix) > 0:
                max_len = self.pattern_matrix.shape[1]
                padded_text = np.zeros(max_len, dtype=np.int32)
                padded_text[:min(len(text_numbers), max_len)] = text_numbers[:min(len(text_numbers), max_len)]

                # Classification Numba
                pattern_idx, confidence = classify_command_numba(
                    padded_text, self.pattern_matrix, self.pattern_labels
                )

                # Résultats
                if pattern_idx >= 0 and pattern_idx < len(self.pattern_names):
                    category = self.pattern_names[pattern_idx]
                    result = {
                        'category': category,
                        'confidence': float(confidence),
                        'matched': confidence >= threshold,
                        'text': text,
                        'optimized': True
                    }

                    # Mettre en cache
                    self.patterns_cache[cache_key] = result
                    self.performance_stats['classifications'] += 1

                    return result

            # Fallback si problème
            return self._fallback_classify(text, threshold)

        except Exception as e:
            logger.warning(f"Erreur classification Numba: {e}")
            return self._fallback_classify(text, threshold)

    def _fallback_classify(self, text: str, threshold: float) -> Dict:
        """Méthode de secours pour la classification."""
        text_lower = text.lower()
        best_match = None
        best_score = 0.0

        for category, patterns in COMMAND_PATTERNS.items():
            for pattern in patterns:
                # Simple matching
                if pattern in text_lower:
                    score = len(pattern.split()) / len(text_lower.split())
                    if score > best_score:
                        best_score = score
                        best_match = category

        return {
            'category': best_match or 'unknown',
            'confidence': best_score,
            'matched': best_score >= threshold,
            'text': text,
            'optimized': False
        }

    def batch_classify(self, commands: List[str], threshold: float = 0.3) -> List[Dict]:
        """
        Classification en batch de plusieurs commandes.

        Args:
            commands: Liste des commandes à classifier
            threshold: Seuil de confiance

        Returns:
            Liste des résultats de classification
        """
        if not self.enabled or len(commands) == 0:
            return [self._fallback_classify(cmd, threshold) for cmd in commands]

        try:
            # Conversion en batch
            commands_numbers = []
            for cmd in commands:
                cmd_numbers = text_to_numbers_numba(cmd.lower())
                commands_numbers.append(cmd_numbers)

            # Padding
            if len(commands_numbers) > 0 and len(self.pattern_matrix) > 0:
                max_len = max(max(len(cmd), self.pattern_matrix.shape[1]) for cmd in commands_numbers)
                padded_commands = []

                for cmd_numbers in commands_numbers:
                    padded = np.zeros(max_len, dtype=np.int32)
                    padded[:min(len(cmd_numbers), max_len)] = cmd_numbers[:min(len(cmd_numbers), max_len)]
                    padded_commands.append(padded)

                commands_array = np.array(padded_commands)

                # Classification batch Numba
                predictions, confidences = batch_command_classification_numba(
                    commands_array, self.pattern_matrix, self.pattern_labels
                )

                # Conversion des résultats
                results = []
                for i, (pred_idx, conf) in enumerate(zip(predictions, confidences)):
                    if pred_idx >= 0 and pred_idx < len(self.pattern_names):
                        category = self.pattern_names[pred_idx]
                        results.append({
                            'category': category,
                            'confidence': float(conf),
                            'matched': conf >= threshold,
                            'text': commands[i],
                            'optimized': True
                        })
                    else:
                        results.append(self._fallback_classify(commands[i], threshold))

                return results

        except Exception as e:
            logger.warning(f"Erreur batch classification Numba: {e}")

        # Fallback
        return [self._fallback_classify(cmd, threshold) for cmd in commands]

    def get_performance_stats(self) -> Dict:
        """Retourne les statistiques de performance."""
        cache_hit_rate = 0.0
        if self.performance_stats['classifications'] > 0:
            cache_hit_rate = (self.performance_stats['cache_hits'] /
                            self.performance_stats['classifications']) * 100

        return {
            'enabled': self.enabled,
            'total_classifications': self.performance_stats['classifications'],
            'cache_hits': self.performance_stats['cache_hits'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'processing_time_saved': f"{self.performance_stats['processing_time_saved']:.2f}s",
            'patterns_loaded': len(self.pattern_names),
            'optimizations_available': [
                'pattern_match_score_numba',
                'classify_command_numba',
                'batch_command_classification_numba',
                'calculate_command_confidence_numba'
            ]
        }

# Instance globale pour l'optimisation des commandes
command_optimizer = CommandOptimizer()

# Fonctions pratiques pour l'utilisation dans d'autres modules
def classify_voice_command(text: str, threshold: float = 0.3) -> Dict:
    """Classifie une commande vocale."""
    return command_optimizer.classify_command(text, threshold)

def batch_classify_commands(commands: List[str], threshold: float = 0.3) -> List[Dict]:
    """Classifie plusieurs commandes en batch."""
    return command_optimizer.batch_classify(commands, threshold)

def get_command_performance_stats() -> Dict:
    """Retourne les statistiques de performance des commandes."""
    return command_optimizer.get_performance_stats()