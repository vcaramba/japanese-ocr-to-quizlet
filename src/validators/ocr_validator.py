"""
OCR Validator Module
Provides validation and correction capabilities for OCR results
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

from models.data_models import OCRResult, OCRConsensus, PageExtraction, TextOrientation, ValidationStatus, TrainingExample


class OCRValidator:
    """
    Validates OCR results and collects training data for improvement
    
    Features:
    - Manual validation and correction of OCR results
    - Confidence-based auto-validation
    - Training data collection for OCR improvement
    - Validation history tracking
    - Feedback loop for OCR selector weights
    """
    
    def __init__(
        self,
        auto_validate_threshold: float = 0.95,
        training_data_dir: str = "data/training"
    ):
        """
        Initialize OCR validator
        
        Args:
            auto_validate_threshold: Confidence threshold for auto-validation
            training_data_dir: Directory to store training examples
        """
        self.auto_validate_threshold = auto_validate_threshold
        self.training_data_dir = Path(training_data_dir)
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.training_data_dir / "images").mkdir(exist_ok=True)
        (self.training_data_dir / "annotations").mkdir(exist_ok=True)
        
        # Load validation history
        self.validation_history_path = self.training_data_dir / "validation_history.json"
        self.validation_history = self._load_validation_history()
    
    def validate_page(
        self,
        page_extraction: PageExtraction,
        auto_validate: bool = True
    ) -> PageExtraction:
        """
        Validate OCR results for a page
        
        Args:
            page_extraction: Page extraction to validate
            auto_validate: Whether to auto-validate high-confidence results
            
        Returns:
            Updated PageExtraction with validation status
        """
        # Check if OCR was used
        if not page_extraction.ocr_consensus:
            # No OCR used (direct PDF text extraction)
            page_extraction.validation_status = ValidationStatus.VALIDATED
            return page_extraction
        
        consensus = page_extraction.ocr_consensus
        
        # Auto-validate if confidence is very high
        if auto_validate and consensus.consensus_score >= self.auto_validate_threshold:
            page_extraction.validation_status = ValidationStatus.VALIDATED
            consensus.validation_status = ValidationStatus.VALIDATED
            
            # Log auto-validation
            self.log_validation(
                page_number=page_extraction.page_number,
                engine=consensus.selected_engine,
                confidence=consensus.consensus_score,
                validation_type="auto",
                status="validated"
            )
        
        return page_extraction
    
    def correct_ocr(
        self,
        page_extraction: PageExtraction,
        corrected_text: str,
        user_notes: Optional[str] = None,
        save_as_training: bool = True
    ) -> PageExtraction:
        """
        Apply manual correction to OCR result
        
        Args:
            page_extraction: Page extraction to correct
            corrected_text: Manually corrected text
            user_notes: Optional notes about the correction
            save_as_training: Whether to save as training example
            
        Returns:
            Updated PageExtraction with corrected text
        """
        if not page_extraction.ocr_consensus:
            raise ValueError("Cannot correct page without OCR consensus")
        
        consensus = page_extraction.ocr_consensus
        
        # Store original text
        original_text = consensus.selected_text
        
        # Update consensus
        consensus.corrected_text = corrected_text
        consensus.user_notes = user_notes
        consensus.validation_status = ValidationStatus.CORRECTED
        
        # Update page extraction
        page_extraction.raw_text = corrected_text
        page_extraction.validation_status = ValidationStatus.CORRECTED
        
        # Log correction
        self.log_validation(
            page_number=page_extraction.page_number,
            engine=consensus.selected_engine,
            confidence=consensus.consensus_score,
            validation_type="manual_correction",
            status="corrected",
            original_text=original_text,
            corrected_text=corrected_text,
            notes=user_notes
        )
        
        # Save as training example if requested
        if save_as_training:
            self.save_training_example(
                image_path=page_extraction.image_path,
                ground_truth_text=corrected_text,
                orientation=page_extraction.orientation,
                source="user_correction",
                metadata={
                    "page_number": page_extraction.page_number,
                    "original_engine": consensus.selected_engine,
                    "original_confidence": consensus.consensus_score,
                    "correction_notes": user_notes
                }
            )
        
        return page_extraction
    
    def reject_ocr(
        self,
        page_extraction: PageExtraction,
        reason: Optional[str] = None
    ) -> PageExtraction:
        """
        Reject OCR result (mark for re-processing)
        
        Args:
            page_extraction: Page extraction to reject
            reason: Optional reason for rejection
            
        Returns:
            Updated PageExtraction with rejected status
        """
        if not page_extraction.ocr_consensus:
            raise ValueError("Cannot reject page without OCR consensus")
        
        consensus = page_extraction.ocr_consensus
        
        # Update status
        consensus.validation_status = ValidationStatus.REJECTED
        consensus.user_notes = reason
        page_extraction.validation_status = ValidationStatus.REJECTED
        
        # Log rejection
        self.log_validation(
            page_number=page_extraction.page_number,
            engine=consensus.selected_engine,
            confidence=consensus.consensus_score,
            validation_type="rejection",
            status="rejected",
            notes=reason
        )
        
        return page_extraction
    
    def save_training_example(
        self,
        image_path: str,
        ground_truth_text: str,
        orientation: TextOrientation,
        source: str = "user_correction",
        metadata: Optional[Dict] = None
    ) -> TrainingExample:
        """
        Save a training example for OCR improvement
        
        Args:
            image_path: Path to original image
            ground_truth_text: Correct text (ground truth)
            orientation: Text orientation
            source: Source of training data
            metadata: Additional metadata
            
        Returns:
            TrainingExample object
        """
        # Create training example
        training_example = TrainingExample(
            image_path=image_path,
            ground_truth_text=ground_truth_text,
            orientation=orientation,
            source=source
        )
        
        # Save annotation file
        annotation_path = (
            self.training_data_dir / "annotations" / 
            f"{training_example.id}.json"
        )
        
        annotation_data = {
            "id": training_example.id,
            "image_path": image_path,
            "ground_truth_text": ground_truth_text,
            "orientation": orientation.value,
            "source": source,
            "created_at": training_example.created_at.isoformat(),
            "metadata": metadata or {}
        }
        
        with open(annotation_path, 'w', encoding='utf-8') as f:
            json.dump(annotation_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Saved training example: {training_example.id}")
        
        return training_example
    
    def get_validation_statistics(self) -> Dict:
        """
        Get statistics about validation history
        
        Returns:
            Dictionary with validation statistics
        """
        if not self.validation_history:
            return {
                "total_validations": 0,
                "auto_validated": 0,
                "manually_corrected": 0,
                "rejected": 0,
                "engines": {}
            }
        
        stats = {
            "total_validations": len(self.validation_history),
            "auto_validated": 0,
            "manually_corrected": 0,
            "rejected": 0,
            "engines": {}
        }
        
        for entry in self.validation_history:
            # Count by validation type
            if entry["validation_type"] == "auto":
                stats["auto_validated"] += 1
            elif entry["validation_type"] == "manual_correction":
                stats["manually_corrected"] += 1
            elif entry["validation_type"] == "rejection":
                stats["rejected"] += 1
            
            # Count by engine
            engine = entry["engine"]
            if engine not in stats["engines"]:
                stats["engines"][engine] = {
                    "total": 0,
                    "validated": 0,
                    "corrected": 0,
                    "rejected": 0,
                    "avg_confidence": 0.0
                }
            
            stats["engines"][engine]["total"] += 1
            
            if entry["status"] == "validated":
                stats["engines"][engine]["validated"] += 1
            elif entry["status"] == "corrected":
                stats["engines"][engine]["corrected"] += 1
            elif entry["status"] == "rejected":
                stats["engines"][engine]["rejected"] += 1
            
            # Track confidence
            if "confidence" in entry:
                current_avg = stats["engines"][engine]["avg_confidence"]
                total = stats["engines"][engine]["total"]
                new_avg = (current_avg * (total - 1) + entry["confidence"]) / total
                stats["engines"][engine]["avg_confidence"] = new_avg
        
        return stats
    
    def get_engine_accuracy(self, engine_name: str) -> float:
        """
        Calculate accuracy for a specific OCR engine
        
        Args:
            engine_name: Name of OCR engine
            
        Returns:
            Accuracy score (0.0 to 1.0)
        """
        engine_entries = [
            entry for entry in self.validation_history 
            if entry.get("engine") == engine_name
        ]
        
        if not engine_entries:
            return 0.0
        
        validated_count = sum(
            1 for entry in engine_entries 
            if entry.get("status") == "validated"
        )
        
        return validated_count / len(engine_entries)
    
    def get_correction_suggestions(
        self,
        page_extraction: PageExtraction
    ) -> List[str]:
        """
        Get suggestions for common OCR corrections
        
        Args:
            page_extraction: Page extraction to analyze
            
        Returns:
            List of suggested corrections
        """
        if not page_extraction.ocr_consensus:
            return []
        
        suggestions = []
        text = page_extraction.ocr_consensus.selected_text
        
        # Common OCR mistakes in Japanese
        common_mistakes = [
            ("人", "入", "人 vs 入 (person vs enter)"),
            ("土", "士", "土 vs 士 (earth vs samurai)"),
            ("未", "末", "未 vs 末 (not yet vs end)"),
            ("己", "已", "己 vs 已 (self vs already)"),
            ("る", "ろ", "る vs ろ (hiragana ru vs ro)"),
            ("わ", "ね", "わ vs ね (hiragana wa vs ne)"),
        ]
        
        for char1, char2, description in common_mistakes:
            if char1 in text or char2 in text:
                suggestions.append(f"Check: {description}")
        
        # Low confidence warning
        if page_extraction.ocr_consensus.consensus_score < 0.8:
            suggestions.append("⚠️ Low confidence score - carefully review text")
        
        # Mixed results warning
        if len(page_extraction.ocr_consensus.all_results) > 1:
            unique_texts = set(r.text for r in page_extraction.ocr_consensus.all_results)
            if len(unique_texts) > 1:
                suggestions.append("⚠️ OCR engines disagree - verify carefully")
        
        return suggestions
    
    def log_validation(
        self,
        page_number: int,
        engine: str,
        confidence: float,
        validation_type: str,
        status: str,
        original_text: Optional[str] = None,
        corrected_text: Optional[str] = None,
        notes: Optional[str] = None
    ):
        """
        Log validation event to history
        
        Args:
            page_number: Page number
            engine: OCR engine name
            confidence: Confidence score
            validation_type: Type of validation
            status: Validation status
            original_text: Original OCR text
            corrected_text: Corrected text
            notes: Additional notes
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "page_number": page_number,
            "engine": engine,
            "confidence": confidence,
            "validation_type": validation_type,
            "status": status
        }
        
        if original_text:
            entry["original_text"] = original_text
        if corrected_text:
            entry["corrected_text"] = corrected_text
        if notes:
            entry["notes"] = notes
        
        self.validation_history.append(entry)
        self.save_validation_history()
    
    def _load_validation_history(self) -> List[Dict]:
        """Load validation history from file"""
        if self.validation_history_path.exists():
            try:
                with open(self.validation_history_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load validation history: {e}")
                return []
        return []
    
    def save_validation_history(self):
        """Save validation history to file"""
        try:
            with open(self.validation_history_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save validation history: {e}")


# ============================================================================
# Usage Example
# ============================================================================

# if __name__ == "__main__":
#     """
#     Example usage of OCR validator
#     """
#     from models.data_models import OCRResult, OCRConsensus, PageExtraction, ExtractionMethod
    
#     print("=" * 60)
#     print("OCR Validator - Usage Example")
#     print("=" * 60)
    
#     # Initialize validator
#     validator = OCRValidator(
#         auto_validate_threshold=0.95,
#         training_data_dir="data/training"
#     )
    
#     print("\n✓ Validator initialized")
    
#     # Create mock OCR results
#     ocr_result1 = OCRResult(
#         engine="manga_ocr",
#         text="今日は天気がいいです",
#         confidence=0.92,
#         orientation=TextOrientation.HORIZONTAL,
#         processing_time=2.5
#     )
    
#     ocr_result2 = OCRResult(
#         engine="easyocr",
#         text="今日は天気がいいです",
#         confidence=0.88,
#         orientation=TextOrientation.HORIZONTAL,
#         processing_time=3.1
#     )
    
#     consensus = OCRConsensus(
#         selected_text="今日は天気がいいです",
#         selected_engine="manga_ocr",
#         all_results=[ocr_result1, ocr_result2],
#         consensus_score=0.96,
#         orientation=TextOrientation.HORIZONTAL
#     )
    
#     page = PageExtraction(
#         page_number=0,
#         image_path="test_page.jpg",
#         extraction_method=ExtractionMethod.OCR_IMAGE,
#         ocr_consensus=consensus,
#         raw_text="今日は天気がいいです",
#         orientation=TextOrientation.HORIZONTAL
#     )
    
#     # Auto-validate high confidence result
#     print("\n" + "-" * 60)
#     print("Test 1: Auto-validation")
#     print("-" * 60)
    
#     validated_page = validator.validate_page(page, auto_validate=True)
#     print(f"Validation status: {validated_page.validation_status.value}")
#     print(f"Consensus score: {consensus.consensus_score:.1%}")
    
#     # Manual correction example
#     print("\n" + "-" * 60)
#     print("Test 2: Manual correction")
#     print("-" * 60)
    
#     # Simulate low confidence result
#     consensus.consensus_score = 0.75
#     page.validation_status = ValidationStatus.PENDING
    
#     corrected_page = validator.correct_ocr(
#         page,
#         corrected_text="今日は天気が良いです",  # Changed いい to 良い
#         user_notes="Changed hiragana to kanji for 'いい'",
#         save_as_training=True
#     )
    
#     print(f"Original: {consensus.selected_text}")
#     print(f"Corrected: {consensus.corrected_text}")
#     print(f"Status: {corrected_page.validation_status.value}")
    
#     # Get statistics
#     print("\n" + "-" * 60)
#     print("Validation Statistics")
#     print("-" * 60)
    
#     stats = validator.get_validation_statistics()
#     print(f"Total validations: {stats['total_validations']}")
#     print(f"Auto-validated: {stats['auto_validated']}")
#     print(f"Manually corrected: {stats['manually_corrected']}")
#     print(f"Rejected: {stats['rejected']}")
    
#     if stats['engines']:
#         print("\nPer-engine statistics:")
#         for engine, engine_stats in stats['engines'].items():
#             print(f"\n  {engine}:")
#             print(f"    Total: {engine_stats['total']}")
#             print(f"    Validated: {engine_stats['validated']}")
#             print(f"    Corrected: {engine_stats['corrected']}")
#             print(f"    Avg confidence: {engine_stats['avg_confidence']:.1%}")
    
#     # Get correction suggestions
#     print("\n" + "-" * 60)
#     print("Correction Suggestions")
#     print("-" * 60)
    
#     suggestions = validator.get_correction_suggestions(page)
#     if suggestions:
#         for suggestion in suggestions:
#             print(f"  • {suggestion}")
#     else:
#         print("  No suggestions")
    
#     print("\n" + "=" * 60)
#     print("Example complete!")
#     print("=" * 60)
#     print()