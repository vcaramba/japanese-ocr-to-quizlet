"""
Abstract base class for OCR engines
All OCR implementations must inherit from this class
"""

from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
import time
from PIL import Image

from ..models.data_models import OCRResult, TextOrientation


class BaseOCR(ABC):
    """Abstract base class for OCR engines"""

    def __init__(self, name: str):
        """
        Initialize OCR engine

        Args:
            name: Name of the OCR engine
        """
        self.name = name

    @abstractmethod
    def _extract_text(self, image: Image.Image) -> tuple[str, float]:
        """
        Internal method to extract text from image
        Must be implemented by subclasses

        Args:
            image: PIL Image object

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        pass

    def extract(
            self,
            image_path: str,
            orientation_hint: Optional[TextOrientation] = None
    ) -> OCRResult:
        """
        Extract text from image

        Args:
            image_path: Path to image file
            orientation_hint: Optional hint about text orientation

        Returns:
            OCRResult with extracted text and metadata
        """
        start_time = time.time()

        # Load image
        image = Image.open(image_path)

        # Preprocess if needed
        image = self.preprocess_image(image, orientation_hint)

        # Extract text
        text, confidence = self._extract_text(image)

        # Detect orientation
        orientation = self.detect_orientation(text, orientation_hint)

        processing_time = time.time() - start_time

        return OCRResult(
            engine=self.name,
            text=text,
            confidence=confidence,
            orientation=orientation,
            processing_time=processing_time,
            metadata={
                "image_size": image.size,
                "image_mode": image.mode,
            }
        )

    def preprocess_image(
            self,
            image: Image.Image,
            orientation_hint: Optional[TextOrientation]
    ) -> Image.Image:
        """
        Preprocess image before OCR
        Can be overridden by subclasses

        Args:
            image: PIL Image
            orientation_hint: Optional orientation hint

        Returns:
            Preprocessed image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        return image

    def detect_orientation(
            self,
            text: str,
            orientation_hint: Optional[TextOrientation]
    ) -> TextOrientation:
        """
        Detect text orientation
        Can be overridden by subclasses for better detection

        Args:
            text: Extracted text
            orientation_hint: Optional hint

        Returns:
            Detected orientation
        """
        if orientation_hint:
            return orientation_hint

        # Simple heuristic: if text has newlines, likely vertical
        # More sophisticated detection can be added
        # TODO: detect tategaki other way; what about mixed orientation case?
        if text.count('\n') > len(text) / 20:
            return TextOrientation.VERTICAL

        return TextOrientation.HORIZONTAL

    def supports_language(self, language: str) -> bool:
        """
        Check if engine supports a language

        Args:
            language: Language code (e.g., 'ja', 'en')

        Returns:
            True if supported
        """
        return True  # Default: support all languages