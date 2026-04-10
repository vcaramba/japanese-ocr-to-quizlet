import pytest
from datetime import datetime
from uuid import uuid4
from models.data_models import (
    TextOrientation, ValidationStatus, ExtractionMethod,
    OCRResult, OCRConsensus, JapaneseToken, Flashcard,
    SessionStatus, ProcessingSession, RawPageExtraction,
    PageExtraction, FlashcardSet, TextLanguage
)


class TestEnums:
    def test_text_orientation_values(self):
        assert TextOrientation.HORIZONTAL == "horizontal"
        assert TextOrientation.VERTICAL == "vertical"
        assert TextOrientation.AUTO_DETECT == "auto_detect"

    def test_validation_status_values(self):
        assert ValidationStatus.PENDING == "pending"
        assert ValidationStatus.VALIDATED == "validated"
        assert ValidationStatus.CORRECTED == "corrected"
        assert ValidationStatus.REJECTED == "rejected"

    def test_extraction_method_values(self):
        assert ExtractionMethod.PDF_TEXT_LAYER == "pdf_text_layer"
        assert ExtractionMethod.OCR_IMAGE == "ocr_image"
        assert ExtractionMethod.OCR_PDF_CONVERTED == "ocr_pdf_converted"


class TestOCRResult:
    def test_valid_ocr_result(self):
        result = OCRResult(
            engine="Tesseract",
            text="こんにちは",
            confidence=0.85,
            orientation=TextOrientation.HORIZONTAL,
            processing_time=1.2,
            metadata={"version": "5.0"}
        )
        assert result.engine == "Tesseract"
        assert result.confidence == 0.85

    def test_invalid_confidence(self):
        with pytest.raises(ValueError):
            OCRResult(
                engine="EasyOCR",
                text="Hello",
                confidence=1.5,  # Invalid
                orientation=TextOrientation.HORIZONTAL,
                processing_time=0.8
            )


class TestOCRConsensus:
    def test_valid_consensus(self):
        best_result = OCRResult(
            engine="EasyOCR",
            text="こんにちは",
            confidence=0.9,
            orientation=TextOrientation.HORIZONTAL,
            processing_time=1.0
        )
        consensus = OCRConsensus(
            selected_text="こんにちは",
            selected_engine="EasyOCR",
            best_result=best_result,
            consensus_score=0.85,
            orientation=TextOrientation.HORIZONTAL
        )
        assert consensus.selected_engine == "EasyOCR"
        assert consensus.consensus_score == 0.85


class TestJapaneseToken:
    def test_valid_token(self):
        token = JapaneseToken(
            surface="こんにちは",
            reading="こんにちは",
            lemma="こんにちは",
            pos="greeting",
            has_kanji=False,
            confidence=0.95
        )
        assert token.surface == "こんにちは"
        assert token.has_kanji is False


class TestFlashcard:
    def test_valid_flashcard(self):
        card = Flashcard(
            front="今晩は",
            back_reading="こんばんは",
            back_translation="Good evening",
            context="Used for greeting",
            confidence_score=0.9
        )
        assert card.front == "今晩は"
        assert card.back_translation == "Good evening"
        assert card.validation_status == ValidationStatus.PENDING


class TestProcessingSession:
    def test_session_creation(self):
        session = ProcessingSession(
            source_files=["test.pdf"],
            status=SessionStatus.PROCESSING
        )
        assert len(session.source_files) == 1
        assert session.status == SessionStatus.PROCESSING
        assert isinstance(session.session_id, str)  # UUID as string

    def test_session_json_serialization(self):
        session = ProcessingSession(source_files=["test.png"])
        json_str = session.json()
        assert "test.png" in json_str
        assert "session_id" in json_str


class TestRawPageExtraction:
    def test_valid_raw_extraction(self):
        extraction = RawPageExtraction(
            image_path="/path/to/image.png",
            extraction_method=ExtractionMethod.OCR_IMAGE,
            raw_text="Extracted text",
            orientation=TextOrientation.VERTICAL
        )
        assert extraction.raw_text == "Extracted text"
        assert extraction.extraction_method == ExtractionMethod.OCR_IMAGE


class TestPageExtraction:
    def test_page_extraction_inheritance(self):
        extraction = PageExtraction(
            image_path="/path/to/image.png",
            extraction_method=ExtractionMethod.OCR_IMAGE,
            raw_text="Text",
            tokens=[],
            sentences=[]
        )
        assert isinstance(extraction, RawPageExtraction)
        assert extraction.validation_status == ValidationStatus.PENDING


class TestFlashcardSet:
    def test_flashcard_set_creation(self):
        card = Flashcard(
            front="猫",
            back_reading="ねこ",
            back_translation="Cat"
        )
        flashcard_set = FlashcardSet(
            title="Japanese Animals",
            cards=[card],
            source_files=["animals.pdf"]
        )
        assert flashcard_set.title == "Japanese Animals"
        assert len(flashcard_set.cards) == 1

    def test_to_quizlet_csv(self):
        card1 = Flashcard(
            front="犬",
            back_reading="いぬ",
            back_translation="Dog",
            context="A pet animal"
        )
        card2 = Flashcard(
            front="猫",
            back_reading="ねこ",
            back_translation="Cat"
        )
        flashcard_set = FlashcardSet(
            title="Animals",
            cards=[card1, card2],
            source_files=["test.pdf"]
        )
        csv_output = flashcard_set.to_quizlet_csv()
        lines = csv_output.strip().split('\n')
        assert len(lines) == 2
        assert "犬" in lines[0]
        assert "いぬ" in lines[0]
        assert "Dog" in lines[0]
        assert "A pet animal" in lines[0]
        assert "猫" in lines[1]


class TestTextLanguage:
    def test_language_values(self):
        assert TextLanguage.JAPANESE == ['ja', 'jpn', 'japanese']
        assert TextLanguage.ENGLISH == ['en', 'eng', 'english']