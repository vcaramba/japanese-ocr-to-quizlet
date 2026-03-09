def contains_japanese(text: str) -> bool:
    """
    Check if text contains Japanese characters

    Args:
        text: Text to check

    Returns:
        True if contains Japanese
    """

    for char in text:
        # Check for hiragana, katakana, or kanji
        if '\u3040' <= char <= '\u30ff':  # Hiragana and Katakana
            return True
        if '\u4e00' <= char <= '\u9fff':  # Kanji
            return True
        if '\uff66' <= char <= '\uff9f':  # half-width Katakana
            return True

    return False

def contains_kanji(text: str) -> bool:
    """
            Check if text contains kanji characters

            Args:
                text: Text to check

            Returns:
                True if contains kanji
            """
    for char in text:
        # Kanji Unicode ranges
        if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
            return True
        if '\u3400' <= char <= '\u4dbf':  # CJK Extension A
            return True
        if '\uf900' <= char <= '\ufaff':  # CJK Compatibility Ideographs
            return True

    return False
