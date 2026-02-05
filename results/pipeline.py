# Main pipeline orchestrator
from results.extractors.easyocr_impl import EasyOCR
from results.extractors.ocr_selector import OCRSelector
from results.extractors.tesseract_ocr import TesseractOCR
from results.models.data_models import FlashcardSet, PageExtraction
from results.transformers.segmenter import Segmenter
from results.transformers.translator import Translator


class FlashcardPipeline:
    def __init__(self, config):
        self.ocr_engines = [TesseractOCR(), EasyOCR(), ...]
        self.selector = OCRSelector()
        self.segmenter = Segmenter()
        self.translator = Translator()

    def process_document(self, pdf_path: str) -> FlashcardSet:
        """Main entry point"""
        """TODO: handle case when input is a PDF, return detected text
        from a PDF if text layer is present"""
        pages = self.extract_images_from_pdf(pdf_path)
        extractions = []

        for page_num, image in enumerate(pages):
            # 1. Extract with all OCR engines
            ocr_results = [engine.extract(image) for engine in self.ocr_engines]

            # 2. Select best result
            consensus = self.selector.select_best(ocr_results)

            # 3. Transform text
            tokens = self.segmenter.segment(consensus.selected_text)

            extractions.append(PageExtraction(
                page_number=page_num,
                ocr_consensus=consensus,
                tokens=tokens
            ))

        # 4. Generate flashcards
        cards = self.generate_flashcards(extractions)

        # 5. Export
        return FlashcardSet(cards=cards)

    def extract_images_from_pdf(self, pdf_path):
        pass

    def generate_flashcards(self, extractions):
        pass
