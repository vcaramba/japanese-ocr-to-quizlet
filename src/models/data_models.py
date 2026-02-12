import csv
import io
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TextOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    MIXED = "mixed"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class ExtractionMethod(str, Enum):
    """Defines whether to extract text from PDF document or from image"""
    PDF_TEXT_LAYER = "pdf_text_layer"  # Direct text extraction from PDF
    OCR_IMAGE = "ocr_image"  # OCR performed on image
    OCR_PDF_CONVERTED = "ocr_pdf_converted"  # PDF converted to image then OCR


class OCRResult(BaseModel):
    """Raw OCR output from a single engine"""
    engine: str
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    orientation: TextOrientation
    bounding_boxes: Optional[List[Dict]] = None
    processing_time: float
    metadata: Dict[str, Any] = {}


class OCRConsensus(BaseModel):
    """Merged result from multiple OCR engines"""
    selected_text: str
    selected_engine: str
    all_results: List[OCRResult]
    consensus_score: float = Field(ge=0.0, le=1.0)
    orientation: TextOrientation

    # Validation fields
    validation_status: ValidationStatus = ValidationStatus.PENDING
    corrected_text: Optional[str] = None
    user_notes: Optional[str] = None


class OCRSelectionStrategy(str, Enum):
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    MAJORITY_VOTE = "majority_vote"
    LEARNED = "learned"


class TrainingExample(BaseModel):
    """Ground truth data for OCR improvement"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    image_path: str
    ground_truth_text: str
    orientation: TextOrientation
    source: str  # "tategaki_novel", "manga", etc.
    created_at: datetime = Field(default_factory=datetime.now)


class VocabularyEntry(BaseModel):
    """Validated vocabulary item"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    kanji: Optional[str] = None  # Can be None for pure kana words
    kana: str  # Hiragana/Katakana
    reading: str  # Hiragana reading
    translation: str  # English
    context: Optional[str] = None  # Example sentence
    frequency: Optional[int] = None
    tags: List[str] = []
    validated: bool = False


class JapaneseToken(BaseModel):
    """Segmented word/phrase with readings"""
    surface: str
    reading: str
    base_form: str
    pos: str
    has_kanji: bool
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class Flashcard(BaseModel):
    """Individual flashcard with validation support"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    front: str  # Kanji/Kana
    back_reading: str  # Hiragana reading
    back_translation: str  # English
    context: Optional[str] = None
    frequency_rank: Optional[int] = None
    notes: Optional[str] = None

    # Validation fields
    validation_status: ValidationStatus = ValidationStatus.PENDING
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    user_edited: bool = False


class SessionStatus(str, Enum):
    PROCESSING = "processing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingSession(BaseModel):
    """Track processing pipeline state"""
    session_id: UUID = Field(default_factory=uuid4)
    source_files: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.PROCESSING
    page_extractions: List['PageExtraction'] = []
    flashcard_set: Optional['FlashcardSet'] = None


class PageExtraction(BaseModel):
    """Intermediate result per page"""
    page_number: int
    image_path: str
    extraction_method: ExtractionMethod
    # OCR results (only if OCR was used)
    ocr_consensus: Optional[OCRConsensus] = None
    # Extracted text (from PDF text layer or OCR)
    raw_text: str

    tokens: List[JapaneseToken] = []
    sentences: List[str] = []
    orientation: TextOrientation
    validation_status: ValidationStatus = ValidationStatus.PENDING


class FlashcardSet(BaseModel):
    """Complete set for export"""
    title: str
    description: Optional[str] = None
    cards: List[Flashcard]
    source_files: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

    def to_quizlet_csv(self) -> str:
        """Export as Quizlet-compatible CSV"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Quizlet format: front, back (reading + translation)
        for card in self.cards:
            front = card.front
            back = f"{card.back_reading}\n{card.back_translation}"
            if card.context:
                back += f"\n例: {card.context}"
            writer.writerow([front, back])

        return output.getvalue()
