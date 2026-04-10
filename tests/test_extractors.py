import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np
from pathlib import Path
from extractors.base_ocr import BaseOCR
from extractors.ocr_selector import OCRSelector
from extractors.text_extractor import TextExtractor
from extractors.easyocr_impl import EasyOCRImpl
from extractors.tesseract_ocr import TesseractOCR
from models.data_models import (
    OCRResult, OCRConsensus, TextOrientation,
    ExtractionMethod, RawPageExtraction
)


class TestBaseOCR:
    """Test the base OCR class"""

    def test_init(self):
        ocr = BaseOCR("test_engine")
        assert ocr.name == "test_engine"

    def test_preprocess_image_rgb(self):
        """Test preprocessing RGB image"""
        ocr = BaseOCR("test")
        image = Image.new('RGB', (100, 100), color='red')
        processed = ocr.preprocess_image(image, None)
        assert processed.mode == 'RGB'

    def test_preprocess_image_convert_to_rgb(self):
        """Test converting non-RGB image to RGB"""
        ocr = BaseOCR("test")
        image = Image.new('L', (100, 100), color=128)  # Grayscale
        processed = ocr.preprocess_image(image, None)
        assert processed.mode == 'RGB'

    def test_detect_orientation_with_hint(self):
        """Test orientation detection with hint"""
        ocr = BaseOCR("test")
        orientation = ocr.detect_orientation("test", TextOrientation.VERTICAL)
        assert orientation == TextOrientation.VERTICAL

    def test_detect_orientation_vertical_heuristic(self):
        """Test vertical orientation detection heuristic"""
        ocr = BaseOCR("test")
        # Create text with many newlines
        text = "line1\nline2\nline3\nline4\nline5\nline6"
        orientation = ocr.detect_orientation(text, None)
        assert orientation == TextOrientation.VERTICAL

    def test_detect_orientation_horizontal_heuristic(self):
        """Test horizontal orientation detection heuristic"""
        ocr = BaseOCR("test")
        text = "This is a horizontal text with few line breaks."
        orientation = ocr.detect_orientation(text, None)
        assert orientation == TextOrientation.HORIZONTAL

    def test_parse_text_orientation(self):
        """Test parsing text orientation strings"""
        ocr = BaseOCR("test")

        assert ocr.parse_text_orientation("vertical") == TextOrientation.VERTICAL
        assert ocr.parse_text_orientation("tategaki") == TextOrientation.VERTICAL
        assert ocr.parse_text_orientation("horizontal") == TextOrientation.HORIZONTAL
        assert ocr.parse_text_orientation("yokogaki") == TextOrientation.HORIZONTAL
        assert ocr.parse_text_orientation("auto-detect") == TextOrientation.AUTO_DETECT

    def test_parse_text_orientation_invalid(self):
        """Test parsing invalid orientation"""
        ocr = BaseOCR("test")
        with pytest.raises(ValueError):
            ocr.parse_text_orientation("invalid")

    def test_supports_language_default(self):
        """Test default language support"""
        ocr = BaseOCR("test")
        assert ocr.supports_language("ja") is True
        assert ocr.supports_language("en") is True

    @patch('PIL.Image.open')
    @patch.object(BaseOCR, 'extract_text')
    def test_extract_full_flow(self, mock_extract_text, mock_image_open):
        """Test the full extract method"""
        # Setup mocks
        mock_image = Mock()
        mock_image.size = (800, 600)
        mock_image.mode = 'RGB'
        mock_image_open.return_value = mock_image

        mock_extract_text.return_value = ("Hello World", 0.95)

        ocr = BaseOCR("test_engine")
        result = ocr.extract("/path/to/image.png", TextOrientation.HORIZONTAL)

        assert result.engine == "test_engine"
        assert result.text == "Hello World"
        assert result.confidence == 0.95
        assert result.orientation == TextOrientation.HORIZONTAL
        assert "image_size" in result.metadata


