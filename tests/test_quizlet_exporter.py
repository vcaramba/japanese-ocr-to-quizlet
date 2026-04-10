import pytest
import csv
import io
from models.data_models import Flashcard, FlashcardSet


class TestQuizletExporter:
    """Test the Quizlet export functionality"""

    def test_export_single_card_no_context(self):
        """Test exporting a single flashcard without context"""
        card = Flashcard(
            front="今晩は",
            back_reading="こんばんは",
            back_translation="Good evening"
        )
        flashcard_set = FlashcardSet(
            title="Greetings",
            cards=[card],
            source_files=["greetings.pdf"]
        )

        csv_output = flashcard_set.to_quizlet_csv()
        # Parse the CSV to verify
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) == 1
        front, back = rows[0]
        assert front == "今晩は"
        assert "こんばんは" in back
        assert "Good evening" in back

    def test_export_multiple_cards_with_context(self):
        """Test exporting multiple flashcards with context"""
        card1 = Flashcard(
            front="犬",
            back_reading="いぬ",
            back_translation="Dog",
            context="A loyal pet"
        )
        card2 = Flashcard(
            front="猫",
            back_reading="ねこ",
            back_translation="Cat"
        )
        flashcard_set = FlashcardSet(
            title="Animals",
            cards=[card1, card2],
            source_files=["animals.pdf"]
        )

        csv_output = flashcard_set.to_quizlet_csv()
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) == 2

        # First card
        front1, back1 = rows[0]
        assert front1 == "犬"
        assert "いぬ" in back1
        assert "Dog" in back1
        assert "A loyal pet" in back1

        # Second card
        front2, back2 = rows[1]
        assert front2 == "猫"
        assert "ねこ" in back2
        assert "Cat" in back2

    def test_export_empty_set(self):
        """Test exporting an empty flashcard set"""
        flashcard_set = FlashcardSet(
            title="Empty",
            cards=[],
            source_files=[]
        )
        csv_output = flashcard_set.to_quizlet_csv()
        # Should be empty
        assert csv_output.strip() == ""

    def test_export_special_characters(self):
        """Test exporting cards with special characters"""
        card = Flashcard(
            front="café",
            back_reading="kafe",
            back_translation="coffee",
            context="A drink with café au lait"
        )
        flashcard_set = FlashcardSet(
            title="Drinks",
            cards=[card],
            source_files=["drinks.pdf"]
        )

        csv_output = flashcard_set.to_quizlet_csv()
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) == 1
        front, back = rows[0]
        assert front == "café"
        assert "café au lait" in back

    def test_csv_format_validation(self):
        """Test that the CSV format is valid and parseable"""
        card = Flashcard(
            front="test",
            back_reading="reading",
            back_translation="translation"
        )
        flashcard_set = FlashcardSet(
            title="Test",
            cards=[card],
            source_files=["test.pdf"]
        )

        csv_output = flashcard_set.to_quizlet_csv()
        # Should be valid CSV
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)
        assert len(rows) == 1
        assert len(rows[0]) == 2  # front, back