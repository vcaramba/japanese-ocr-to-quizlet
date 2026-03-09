from pathlib import Path
from typing import List, Any

import pypdf
from pdf2image import convert_from_path

from extractors.easyocr_impl import EasyOCRImpl
from extractors.ocr_selector import OCRSelector
from extractors.tesseract_ocr import TesseractOCR
from models.data_models import PageExtraction, TextOrientation, ExtractionMethod, RawPageExtraction
from validators.characters_validator import contains_japanese


class TextExtractor:
    def __init__(self, text_orientation: TextOrientation):
        self.ocr_selector = OCRSelector()
        self.ocr_engines = [TesseractOCR(), EasyOCRImpl(), ...]
        self.orientation_hint = text_orientation

    def process_pdf(self, pdf_path: Path) -> List[RawPageExtraction]:
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
                if text and contains_japanese(text):
                    # Successfully extracted text from PDF
                    print(f"Page {page_num + 1}: Extracted text from PDF layer")

                    page_extraction = self.get_extracted_text(
                        text=text,
                        page_number=page_num,
                        source_path=str(pdf_path)
                    )
                    pages.append(page_extraction)
                else:
                    # No text layer or no Japanese text, use OCR
                    print(f"Page {page_num + 1}: No text layer, using OCR")
                    page_extraction = self.get_ocr_for_pdf_page(
                        pdf_path=pdf_path,
                        page_number=page_num)
                    pages.append(page_extraction)

        except Exception as e:
            print(f"Error reading PDF: {e}, falling back to OCR for all pages")
            # Fall back to OCR for entire PDF
            pages = self.get_ocr_for_pdf_pages(pdf_path)

        return pages

    def get_text_from_image(self, image_path: str, page_number: int) -> RawPageExtraction:

        """
                Process image with OCR

                Args:
                    image_path: Path to image

                Returns:
                    OCR result
                """
        # Run all OCR engines
        ocr_results = []
        for engine in self.ocr_engines:
            try:
                result = engine.extract(image_path, self.orientation_hint)
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
        # return ocr_results
        return RawPageExtraction(
            page_number=page_number,
            image_path=image_path,
            extraction_method=ExtractionMethod.OCR_IMAGE,
            ocr_consensus=consensus,
            raw_text=consensus.best_result.text,
            orientation=consensus.orientation
            # tokens=tokens,
            # sentences=sentences,
        )



    def get_temp_file_dir(self, page_number: int) -> str:
        temp_image_path = f"data/processing/temp_page_{page_number}.png"
        Path(temp_image_path).parent.mkdir(parents=True, exist_ok=True)
        return temp_image_path

    def get_extracted_images_path_from_pdf(self, pdf_path: Path, page_number: int):
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
        temp_image_path = self.get_temp_file_dir(page_number)
        images[0].save(temp_image_path)

        return temp_image_path

    def get_ocr_for_pdf_page(self,
                             pdf_path: Path,
                             page_number: int) -> RawPageExtraction:

        """
                Convert a single PDF page to image and run OCR

                Args:
                    pdf_path: Path to PDF
                    page_number: Page number (0-indexed)

                Returns:
                    RawPageExtraction object
                """
        temp_image_path = self.get_extracted_images_path_from_pdf(
            pdf_path=pdf_path, page_number=page_number)

        # Process image with OCR
        return self.get_text_from_image(temp_image_path, page_number)

    def get_ocr_for_pdf_pages(self, pdf_path: Path) -> List[RawPageExtraction]:
        """
               Convert entire PDF to images and run OCR on all pages

               Args:
                   pdf_path: Path to PDF

               Returns:
                   List of RawPageExtraction objects
               """
        # Convert all pages to images
        images = convert_from_path(str(pdf_path), dpi=300)

        ocr_results = []
        for page_num, image in enumerate(images):
            # Save temporary image
            temp_image_path = self.get_temp_file_dir(page_num)
            image.save(temp_image_path)

            # Process with OCR
            ocr_results = self.get_text_from_image(temp_image_path, page_num)

        return ocr_results

    def get_extracted_text(
            self,
            text: str,
            page_number: int,
            source_path: str
    ) -> RawPageExtraction:
        """
        Process text extracted directly from PDF

        Args:
            text: Extracted text
            page_number: Page number
            source_path: Source file path

        Returns:
            PageExtraction object
        """
        # # Clean text
        # cleaned_text = self.text_cleaner.clean(text)
        #
        # # Detect orientation
        # orientation = self.text_cleaner.detect_orientation(cleaned_text)
        #
        # # Tokenize
        # tokens = self.tokenizer.tokenize(cleaned_text)
        #
        # # Get sentences
        # sentences = self.tokenizer.get_sentences(cleaned_text)

        return RawPageExtraction(
            page_number=page_number,
            image_path=source_path,
            extraction_method=ExtractionMethod.PDF_TEXT_LAYER,
            ocr_consensus=None,  # No OCR was used
            raw_text=text
        )
