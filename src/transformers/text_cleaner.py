from sympy import re
import jaconv

from models.data_models import TextOrientation


class TextCleaner:
    def clean(self, text: str) -> str:
        """
        Clean and normalize Japanese text
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove furigana in brackets: 漢字(かんじ) -> 漢字
        text = self.remove_furigana_brackets(text)
        
        # Normalize characters
        text = self.normalize_japanese(text)
        
        # Remove extra whitespace
        text = self.remove_extra_whitespace(text)
        
        return text
    def remove_furigana_brackets(self, text: str) -> str:
        """
        Remove furigana in parentheses
        
        Examples:
            漢字(かんじ) -> 漢字
            東京(とうきょう) -> 東京
        
        Args:
            text: Text with furigana
            
        Returns:
            Text without furigana brackets
        """
        # Remove (hiragana/katakana) after kanji
        # Match pattern: kanji(kana)
        pattern = r'([一-龯々])[\(（][\u3040-\u309F\u30A0-\u30FF]+[\)）]'
        text = re.sub(pattern, r'\1', text)
        
        # Also handle multi-kanji patterns
        pattern = r'([一-龯々]+)[\(（]([\u3040-\u309F\u30A0-\u30FF]+)[\)）]'
        text = re.sub(pattern, r'\1', text)
        
        return text

    def detect_orientation(self, text: str) -> TextOrientation:
        """Detect tategaki vs yokogaki  (horizontal vs vertical)
         Args:
            text: Japanese text
            
        Returns:
            Detected orientation
        """
        if not text:
            return TextOrientation.HORIZONTAL
        
        # Count new lines vs total characters
        lines = text.split('\n')
        num_lines = len(lines)
        
        if num_lines == 1:
            # Single line - likely horizontal
            return TextOrientation.HORIZONTAL
        
        # Calculate average line length
        avg_line_length = sum(len(line) for line in lines) / num_lines
        
        # Heuristic: vertical text has many short lines
        if avg_line_length < 15 and num_lines > 3:
            return TextOrientation.VERTICAL
        
        # Check for vertical punctuation marks
        vertical_marks = ['︙', '︰', '︱', '︳', '︴', '︵', '︶', '︷', '︸']
        if any(mark in text for mark in vertical_marks):
            return TextOrientation.VERTICAL
        
        # Default to horizontal
        return TextOrientation.HORIZONTAL

    def normalize_japanese(self, text: str) -> str:
        """Normalize width, remove noise"""
        """
        Normalize Japanese characters
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert full-width alphanumerics to half-width
        text = jaconv.z2h(text, kana=False, digit=True, ascii=True)
        
        # Normalize variations
        # Convert full-width katakana to half-width where appropriate
        # But keep Japanese characters as-is
        
        return text
    
    def remove_extra_whitespace(self, text: str) -> str:
        """
        Remove extra whitespace while preserving structure
        
        Args:
            text: Text with whitespace
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Trim whitespace at start and end
        text = text.strip()
        
        return text