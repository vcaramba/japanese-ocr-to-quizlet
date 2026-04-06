from typing import Optional, List

from src.models.data_models import JapaneseToken

import deepl


class Translator:
    """
    Translates Japanese text to English using DeepL API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize translator
        
        Args:
            api_key: DeepL API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "DeepL API key not provided. "
                "Set DEEPL_API_KEY environment variable or pass api_key parameter."
            )
        
        # Initialize DeepL translator
        self.translator = deepl.Translator(self.api_key)
    def translate_tokens(
        self,
        flashcard_tokens: List[JapaneseToken],
        batch_size: int = 50
    ) -> List[str]:
        """
        Translate base forms of tokens
        
        Args:
            tokens: List of Japanese tokens
            batch_size: Number of tokens to translate at once
            
        Returns:
            List of translations (same length as tokens)
        """
        # Extract unique base forms to minimize API calls
        unique_forms = {}
        for i, token in enumerate(flashcard_tokens):
            base_form = token.base_form
            if base_form not in unique_forms:
                unique_forms[base_form] = []
            unique_forms[base_form].append(i)
        
        # Translate unique forms in batches
        translations_map = {}
        base_forms_list = list(unique_forms.keys())
        
        for i in range(0, len(base_forms_list), batch_size):
            batch = base_forms_list[i:i + batch_size]
            batch_translations = self.translate_batch(batch)
            
            for base_form, translation in zip(batch, batch_translations):
                translations_map[base_form] = translation
        
        # Map translations back to tokens
        translations = []
        for token in flashcard_tokens:
            translation = translations_map.get(token.base_form, "")
            translations.append(translation)
        
        return translations
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "JA",
        target_lang: str = "EN-US"
    ) -> List[str]:
        """
        Translate multiple texts in batch (more efficient)
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        # Filter out empty texts but remember positions
        text_map = {}
        texts_to_translate = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                text_map[len(texts_to_translate)] = i
                texts_to_translate.append(text)
        
        if not texts_to_translate:
            return [""] * len(texts)
        
        try:
            results = self.translator.translate_text(
                texts_to_translate,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # Map results back to original positions
            translations = [""] * len(texts)
            for result_idx, original_idx in text_map.items():
                translations[original_idx] = results[result_idx].text
            
            return translations
        
        except Exception as e:
            raise Exception(f"Batch translation failed: {str(e)}")