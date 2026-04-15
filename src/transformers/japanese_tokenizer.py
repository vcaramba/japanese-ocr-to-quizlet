from typing import List

from fugashi import Tagger

from models.data_models import JapaneseToken
import re
from validators.characters_validator import contains_kanji

"""
Japanese Tokenizer (Fugashi)
Segments Japanese text into words with readings and part-of-speech tags
"""


class JapaneseTokenizer:
    def __init__(self):
        self.tagger = Tagger()

    def tokenize(self, text: str) -> List[JapaneseToken]:
        """Tokenize Japanese text into words with readings
        Args:
            text: Japanese text to tokenize

        Returns:
            List of JapaneseToken objects
        """
        print(f"Tokenizing text: {text[:30]}...")  # Debug log
        if not text or not text.strip():
            return []

        tokens = []
        # self.tagger.parse(text)  # Pre-parse to initialize the tagger

        for word in self.tagger(text):
            # Extract features
            surface = word.surface  # Original form

            # Get reading (kana)
            # feature[7] is the reading in katakana
            reading = word.feature.kana if hasattr(word.feature, 'kana') and word.feature.kana else surface

            # Get base form (dictionary form)
            base_form = word.feature.lemma if hasattr(word.feature, 'lemma') and word.feature.lemma else surface

            # Get part of speech
            pos = word.feature.pos1 if hasattr(word.feature, 'pos1') and word.feature.pos1 else "unknown"

            # Check if contains kanji
            has_kanji = contains_kanji(surface)
            print(f"Token: {surface}, Reading: {reading}, Base: {base_form}, POS: {pos}, Has Kanji: {has_kanji}")  # Debug log

            # Create token
            token = JapaneseToken(
                surface=surface,
                reading=self.convert_katakana_to_hiragana(reading),
                base_form=base_form,
                pos=pos,
                has_kanji=has_kanji,
                confidence=1.0
            )
            print(f"Created token: {token}")  # Debug log

            tokens.append(token)

        return tokens
    
    def convert_katakana_to_hiragana(self, text: str) -> str:
        """
        Convert katakana to hiragana
        
        Args:
            text: Text in katakana
            
        Returns:
            Text in hiragana
        """
        if text is None:
            return ""
        
        hiragana = []
        for char in text:
            # Katakana range: 0x30A0 - 0x30FF
            # Hiragana range: 0x3040 - 0x309F
            # Difference: 0x0060
            if '\u30a0' <= char <= '\u30ff':
                hiragana.append(chr(ord(char) - 0x60))
            else:
                hiragana.append(char)
        
        return ''.join(hiragana)
    
    






