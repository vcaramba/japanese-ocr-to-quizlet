from models.data_models import TextOrientation


class TextCleaner:
    def remove_furigana_brackets(self, text: str) -> str:
        """Remove ruby annotations like 漢字(かんじ)"""
        pass

    def detect_orientation(self, text: str) -> TextOrientation:
        """Detect tategaki vs yokogaki"""
        pass

    def normalize_japanese(self, text: str) -> str:
        """Normalize width, remove noise"""
        pass