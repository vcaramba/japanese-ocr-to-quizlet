import difflib
from pathlib import Path
from typing import List, Optional

from pydantic import json

from models.data_models import OCRResult, OCRConsensus, TextOrientation, OCRSelectionStrategy


class OCRSelector:
    """
    Selects the best OCR result from multiple engines
    Can learn from user corrections over time
    Strategies:
    - Confidence voting: Highest average confidence
    - Character overlap: Most agreement on characters
    - Length heuristic: Penalize too short/long outputs
    - Ensemble: Merge results character-by-character
    """

    def __init__(self, weights_path: Optional[str] = None):
        """
        Initialize OCR Selector

        Args:
            weights_path: Path to saved engine weights/preferences
        """
        self.weights_path = weights_path
        self.engine_weights = self.load_weights()

    def load_weights(self) -> dict:
        """
        Load engine weights from file

        Returns:
            Dictionary of engine weights
        """
        if self.weights_path and Path(self.weights_path).exists():
            with open(self.weights_path, 'r') as f:
                return json.load(f)

        # Default weights (all equal initially)
        return {
            "tesseract": 1.0,
            "easyocr": 1.0,
            "manga_ocr": 1.2,  # Slight preference for manga_ocr for Japanese
        }

    def select_best(
            self,
            results: List[OCRResult],
            strategy: OCRSelectionStrategy = OCRSelectionStrategy.CONFIDENCE_WEIGHTED
    ) -> OCRConsensus:
        """
        Apply voting strategy to choose best result from multiple OCR engines

        Args:
            results: List of OCR results from different engines
            strategy: Selection strategy

        Returns:
            OCRConsensus with selected result
        """
        if not results:
            raise ValueError("No OCR results provided")

        if len(results) == 1:
            return OCRConsensus(
                selected_text=results[0].text,
                selected_engine=results[0].engine,
                all_results=results,
                consensus_score=results[0].confidence,
                orientation=results[0].orientation
            )

        if strategy == OCRSelectionStrategy.CONFIDENCE_WEIGHTED:
            selected = self.confidence_weighted_selection(results)
        elif strategy == OCRSelectionStrategy.MAJORITY_VOTE:
            selected = self.majority_vote_selection(results)
        elif strategy == OCRSelectionStrategy.MAJORITY_VOTE:
            selected = self.learned_selection(results)
        else:
            raise ValueError(f"Unknown strategy: {strategy.value}")

        # Calculate consensus score
        consensus_score = self.calculate_consensus(results)

        # Determine orientation (use most common)
        orientation = self.determine_orientation(results)

        return OCRConsensus(
            selected_text=selected.text,
            selected_engine=selected.engine,
            all_results=results,
            consensus_score=consensus_score,
            orientation=orientation
        )

    def confidence_weighted_selection(self, results: List[OCRResult]) -> OCRResult:
        """
        Select based on confidence scores weighted by engine performance

        Args:
            results: List of OCR results

        Returns:
            Best OCRResult
        """
        best_result = None
        best_score = -1

        for result in results:
            # Combine confidence with engine weight
            weight = self.engine_weights.get(result.engine, 1.0)
            score = result.confidence * weight

            if score > best_score:
                best_score = score
                best_result = result

        return best_result

    def majority_vote_selection(self, results: List[OCRResult]) -> OCRResult:
        """
        Select based on character-level agreement between engines

        Args:
            results: List of OCR results

        Returns:
            Best OCRResult
        """
        # Compare all pairs and find most similar
        similarity_scores = []

        for i, result in enumerate(results):
            total_similarity = 0
            for j, other in enumerate(results):
                if i != j:
                    similarity = difflib.SequenceMatcher(
                        None, result.text, other.text
                    ).ratio()
                    total_similarity += similarity

            avg_similarity = total_similarity / (len(results) - 1)
            similarity_scores.append((result, avg_similarity))

        # Return result with the highest average similarity
        return max(similarity_scores, key=lambda x: x[1])[0]

    def learned_selection(self, results: List[OCRResult]) -> OCRResult:
        """
        Select based on learned preferences from user corrections

        Args:
            results: List of OCR results

        Returns:
            Best OCRResult
        """
        # Similar to confidence_weighted but with more emphasis on learned weights
        best_result = None
        best_score = -1

        for result in results:
            weight = self.engine_weights.get(result.engine, 1.0)
            # Give more importance to learned weights
            score = (result.confidence * 0.3) + (weight * 0.7)

            if score > best_score:
                best_score = score
                best_result = result

        return best_result

    def calculate_consensus(self, results: List[OCRResult]) -> float:
        """
         Measure agreement between engines

        Args:
            results: List of OCR results

        Returns:
            Consensus score between 0 and 1
        """
        if len(results) < 2:
            return 1.0

        # Calculate pairwise similarity
        similarities = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                similarity = difflib.SequenceMatcher(
                    None, results[i].text, results[j].text
                ).ratio()
                similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def determine_orientation(self, results: List[OCRResult]) -> TextOrientation:
        """
        Determine text orientation based on majority vote

        Args:
            results: List of OCR results

        Returns:
            Most common orientation
        """
        orientations = [r.orientation for r in results]

        # Count occurrences
        from collections import Counter
        counts = Counter(orientations)

        # Return most common
        return counts.most_common(1)[0][0]

    def update_weights(self, engine: str, was_correct: bool):
        """
        Update engine weights based on user feedback

        Args:
            engine: Name of the engine
            was_correct: Whether the engine's result was correct
        """
        if engine not in self.engine_weights:
            self.engine_weights[engine] = 1.0

        # Adjust weight
        if was_correct:
            self.engine_weights[engine] *= 1.05  # Increase by 5%
        else:
            self.engine_weights[engine] *= 0.95  # Decrease by 5%

        # Keep weights in reasonable range
        self.engine_weights[engine] = max(0.1, min(2.0, self.engine_weights[engine]))

        # Save weights
        self._save_weights()

    def _save_weights(self):
        """Save engine weights to file"""
        if self.weights_path:
            Path(self.weights_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.weights_path, 'w') as f:
                json.dump(self.engine_weights, f, indent=2)
