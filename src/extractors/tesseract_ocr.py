"""
Tesseract OCR implementation
"""

import pytesseract
from PIL import Image
from typing import Optional

from extractors.base_ocr import BaseOCR
from models.data_models import TextOrientation, TextLanguage


class TesseractOCR(BaseOCR):
    """Tesseract OCR engine implementation"""

    def __init__(self):
        super().__init__("tesseract")
        self.lang = "jpn"  # Japanese language

    def extract_text(self, image: Image.Image) -> tuple[str, float]:
        """
        Extract text using Tesseract

        Args:
            image: PIL Image

        Returns:
            Tuple of (text, confidence)
        """
        # Get detailed data for confidence calculation
        data = pytesseract.image_to_data(
            image,
            lang=self.lang,
            output_type=pytesseract.Output.DICT
        )

        # Extract text
        text = pytesseract.image_to_string(image, lang=self.lang)

        # Calculate average confidence
        confidences = [
            int(conf) for conf in data['conf']
            if conf != '-1'  # -1 means no text detected
        ]

        if confidences:
            avg_confidence = sum(confidences) / len(confidences) / 100.0
        else:
            avg_confidence = 0.0

        return text.strip(), avg_confidence

    def preprocess_image(
            self,
            image: Image.Image,
            orientation_hint: Optional[TextOrientation]
    ) -> Image.Image:
        """
        Preprocess image for better Tesseract results

        Args:
            image: Original image
            orientation_hint: Optional orientation hint

        Returns:
            Preprocessed image
        """
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Scale up small images (Tesseract works better with larger images)
        min_dimension = 1000
        width, height = image.size
        if width < min_dimension or height < min_dimension:
            scale_factor = min_dimension / min(width, height)
            new_size = (int(width * scale_factor), int(height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        return image

    def supports_language(self, language: str) -> bool:
        """Check if Tesseract supports the language"""
        # Tesseract supports Japanese if 'jpn' data is installed
        return language in TextLanguage.JAPANESE
