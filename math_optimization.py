"""
Module d'optimisation des calculs mathématiques avec Numba JIT
Contient les fonctions de calcul optimisées pour Whisp Assistant
"""
import numpy as np
from numba import jit, prange, float64, int32, boolean
import re
import logging

logger = logging.getLogger(__name__)

# Optimisations Numba pour les calculs mathématiques et textuels

@jit(nopython=True, cache=True, fastmath=True)
def levenshtein_distance_numba(s1: str, s2: str) -> int:
    """
    Calcule la distance de Levenshtein entre deux chaînes (optimisée Numba).

    Note: Numba ne supporte pas directement les strings, donc cette fonction
    utilise des arrays de caractères numériques.
    """
    # Conversion des strings en arrays de codes ASCII
    # Note: Cette approche est limitée pour les caractères Unicode
    arr1 = np.array([ord(c) for c in s1], dtype=np.int32)
    arr2 = np.array([ord(c) for c in s2], dtype=np.int32)

    len1, len2 = len(arr1), len(arr2)

    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Initialisation de la matrice de distance
    distances = np.zeros((len1 + 1, len2 + 1), dtype=np.int32)

    for i in range(len1 + 1):
        distances[i, 0] = i
    for j in range(len2 + 1):
        distances[0, j] = j

    # Calcul des distances
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if arr1[i-1] == arr2[j-1] else 1
            distances[i, j] = min(
                distances[i-1, j] + 1,      # suppression
                distances[i, j-1] + 1,      # insertion
                distances[i-1, j-1] + cost  # substitution
            )

    return distances[len1, len2]

@jit(nopython=True, cache=True, fastmath=True)
def cosine_similarity_numba(vec1: np.ndarray, vec2: np.ndarray) -> float64:
    """
    Calcule la similarité cosinus entre deux vecteurs (optimisée Numba).
    """
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)

