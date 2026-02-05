from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict
from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4


class TextOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    MIXED = "mixed"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    CORRECTED = "corrected"
    REJECTED = "rejected"


class OCRResult(BaseModel):
    """Raw OCR output from a single engine"""
    engine: str
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    orientation: TextOrientation
    bounding_boxes: Optional[List[Dict]] = None
    processing_time: float
    metadata: Dict = {}


class OCRConsensus(BaseModel):
    """Merged result from multiple OCR engines"""
    selected_text: str
    selected_engine: str
    all_results: List[OCRResult]
    consensus_score: float
    orientation: TextOrientation

    # Validation fields
    validation_status: ValidationStatus = ValidationStatus.PENDING
    corrected_text: Optional[str] = None
    user_notes: Optional[str] = None


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
    confidence: float = 1.0


class Flashcard(BaseModel):
    """Individual flashcard with validation support"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    front: str
    back_reading: str
    back_translation: str
    context: Optional[str] = None
    frequency_rank: Optional[int] = None
    notes: Optional[str] = None

    # Validation fields
    validation_status: ValidationStatus = ValidationStatus.PENDING
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    user_edited: bool = False


class ProcessingSession(BaseModel):
    """Track processing pipeline state"""
    session_id: UUID = Field(default_factory=uuid4)
    source_files: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    status: Literal["processing", "validating", "completed", "failed"] = "processing"
    page_extractions: List['PageExtraction'] = []
    flashcard_set: Optional['FlashcardSet'] = None


class PageExtraction(BaseModel):
    """Intermediate result per page"""
    page_number: int
    image_path: str
    ocr_consensus: OCRConsensus
    tokens: List[JapaneseToken]
    sentences: List[str]
    orientation: TextOrientation
    validation_status: ValidationStatus = ValidationStatus.PENDING


class FlashcardSet(BaseModel):
    """Complete set for export"""
    title: str
    description: Optional[str] = None
    cards: List[Flashcard]
    source_files: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict = {}

    def to_quizlet_csv(self) -> str:
        """Export as Quizlet-compatible CSV"""
        pass