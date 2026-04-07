from sympy import re
import os

from models.data_models import TextOrientation


class TextTransformer:
    def __init__(self):
        pass

    def transform(self, text: str, orientation: TextOrientation) -> str:
        # Placeholder for actual text transformation logic
      
        if not text:
            return ""
        
        # Remove furigana in brackets: 漢字(かんじ) -> 漢字
        text = self.remove_furigana_brackets(text)
        
        # Normalize characters
        text = self.normalize_japanese(text)
        
        # Remove extra whitespace
        text = self._remove_extra_whitespace(text)
        
        return text
    
    def remove_furigana_brackets(self, text: str) -> str:
        # Remove (hiragana/katakana) after kanji
        # Match pattern: kanji(kana)
        pattern = r'([一-龯々])[\(（][\u3040-\u309F\u30A0-\u30FF]+[\)）]'
        text = re.sub(pattern, r'\1', text)
        
        # Also handle multi-kanji patterns
        pattern = r'([一-龯々]+)[\(（]([\u3040-\u309F\u30A0-\u30FF]+)[\)）]'
        text = re.sub(pattern, r'\1', text)
        
        return text