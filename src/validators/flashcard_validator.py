"""
Flashcard Validator Module
Provides validation and editing capabilities for flashcards
"""

from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
import json
from datetime import datetime
from collections import Counter

from models.data_models import (
    Flashcard,
    FlashcardSet,
    ValidationStatus,
    VocabularyEntry
)


class FlashcardValidator:
    """
    Validates and manages flashcard quality
    
    Features:
    - Duplicate detection and removal
    - Quality validation (completeness, formatting)
    - Manual editing support
    - Frequency-based filtering
    - Vocabulary database management
    - Export validation
    """
    
    def __init__(
        self,
        vocabulary_db_path: str = "data/training/vocabulary/validated.json",
        min_confidence: float = 0.5
    ):
        """
        Initialize flashcard validator
        
        Args:
            vocabulary_db_path: Path to validated vocabulary database
            min_confidence: Minimum confidence score for auto-validation
        """
        self.vocabulary_db_path = Path(vocabulary_db_path)
        self.vocabulary_db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.min_confidence = min_confidence
        
        # Load validated vocabulary
        self.validated_vocabulary = self.load_vocabulary_db()
    
    def validate_flashcard_set(
        self,
        flashcard_set: FlashcardSet,
        auto_validate: bool = True,
        remove_duplicates: bool = True
    ) -> Tuple[FlashcardSet, Dict]:
        """
        Validate entire flashcard set
        
        Args:
            flashcard_set: FlashcardSet to validate
            auto_validate: Auto-validate high-quality cards
            remove_duplicates: Remove duplicate cards
            
        Returns:
            Tuple of (validated FlashcardSet, validation report)
        """
        report = {
            "total_cards": len(flashcard_set.cards),
            "duplicates_removed": 0,
            "auto_validated": 0,
            "needs_review": 0,
            "issues": []
        }
        
        # Remove duplicates if requested
        if remove_duplicates:
            original_count = len(flashcard_set.cards)
            flashcard_set.cards = self.remove_duplicates(flashcard_set.cards)
            report["duplicates_removed"] = original_count - len(flashcard_set.cards)
        
        # Validate each card
        for card in flashcard_set.cards:
            # Check quality
            issues = self.validate_card(card)
            
            if issues:
                report["issues"].append({
                    "card_id": card.id,
                    "front": card.front,
                    "issues": issues
                })
                report["needs_review"] += 1
                card.validation_status = ValidationStatus.PENDING
            else:
                # Auto-validate if high confidence and no issues
                if auto_validate and card.confidence_score >= 0.8:
                    card.validation_status = ValidationStatus.VALIDATED
                    report["auto_validated"] += 1
                else:
                    card.validation_status = ValidationStatus.PENDING
                    report["needs_review"] += 1
        
        return flashcard_set, report
    
    def validate_card(self, card: Flashcard) -> List[str]:
        """
        Validate individual flashcard
        
        Args:
            card: Flashcard to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Check required fields
        if not card.front or not card.front.strip():
            issues.append("Missing front text")
        
        if not card.back_reading or not card.back_reading.strip():
            issues.append("Missing reading")
        
        if not card.back_translation or not card.back_translation.strip():
            issues.append("Missing translation")
        
        # Check confidence
        if card.confidence_score < self.min_confidence:
            issues.append(f"Low confidence ({card.confidence_score:.1%})")
        
        # Check for suspicious patterns
        if card.front == card.back_reading:
            issues.append("Front and reading are identical")
        
        if len(card.front) > 100:
            issues.append("Front text unusually long (might be a sentence)")
        
        if len(card.back_translation) > 200:
            issues.append("Translation unusually long")
        
        # Check for placeholder/error text
        suspicious_words = ["error", "failed", "unknown", "null", "none", "N/A"]
        if any(word in card.back_translation.lower() for word in suspicious_words):
            issues.append("Translation contains suspicious text")
        
        return issues
    
    def remove_duplicates(
        self,
        cards: List[Flashcard],
        key: str = "front"
    ) -> List[Flashcard]:
        """
        Remove duplicate flashcards
        
        Args:
            cards: List of flashcards
            key: Field to use for duplicate detection ('front', 'reading', or 'both')
            
        Returns:
            Deduplicated list of flashcards
        """
        seen = set()
        unique_cards = []
        
        for card in cards:
            # Create deduplication key
            if key == "front":
                dedup_key = card.front.strip()
            elif key == "reading":
                dedup_key = card.back_reading.strip()
            elif key == "both":
                dedup_key = (card.front.strip(), card.back_reading.strip())
            else:
                raise ValueError(f"Invalid key: {key}")
            
            # Check if seen
            if dedup_key not in seen:
                seen.add(dedup_key)
                unique_cards.append(card)
        
        return unique_cards
    
    def edit_flashcard(
        self,
        card: Flashcard,
        front: Optional[str] = None,
        back_reading: Optional[str] = None,
        back_translation: Optional[str] = None,
        context: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Flashcard:
        """
        Edit flashcard fields
        
        Args:
            card: Flashcard to edit
            front: New front text
            back_reading: New reading
            back_translation: New translation
            context: New context
            notes: New notes
            
        Returns:
            Updated flashcard
        """
        # Update fields if provided
        if front is not None:
            card.front = front
        if back_reading is not None:
            card.back_reading = back_reading
        if back_translation is not None:
            card.back_translation = back_translation
        if context is not None:
            card.context = context
        if notes is not None:
            card.notes = notes
        
        # Mark as edited
        card.user_edited = True
        card.validation_status = ValidationStatus.CORRECTED
        
        return card
    
    def approve_flashcard(
        self,
        card: Flashcard,
        save_to_vocabulary: bool = True
    ) -> Flashcard:
        """
        Approve flashcard (mark as validated)
        
        Args:
            card: Flashcard to approve
            save_to_vocabulary: Save to validated vocabulary database
            
        Returns:
            Approved flashcard
        """
        card.validation_status = ValidationStatus.VALIDATED
        
        # Save to vocabulary database if requested
        if save_to_vocabulary:
            self.add_to_vocabulary(
                kanji=card.front if self._contains_kanji(card.front) else None,
                kana=card.back_reading,
                reading=card.back_reading,
                translation=card.back_translation,
                context=card.context,
                validated=True
            )
        
        return card
    
    def reject_flashcard(
        self,
        card: Flashcard,
        reason: Optional[str] = None
    ) -> Flashcard:
        """
        Reject flashcard (mark for removal)
        
        Args:
            card: Flashcard to reject
            reason: Reason for rejection
            
        Returns:
            Rejected flashcard
        """
        card.validation_status = ValidationStatus.REJECTED
        if reason:
            card.notes = f"Rejected: {reason}"
        
        return card
    
    def filter_by_frequency(
        self,
        cards: List[Flashcard],
        min_frequency: Optional[int] = None,
        max_frequency: Optional[int] = None,
        top_n: Optional[int] = None
    ) -> List[Flashcard]:
        """
        Filter flashcards by frequency rank
        
        Args:
            cards: List of flashcards
            min_frequency: Minimum frequency rank (lower is more common)
            max_frequency: Maximum frequency rank
            top_n: Keep only top N most frequent words
            
        Returns:
            Filtered list of flashcards
        """
        filtered = []
        
        for card in cards:
            # Skip if no frequency data
            if card.frequency_rank is None:
                continue
            
            # Apply frequency filters
            if min_frequency and card.frequency_rank < min_frequency:
                continue
            if max_frequency and card.frequency_rank > max_frequency:
                continue
            
            filtered.append(card)
        
        # Sort by frequency if top_n requested
        if top_n:
            filtered.sort(key=lambda c: c.frequency_rank or float('inf'))
            filtered = filtered[:top_n]
        
        return filtered
    
    def get_validation_statistics(
        self,
        flashcard_set: FlashcardSet
    ) -> Dict:
        """
        Get validation statistics for flashcard set
        
        Args:
            flashcard_set: FlashcardSet to analyze
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_cards": len(flashcard_set.cards),
            "validated": 0,
            "corrected": 0,
            "pending": 0,
            "rejected": 0,
            "user_edited": 0,
            "avg_confidence": 0.0,
            "with_context": 0,
            "with_frequency": 0
        }
        
        confidence_sum = 0.0
        
        for card in flashcard_set.cards:
            # Count by status
            if card.validation_status == ValidationStatus.VALIDATED:
                stats["validated"] += 1
            elif card.validation_status == ValidationStatus.CORRECTED:
                stats["corrected"] += 1
            elif card.validation_status == ValidationStatus.PENDING:
                stats["pending"] += 1
            elif card.validation_status == ValidationStatus.REJECTED:
                stats["rejected"] += 1
            
            # Other statistics
            if card.user_edited:
                stats["user_edited"] += 1
            if card.context:
                stats["with_context"] += 1
            if card.frequency_rank:
                stats["with_frequency"] += 1
            
            confidence_sum += card.confidence_score
        
        # Calculate average confidence
        if flashcard_set.cards:
            stats["avg_confidence"] = confidence_sum / len(flashcard_set.cards)
        
        return stats
    
    def add_to_vocabulary(
        self,
        kanji: Optional[str],
        kana: str,
        reading: str,
        translation: str,
        context: Optional[str] = None,
        frequency: Optional[int] = None,
        tags: Optional[List[str]] = None,
        validated: bool = False
    ) -> VocabularyEntry:
        """
        Add entry to validated vocabulary database
        
        Args:
            kanji: Kanji form (optional)
            kana: Kana form
            reading: Hiragana reading
            translation: English translation
            context: Example sentence
            frequency: Frequency rank
            tags: Tags for categorization
            validated: Whether this entry is validated
            
        Returns:
            VocabularyEntry object
        """
        # Create vocabulary entry
        vocab_entry = VocabularyEntry(
            kanji=kanji,
            kana=kana,
            reading=reading,
            translation=translation,
            context=context,
            frequency=frequency,
            tags=tags or [],
            validated=validated
        )
        
        # Add to in-memory database
        self.validated_vocabulary[vocab_entry.id] = vocab_entry
        
        # Save to file
        self.save_vocabulary_db()
        
        return vocab_entry
    
    def get_vocabulary_suggestions(
        self,
        card: Flashcard
    ) -> List[VocabularyEntry]:
        """
        Get vocabulary suggestions from database
        
        Args:
            card: Flashcard to find suggestions for
            
        Returns:
            List of matching vocabulary entries
        """
        suggestions = []
        
        # Search in validated vocabulary
        for vocab_entry in self.validated_vocabulary.values():
            # Match by kanji or kana
            if (vocab_entry.kanji and vocab_entry.kanji == card.front) or \
               (vocab_entry.kana == card.front):
                suggestions.append(vocab_entry)
        
        return suggestions
    
    def export_rejected_cards(
        self,
        flashcard_set: FlashcardSet,
        output_path: str
    ) -> int:
        """
        Export rejected cards for review
        
        Args:
            flashcard_set: FlashcardSet containing cards
            output_path: Path to save rejected cards
            
        Returns:
            Number of rejected cards exported
        """
        rejected = [
            card for card in flashcard_set.cards 
            if card.validation_status == ValidationStatus.REJECTED
        ]
        
        if not rejected:
            return 0
        
        # Create export data
        export_data = [
            {
                "id": card.id,
                "front": card.front,
                "reading": card.back_reading,
                "translation": card.back_translation,
                "context": card.context,
                "notes": card.notes,
                "confidence": card.confidence_score
            }
            for card in rejected
        ]
        
        # Save to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Exported {len(rejected)} rejected cards to {output_path}")
        
        return len(rejected)
    
    def _contains_kanji(self, text: str) -> bool:
        """Check if text contains kanji characters"""
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def load_vocabulary_db(self) -> Dict[str, VocabularyEntry]:
        """Load vocabulary database from file"""
        if self.vocabulary_db_path.exists():
            try:
                with open(self.vocabulary_db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Convert to VocabularyEntry objects
                vocab_dict = {}
                for entry_data in data.values():
                    vocab_entry = VocabularyEntry(**entry_data)
                    vocab_dict[vocab_entry.id] = vocab_entry
                
                return vocab_dict
            except Exception as e:
                print(f"Warning: Could not load vocabulary database: {e}")
                return {}
        return {}
    
    def save_vocabulary_db(self):
        """Save vocabulary database to file"""
        try:
            # Convert to dict for JSON serialization
            data = {
                entry_id: entry.model_dump()
                for entry_id, entry in self.validated_vocabulary.items()
            }
            
            with open(self.vocabulary_db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save vocabulary database: {e}")


