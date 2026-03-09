"""
EasyOCR implementation
"""

import easyocr
from PIL import Image
import numpy as np
from typing import Optional

from extractors.base_ocr import BaseOCR
from models.data_models import TextOrientation, TextLanguage


class EasyOCRImpl(BaseOCR):
    """EasyOCR engine implementation"""

    def __init__(self, use_gpu: bool = False):
        """
        Initialize EasyOCR

        Args:
            use_gpu: Whether to use GPU acceleration
        """
        super().__init__("easyocr")
        self.use_gpu = use_gpu

        # Initialize reader with Japanese and English
        # First run will download models (~200MB)
        self.reader = easyocr.Reader(
            ['ja', 'en'],
            gpu=use_gpu,
            verbose=False
        )

    def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """
        Extract text using EasyOCR

        Args:
            image: PIL Image

        Returns:
            Tuple of (text, confidence)
        """
        # Convert PIL Image to numpy array
        image_np = np.array(image)

        # Perform OCR
        results = self.reader.readtext(image_np)

        if not results:
            return "", 0.0

        # Extract text and confidences
        texts = []
        confidences = []

        for (bbox, text, confidence) in results:
            texts.append(text)
            confidences.append(confidence)

        # Join texts with newlines
        full_text = '\n'.join(texts)

        # Calculate average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return full_text.strip(), avg_confidence

    def supports_language(self, language: str) -> bool:
        """Check if EasyOCR supports the language"""
        all_languages = list(map(str, TextLanguage))
        return language in all_languages