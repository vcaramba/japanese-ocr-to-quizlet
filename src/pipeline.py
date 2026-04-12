# Main pipeline orchestrator
from pathlib import Path
import os
from typing import List, Optional

from extractors.text_extractor import TextExtractor
from models.data_models import ExtractionMethod, FlashcardSet, PageExtraction, ProcessingSession, Flashcard, RawPageExtraction, SessionStatus, \
    TextOrientation
from src.transformers.japanese_tokenizer import JapaneseTokenizer
from src.transformers.translator import Translator
from src.transformers.text_cleaner import TextCleaner


class FlashcardPipeline:
    def __init__(self, ocr_engines: Optional[List[str]] = None, orientation_hint: Optional[TextOrientation] = None, deepl_api_key: Optional[str] = None):
        self.ocr_engines = ocr_engines
        self.orientation_hint = orientation_hint
        self.text_extractor = TextExtractor(self.orientation_hint)
        self.text_cleaner = TextCleaner()
        self.tokenizer = JapaneseTokenizer()
        self.translator = Translator(deepl_api_key)

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
            raw_pages = self.text_extractor.get_text_from_pdf(file_path)
            pages = [self.process_extracted_text(raw_page) for raw_page in raw_pages]

        else:
            # Single image
            raw_pages = self.text_extractor.get_text_from_image(str(file_path))
            pages = [self.process_extracted_text(raw_page) for raw_page in raw_pages]

        session.page_extractions = pages
        session.status = SessionStatus.VALIDATING

        return session
    
    def process_extracted_text(
        self, raw_page_extraction: RawPageExtraction
    ) -> PageExtraction:
        """
        Process raw extracted text extracted directly from PDF
        
        Args:
            raw_page_extraction: RawPageExtraction object containing the extracted text and metadata
            
        Returns:
            PageExtraction object
        """
        # Clean text
        cleaned_text = self.text_cleaner.clean(raw_page_extraction.raw_text)
        
        # Detect orientation
        orientation = self.text_cleaner.detect_orientation(cleaned_text)
        
        # Tokenize
        tokens = self.tokenizer.tokenize(cleaned_text)
        
        # Get sentences (TODO: should this be done before tokenization?)
        sentences = self.text_cleaner.get_sentences(cleaned_text)
        
        return PageExtraction(
            page_number=raw_page_extraction.page_number,
            image_path=raw_page_extraction.image_path,
            extraction_method=ExtractionMethod.PDF_TEXT_LAYER,
            ocr_consensus=None,  # No OCR was used
            raw_text=cleaned_text,
            tokens=tokens,
            sentences=sentences,
            orientation=orientation
        )
    
    

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
