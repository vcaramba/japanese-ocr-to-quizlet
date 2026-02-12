# Main pipeline orchestrator
from pathlib import Path
from typing import Optional

from extractors.easyocr_impl import EasyOCR
from extractors.tesseract_ocr import TesseractOCR
from extractors.text_extractor import TextExtractor
from models.data_models import FlashcardSet, ProcessingSession, Flashcard, SessionStatus, \
    TextOrientation
from transformers.japanese_tokenizers import JapaneseTokenizer
from transformers.translator import Translator


class FlashcardPipeline:
    def __init__(self, orientation_hint: Optional[TextOrientation] = None):
        self.orientation_hint = orientation_hint
        self.text_extractor = TextExtractor()
        self.ocr_engines = [TesseractOCR(), EasyOCR(), ...]

        self.tokenizer = JapaneseTokenizer("Fugashi")
        self.translator = Translator()

    def process_document(self, file_path: str) -> ProcessingSession:
        """Main entry point"""
        file_path = Path(file_path)

        # Create session
        session = ProcessingSession(
            source_files=[str(file_path)],
            status=SessionStatus.PROCESSING
        )

        # Check file type
        if file_path.suffix.lower() == '.pdf':
            pages = self.text_extractor.process_pdf(file_path)
        else:
            # Single image
            ocr_results = [
                self.text_extractor.get_chars_from_image(str(file_path), self.orientation_hint)]
            pages = []

        session.page_extractions = pages
        session.status = SessionStatus.VALIDATING

        return session

    def generate_flashcards(
            self,
            session: ProcessingSession,
            include_context: bool = True,
            skip_duplicates: bool = True
    ) -> FlashcardSet:
        """
        Generate flashcards from processed session

        Args:
            session: ProcessingSession with extracted text
            include_context: Include example sentences
            skip_duplicates: Remove duplicate cards

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
            if skip_duplicates and token.surface in seen_surfaces:
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
        session.status = SessionStatus.COMPLETED

        return flashcard_set