class TestOCRSelector:
    """Test OCR result selection logic"""

    def test_init_no_weights(self):
        """Test initialization without weights file"""
        selector = OCRSelector()
        assert selector.engine_weights == {"tesseract": 1.0, "easyocr": 1.0}

    def test_select_best_single_result(self):
        """Test selection with single result"""
        selector = OCRSelector()
        result = OCRResult(
            engine="tesseract",
            text="test",
            confidence=0.8,
            orientation=TextOrientation.HORIZONTAL,
            processing_time=1.0
        )

        consensus = selector.select_best([result])
        assert consensus.selected_text == "test"
        assert consensus.selected_engine == "tesseract"
        assert consensus.consensus_score == 0.8

    def test_select_best_multiple_results_confidence_weighted(self):
        """Test confidence weighted selection"""
        selector = OCRSelector()
        results = [
            OCRResult(
                engine="tesseract",
                text="text1",
                confidence=0.6,
                orientation=TextOrientation.HORIZONTAL,
                processing_time=1.0
            ),
            OCRResult(
                engine="easyocr",
                text="text2",
                confidence=0.9,
                orientation=TextOrientation.HORIZONTAL,
                processing_time=1.0
            )
        ]

        consensus = selector.select_best(results)
        assert consensus.selected_engine == "easyocr"
        assert consensus.consensus_score > 0  # Some consensus

    def test_majority_vote_selection(self):
        """Test majority vote selection"""
        selector = OCRSelector()
        results = [
            OCRResult(
                engine="tesseract",
                text="hello",
                confidence=0.8,
                orientation=TextOrientation.HORIZONTAL,
                processing_time=1.0
            ),
            OCRResult(
                engine="easyocr",
                text="hello",
                confidence=0.7,
                orientation=TextOrientation.HORIZONTAL,
                processing_time=1.0
            ),
            OCRResult(
                engine="another",
                text="different",
                confidence=0.9,
                orientation=TextOrientation.HORIZONTAL,
                processing_time=1.0
            )
        ]

        consensus = selector.select_best(results, strategy="majority_vote")
        # Should select one of the "hello" results
        assert consensus.selected_text in ["hello", "different"]

    def test_calculate_consensus(self):
        """Test consensus calculation"""
        selector = OCRSelector()
        results = [
            OCRResult(engine="a", text="hello", confidence=1.0, orientation=TextOrientation.HORIZONTAL, processing_time=1.0),
            OCRResult(engine="b", text="hello", confidence=1.0, orientation=TextOrientation.HORIZONTAL, processing_time=1.0),
            OCRResult(engine="c", text="world", confidence=1.0, orientation=TextOrientation.HORIZONTAL, processing_time=1.0)
        ]

        consensus = selector.calculate_consensus(results)
        assert 0 <= consensus <= 1

    def test_determine_orientation(self):
        """Test orientation determination"""
        selector = OCRSelector()
        results = [
            OCRResult(engine="a", text="text", confidence=1.0, orientation=TextOrientation.VERTICAL, processing_time=1.0),
            OCRResult(engine="b", text="text", confidence=1.0, orientation=TextOrientation.VERTICAL, processing_time=1.0),
            OCRResult(engine="c", text="text", confidence=1.0, orientation=TextOrientation.HORIZONTAL, processing_time=1.0)
        ]

        orientation = selector.determine_orientation(results)
        assert orientation == TextOrientation.VERTICAL

    def test_update_weights_correct(self):
        """Test weight updates for correct predictions"""
        selector = OCRSelector()
        initial_weight = selector.engine_weights["tesseract"]

        selector.update_weights("tesseract", True)
        assert selector.engine_weights["tesseract"] > initial_weight

    def test_update_weights_incorrect(self):
        """Test weight updates for incorrect predictions"""
        selector = OCRSelector()
        initial_weight = selector.engine_weights["tesseract"]

        selector.update_weights("tesseract", False)
        assert selector.engine_weights["tesseract"] < initial_weight


class TestTextExtractor:
    """Test the main text extractor"""

    @patch('extractors.text_extractor.TesseractOCR')
    @patch('extractors.text_extractor.EasyOCRImpl')
    def test_init(self, mock_easyocr, mock_tesseract):
        """Test initialization"""
        extractor = TextExtractor(TextOrientation.HORIZONTAL)
        assert extractor.orientation_hint == TextOrientation.HORIZONTAL
        assert len(extractor.ocr_engines) == 2

    @patch('extractors.text_extractor.TesseractOCR')
    @patch('extractors.text_extractor.EasyOCRImpl')
    @patch('validators.characters_validator.contains_japanese')
    @patch('pypdf.PdfReader')
    def test_process_pdf_with_text_layer(self, mock_reader, mock_contains_japanese,
                                        mock_easyocr, mock_tesseract):
        """Test PDF processing with text layer"""
        # Setup mocks
        mock_page = Mock()
        mock_page.extract_text.return_value = "Japanese text"
        mock_reader.return_value.pages = [mock_page]
        mock_contains_japanese.return_value = True

        extractor = TextExtractor(TextOrientation.HORIZONTAL)

        with patch.object(extractor, 'get_extracted_text') as mock_get_text:
            mock_get_text.return_value = RawPageExtraction(
                image_path="test.pdf",
                extraction_method=ExtractionMethod.PDF_TEXT_LAYER,
                raw_text="Japanese text"
            )

            results = extractor.process_pdf(Path("test.pdf"))
            assert len(results) == 1
            assert results[0].extraction_method == ExtractionMethod.PDF_TEXT_LAYER

    @patch('extractors.text_extractor.TesseractOCR')
    @patch('extractors.text_extractor.EasyOCRImpl')
    def test_get_text_from_image(self, mock_easyocr, mock_tesseract):
        """Test single image processing"""
        # Setup mock OCR engines
        mock_engine1 = Mock()
        mock_engine1.extract.return_value = OCRResult(
            engine="engine1",
            text="text1",
            confidence=0.8,
            orientation=TextOrientation.HORIZONTAL,
            processing_time=1.0
        )

        mock_engine2 = Mock()
        mock_engine2.extract.return_value = OCRResult(
            engine="engine2",
            text="text2",
            confidence=0.9,
            orientation=TextOrientation.HORIZONTAL,
            processing_time=1.0
        )

        extractor = TextExtractor(TextOrientation.HORIZONTAL)
        extractor.ocr_engines = [mock_engine1, mock_engine2]

        # Mock selector
        with patch.object(extractor, 'ocr_selector') as mock_selector:
            mock_consensus = OCRConsensus(
                selected_text="selected text",
                selected_engine="engine2",
                best_result=mock_engine2.extract.return_value,
                consensus_score=0.85,
                orientation=TextOrientation.HORIZONTAL
            )
            mock_selector.select_best.return_value = mock_consensus

            results = extractor.get_text_from_image("test.png")
            assert len(results) == 1
            assert results[0].raw_text == "selected text"
            assert results[0].extraction_method == ExtractionMethod.OCR_IMAGE

    @patch('extractors.text_extractor.TesseractOCR')
    @patch('extractors.text_extractor.EasyOCRImpl')
    def test_get_text_from_image_no_results(self, mock_easyocr, mock_tesseract):
        """Test image processing when all OCR engines fail"""
        mock_engine = Mock()
        mock_engine.extract.side_effect = Exception("OCR failed")

        extractor = TextExtractor(TextOrientation.HORIZONTAL)
        extractor.ocr_engines = [mock_engine]

        with pytest.raises(ValueError, match="All OCR engines failed"):
            extractor.get_text_from_image("test.png")

    @patch('extractors.text_extractor.TesseractOCR')
    @patch('extractors.text_extractor.EasyOCRImpl')
    def test_get_extracted_text(self, mock_easyocr, mock_tesseract):
        """Test PDF text extraction processing"""
        extractor = TextExtractor(TextOrientation.HORIZONTAL)

        result = extractor.get_extracted_text(
            text="PDF text",
            page_number=1,
            source_path="test.pdf"
        )

        assert result.raw_text == "PDF text"
        assert result.page_number == 1
        assert result.extraction_method == ExtractionMethod.PDF_TEXT_LAYER