@jit(nopython=True, cache=True, fastmath=True)
def jaccard_similarity_numba(set1: np.ndarray, set2: np.ndarray) -> float64:
    """
    Calcule la similarité de Jaccard entre deux ensembles (optimisée Numba).
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0

    intersection = np.intersect1d(set1, set2)
    union = np.union1d(set1, set2)

    if len(union) == 0:
        return 0.0

    return len(intersection) / len(union)

@jit(nopython=True, cache=True, fastmath=True)
def vectorize_text_simple(text: str, vocab_size: int = 1000) -> np.ndarray:
    """
    Vectorisation simple de texte en utilisant les codes ASCII (optimisée Numba).

    Note: Version simplifiée pour démonstration. Pour la production,
    utiliser des embeddings pré-entraînés.
    """
    # Conversion en codes ASCII et limitation
    char_codes = np.array([min(ord(c), vocab_size-1) for c in text[:100]], dtype=np.int32)

    # Création du vecteur de fréquence
    vector = np.zeros(vocab_size, dtype=np.float32)

    for code in char_codes:
        if code < vocab_size:
            vector[code] += 1.0

    # Normalisation
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector

@jit(nopython=True, cache=True, fastmath=True)
def calculate_tf_idf_numba(terms: np.ndarray, doc_counts: np.ndarray, total_docs: int) -> np.ndarray:
    """
    Calcule les scores TF-IDF de manière optimisée.

    Args:
        terms: Array des termes et leurs fréquences
        doc_counts: Nombre de documents contenant chaque terme
        total_docs: Nombre total de documents

    Returns:
        Array des scores TF-IDF
    """
    if total_docs == 0 or len(terms) == 0:
        return np.zeros_like(terms, dtype=np.float64)

    # TF (Term Frequency)
    tf = terms.astype(np.float64)
    tf_norm = tf / np.sum(tf) if np.sum(tf) > 0 else tf

    # IDF (Inverse Document Frequency)
    idf = np.log(float64(total_docs) / (doc_counts + 1.0))

    # TF-IDF
    tfidf = tf_norm * idf

    return tfidf

@jit(nopython=True, cache=True, fastmath=True)
def fuzzy_match_score_numba(pattern: str, text: str) -> float64:
    """
    Calcule un score de correspondance floue (optimisé Numba).

    Args:
        pattern: Motif à rechercher
        text: Texte dans lequel chercher

    Returns:
        Score entre 0 et 1
    """
    if len(pattern) == 0:
        return 0.0
    if len(text) == 0:
        return 0.0

    # Distance de Levenshtein
    distance = levenshtein_distance_numba(pattern, text)
    max_len = max(len(pattern), len(text))

    # Normalisation du score
    similarity = 1.0 - (distance / max_len)

    # Bonus pour les correspondances de préfixe/suffixe
    prefix_bonus = 0.0
    suffix_bonus = 0.0

    min_len = min(len(pattern), len(text))
    for i in range(min_len):
        if pattern[i] == text[i]:
            prefix_bonus += 0.1
        else:
            break

    for i in range(1, min_len + 1):
        if pattern[-i] == text[-i]:
            suffix_bonus += 0.1
        else:
            break

    # Score final avec bonus
    final_score = min(1.0, similarity + prefix_bonus + suffix_bonus)

    return final_score

@jit(nopython=True, cache=True, fastmath=True, parallel=True)
def batch_similarity_numba(queries: np.ndarray, documents: np.ndarray) -> np.ndarray:
    """
    Calcule les similarités en parallèle entre requêtes et documents.

    Args:
        queries: Matrice des vecteurs de requêtes
        documents: Matrice des vecteurs de documents

    Returns:
        Matrice des similarités
    """
    n_queries = queries.shape[0]
    n_docs = documents.shape[0]

    similarities = np.zeros((n_queries, n_docs), dtype=np.float64)

    for i in prange(n_queries):
        for j in range(n_docs):
            similarities[i, j] = cosine_similarity_numba(queries[i], documents[j])

    return similarities

@jit(nopython=True, cache=True, fastmath=True)
def extract_keywords_numba(text_vector: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    """
    Extrait les mots-clés d'un vecteur de texte (optimisé Numba).

    Args:
        text_vector: Vecteur TF-IDF ou de fréquence
        threshold: Seuil pour considérer un terme comme mot-clé

    Returns:
        Indices des termes considérés comme mots-clés
    """
    keyword_indices = np.where(text_vector > threshold)[0]
    return keyword_indices

@jit(nopython=True, cache=True, fastmath=True)
def calculate_text_complexity_numba(word_lengths: np.ndarray, sentence_lengths: np.ndarray) -> float64:
    """
    Calcule un score de complexité textuelle (optimisé Numba).

    Args:
        word_lengths: Array des longueurs de mots
        sentence_lengths: Array des longueurs de phrases

    Returns:
        Score de complexité
    """
    if len(word_lengths) == 0 or len(sentence_lengths) == 0:
        return 0.0

    # Métriques de base
    avg_word_length = np.mean(word_lengths)
    avg_sentence_length = np.mean(sentence_lengths)

    # Variance (complexité)
    word_variance = np.var(word_lengths)
    sentence_variance = np.var(sentence_lengths)

    # Score de complexité combiné
    complexity_score = (avg_word_length * 0.3 +
                       avg_sentence_length * 0.4 +
                       word_variance * 0.15 +
                       sentence_variance * 0.15)

    return complexity_score

# Classe d'optimisation mathématique
class MathOptimizer:
    """Classe principale pour l'optimisation des calculs mathématiques avec Numba."""

    def __init__(self):
        self.enabled = True
        self.cache_hits = 0
        self.processing_time_saved = 0.0

    def text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes de manière optimisée.
        """
        if not self.enabled:
            return self._fallback_similarity(text1, text2)

        try:
            # Vectorisation simple
            vec1 = vectorize_text_simple(text1)
            vec2 = vectorize_text_simple(text2)

            # Similarité cosinus
            similarity = cosine_similarity_numba(vec1, vec2)
            return float(similarity)

        except Exception as e:
            logger.warning(f"Erreur calcul similarité Numba: {e}")
            return self._fallback_similarity(text1, text2)

    def fuzzy_match(self, pattern: str, text: str, threshold: float = 0.7) -> tuple:
        """
        Recherche floue optimisée.

        Returns:
            tuple (matched: bool, score: float)
        """
        if not self.enabled:
            return self._fallback_fuzzy_match(pattern, text, threshold)

        try:
            score = fuzzy_match_score_numba(pattern.lower(), text.lower())
            matched = score >= threshold
            return matched, float(score)

        except Exception as e:
            logger.warning(f"Erreur recherche floue Numba: {e}")
            return self._fallback_fuzzy_match(pattern, text, threshold)

    def calculate_text_stats(self, text: str) -> dict:
        """
        Calcule des statistiques textuelles optimisées.
        """
        if not self.enabled:
            return self._fallback_text_stats(text)

        try:
            # Extraction des longueurs
            words = text.split()
            sentences = [s.strip() for s in text.split('.') if s.strip()]

            word_lengths = np.array([len(word) for word in words], dtype=np.int32)
            sentence_lengths = np.array([len(sentence.split()) for sentence in sentences], dtype=np.int32)

            # Calculs optimisés
            complexity = calculate_text_complexity_numba(word_lengths, sentence_lengths)

            return {
                'word_count': len(words),
                'sentence_count': len(sentences),
                'avg_word_length': float(np.mean(word_lengths)) if len(word_lengths) > 0 else 0,
                'avg_sentence_length': float(np.mean(sentence_lengths)) if len(sentence_lengths) > 0 else 0,
                'complexity_score': float(complexity)
            }

        except Exception as e:
            logger.warning(f"Erreur statistiques textuelles Numba: {e}")
            return self._fallback_text_stats(text)

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        """Méthode de secours pour la similarité."""
        # Simple similarité par mots communs
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _fallback_fuzzy_match(self, pattern: str, text: str, threshold: float) -> tuple:
        """Méthode de secours pour la recherche floue."""
        pattern_lower = pattern.lower()
        text_lower = text.lower()

        # Recherche simple
        if pattern_lower in text_lower:
            return True, 1.0

        # Similarité par mots
        pattern_words = pattern_lower.split()
        text_words = text_lower.split()

        matches = sum(1 for word in pattern_words if word in text_words)
        score = matches / len(pattern_words) if pattern_words else 0.0

        return score >= threshold, score

    def _fallback_text_stats(self, text: str) -> dict:
        """Méthode de secours pour les statistiques textuelles."""
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        word_lengths = [len(word) for word in words]
        sentence_lengths = [len(sentence.split()) for sentence in sentences]

        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_word_length': sum(word_lengths) / len(word_lengths) if word_lengths else 0,
            'avg_sentence_length': sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0,
            'complexity_score': 0.0  # Non calculé en fallback
        }

    def get_performance_stats(self) -> dict:
        """Retourne les statistiques de performance."""
        return {
            'enabled': self.enabled,
            'cache_hits': self.cache_hits,
            'processing_time_saved': f"{self.processing_time_saved:.2f}s",
            'optimizations_available': [
                'levenshtein_distance_numba',
                'cosine_similarity_numba',
                'fuzzy_match_score_numba',
                'vectorize_text_simple',
                'calculate_tf_idf_numba',
                'batch_similarity_numba',
                'extract_keywords_numba',
                'calculate_text_complexity_numba'
            ]
        }

# Instance globale pour l'optimisation mathématique
math_optimizer = MathOptimizer()

# Fonctions pratiques pour l'utilisation dans d'autres modules
def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calcule la similarité entre deux textes."""
    return math_optimizer.text_similarity(text1, text2)

def fuzzy_search(pattern: str, text: str, threshold: float = 0.7) -> tuple:
    """Recherche floue dans un texte."""
    return math_optimizer.fuzzy_match(pattern, text, threshold)

def get_text_statistics(text: str) -> dict:
    """Calcule les statistiques d'un texte."""
    return math_optimizer.calculate_text_stats(text)