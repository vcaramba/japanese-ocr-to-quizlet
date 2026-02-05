from typing import List
from results.models.data_models import OCRResult, OCRConsensus


class OCRSelector:
    """
    Strategies:
    - Confidence voting: Highest average confidence
    - Character overlap: Most agreement on characters
    - Length heuristic: Penalize too short/long outputs
    - Ensemble: Merge results character-by-character
    """

    def select_best(self, results: List[OCRResult]) -> OCRConsensus:
        """Apply voting strategy to choose best OCR result"""
        pass

    def calculate_consensus(self, results: List[OCRResult]) -> float:
        """Measure agreement between engines"""
        pass