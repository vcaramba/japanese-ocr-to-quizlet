# Main pipeline orchestrator
from results.extractors.easyocr_impl import EasyOCR
from results.extractors.ocr_selector import OCRSelector
from results.extractors.tesseract_ocr import TesseractOCR
from results.models.data_models import FlashcardSet, PageExtraction, ProcessingSession, Flashcard
from results.transformers.japanese_tokenizers import JapaneseTokenizer
from results.transformers.translator import Translator


class FlashcardPipeline:
    def __init__(self, config):
        self.ocr_engines = [TesseractOCR(), EasyOCR(), ...]
        self.selector = OCRSelector()
        self.tokenizer = JapaneseTokenizer("Fugashi")
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
            tokens = self.tokenizer.tokenize(consensus.selected_text)

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

    def generate_flashcards(
            self,
            session: ProcessingSession,
            include_context: bool = True,
            deduplicate: bool = True
    ) -> FlashcardSet:
        """
        Generate flashcards from processed session

        Args:
            session: ProcessingSession with extracted text
            include_context: Include example sentences
            deduplicate: Remove duplicate cards

        Returns:
            FlashcardSet ready for export
        """
        all_tokens = []
        token_contexts = {}  # Map token to sentence

        # Collect all tokens with context
        for page in session.page_extractions:
            for token in page.tokens:
                all_tokens.append(token)

                if include_context:
                    # Find sentence containing this token
                    for sentence in page.sentences:
                        if token.surface in sentence:
                            token_contexts[token.surface] = sentence
                            break

        # Filter tokens (only keep those with kanji for now)
        flashcard_tokens = [t for t in all_tokens if t.has_kanji]

        # Translate tokens
        print(f"Translating {len(flashcard_tokens)} tokens...")
        translations = self.translator.translate_tokens(flashcard_tokens)

        # Create flashcards
        cards = []
        seen_surfaces = set()

        for token, translation in zip(flashcard_tokens, translations):
            # Skip duplicates if requested
            if deduplicate and token.surface in seen_surfaces:
                continue

            seen_surfaces.add(token.surface)

            card = Flashcard(
                front=token.surface,
                back_reading=token.reading,
                back_translation=translation,
                context=token_contexts.get(token.surface),
                confidence_score=token.confidence
            )

            cards.append(card)

        # Create flashcard set
        flashcard_set = FlashcardSet(
            title=f"Flashcards from {', '.join(session.source_files)}",
            cards=cards,
            source_files=session.source_files
        )

        session.flashcard_set = flashcard_set
        session.status = "completed"

        return flashcard_set