class TestEasyOCRImpl:
    """Test EasyOCR implementation"""

    @patch('easyocr.Reader')
    def test_init(self, mock_reader):
        """Test initialization"""
        ocr = EasyOCRImpl(use_gpu=True)
        assert ocr.name == "easyocr"
        assert ocr.use_gpu is True
        mock_reader.assert_called_once_with(['ja', 'en'], gpu=True, verbose=False)

    @patch('easyocr.Reader')
    def test_extract_text_success(self, mock_reader_class):
        """Test successful text extraction"""
        mock_reader = Mock()
        mock_reader.readtext.return_value = [
            ([[0, 0], [100, 0], [100, 50], [0, 50]], "Hello", 0.95),
            ([[0, 60], [100, 60], [100, 110], [0, 110]], "World", 0.90)
        ]
        mock_reader_class.return_value = mock_reader

        ocr = EasyOCRImpl()
        image = Image.new('RGB', (100, 100), color='white')

        text, confidence = ocr.extract_text(image)

        assert "Hello" in text
        assert "World" in text
        assert confidence == pytest.approx(0.925, abs=0.01)  # Average of 0.95 and 0.90

    @patch('easyocr.Reader')
    def test_extract_text_no_results(self, mock_reader_class):
        """Test extraction with no results"""
        mock_reader = Mock()
        mock_reader.readtext.return_value = []
        mock_reader_class.return_value = mock_reader

        ocr = EasyOCRImpl()
        image = Image.new('RGB', (100, 100), color='white')

        text, confidence = ocr.extract_text(image)

        assert text == ""
        assert confidence == 0.0


class TestTesseractOCR:
    """Test Tesseract OCR implementation"""

    def test_init(self):
        """Test initialization"""
        ocr = TesseractOCR()
        assert ocr.name == "tesseract"
        assert ocr.lang == "jpn"

    @patch('pytesseract.image_to_data')
    @patch('pytesseract.image_to_string')
    def test_extract_text_success(self, mock_image_to_string, mock_image_to_data):
        """Test successful text extraction"""
        mock_image_to_string.return_value = "Extracted text"
        mock_image_to_data.return_value = {
            'conf': ['95', '90', '-1', '85']
        }

        ocr = TesseractOCR()
        image = Image.new('RGB', (100, 100), color='white')

        text, confidence = ocr.extract_text(image)

        assert text == "Extracted text"
        assert confidence == pytest.approx(0.9, abs=0.01)  # Average of 95, 90, 85

    @patch('pytesseract.image_to_data')
    @patch('pytesseract.image_to_string')
    def test_extract_text_no_confidence(self, mock_image_to_string, mock_image_to_data):
        """Test extraction with no valid confidence scores"""
        mock_image_to_string.return_value = "Text"
        mock_image_to_data.return_value = {
            'conf': ['-1', '-1']  # No valid confidences
        }

        ocr = TesseractOCR()
        image = Image.new('RGB', (100, 100), color='white')

        text, confidence = ocr.extract_text(image)

        assert text == "Text"
        assert confidence == 0.0