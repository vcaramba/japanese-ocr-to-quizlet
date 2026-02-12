from pathlib import Path
from typing import List, Any

import pypdf

from extractors.easyocr_impl import EasyOCR
from extractors.ocr_selector import OCRSelector
from extractors.tesseract_ocr import TesseractOCR
from models.data_models import PageExtraction, TextOrientation
from pdf2image import convert_from_path


class TextExtractor:
    def __init__(self, text_orientation: TextOrientation):
        self.ocr_selector = OCRSelector()
        self.ocr_engines = [TesseractOCR(), EasyOCR(), ...]
        self.text_orientation = text_orientation

    def process_pdf(self, pdf_path: Path) -> List[PageExtraction]:
        """
               Process PDF file
               First tries to extract text layer, falls back to OCR if needed

               Args:
                   pdf_path: Path to PDF file

               Returns:
                   List of PageExtraction objects
               """
        pages = []

        # Try to extract text from PDF first
        try:
            reader = pypdf.PdfReader(str(pdf_path))

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()

                # Check if extracted text contains Japanese
                if text and self.contains_japanese(text):
                    # Successfully extracted text from PDF
                    print(f"Page {page_num + 1}: Extracted text from PDF layer")

                    page_extraction = self.process_extracted_text(
                        text=text,
                        page_number=page_num,
                        source_path=str(pdf_path)
                    )
                    pages.append(page_extraction)
                else:
                    # No text layer or no Japanese text, use OCR
                    print(f"Page {page_num + 1}: No text layer, using OCR")
                    page_extraction = self.process_pdf_page_with_ocr(
                        pdf_path=pdf_path,
                        page_number=page_num,
                        orientation_hint=self.text_orientation
                    )
                    pages.append(page_extraction)

        except Exception as e:
            print(f"Error reading PDF: {e}, falling back to OCR for all pages")
            # Fall back to OCR for entire PDF
            pages = self.process_pdf_with_ocr(pdf_path)

        return pages

    def get_chars_from_image(self, image_path: str, orientation_hint: TextOrientation) -> list[Any]:

        """
                Process image with OCR

                Args:
                    image_path: Path to image
                    orientation_hint: Page number
                    ocr_engines: list of OCR engines

                Returns:
                    OCR result
                """
        # Run all OCR engines
        ocr_results = []
        for engine in self.ocr_engines:
            try:
                result = engine.extract(image_path, orientation_hint)
                ocr_results.append(result)
                print(f"  {engine.name}: {result.confidence:.2%} confidence")
            except Exception as e:
                print(f"  {engine.name} failed: {e}")

        if not ocr_results:
            raise ValueError(f"All OCR engines failed for {image_path}")

        # Select best result
        consensus = self.ocr_selector.select_best(ocr_results)
        print(f"  Selected: {consensus.selected_engine} "
              f"(consensus: {consensus.consensus_score:.2%})")
        return ocr_results

    def extract_images_from_pdf(self, pdf_path):
        pass

    def contains_japanese(self, text: str) -> bool:
        """
        Check if text contains Japanese characters

        Args:
            text: Text to check

        Returns:
            True if contains Japanese
        """

        for char in text:
            # Check for hiragana, katakana, or kanji
            if '\u3040' <= char <= '\u30ff':  # Hiragana and Katakana
                return True
            if '\u4e00' <= char <= '\u9fff':  # Kanji
                return True
            if '\uff66' <= char <= '\uff9f':  # half-width Katakana
                return True

        return False

    def process_pdf_page_with_ocr(self,
                                  pdf_path: Path,
                                  page_number: int,
                                  orientation_hint: TextOrientation
                                  ) -> list[Any]:

        """
                Convert a single PDF page to image and run OCR

                Args:
                    pdf_path: Path to PDF
                    page_number: Page number (0-indexed)
                    orientation_hint: text orientation hint

                Returns:
                    PageExtraction object
                """
        # Convert page to image
        images = convert_from_path(
            str(pdf_path),
            first_page=page_number + 1,
            last_page=page_number + 1,
            dpi=300
        )

        if not images:
            raise ValueError(f"Could not convert page {page_number} to image")

        # Save temporary image
        temp_image_path = f"data/processing/temp_page_{page_number}.png"
        Path(temp_image_path).parent.mkdir(parents=True, exist_ok=True)
        images[0].save(temp_image_path)

        # Process image with OCR
        return self.get_chars_from_image(temp_image_path, orientation_hint)

    def process_pdf_with_ocr(self, pdf_path):
        pass
