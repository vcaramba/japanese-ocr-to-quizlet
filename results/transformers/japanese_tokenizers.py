from fugashi import Tagger


class JapaneseTokenizer:
    def __init__(self, name):
        self.name = name

    def tokenize(self, selected_text):
        pass


class FugashiTokenizer(JapaneseTokenizer):
    def __init__(self):
        super().__init__("Fugashi")

        self.tagger = Tagger()

    def tokenize(self, text):
        tokens = []
        for word in self.tagger(text):
            tokens.append({
                "surface": word.surface,
                "reading": getattr(word.feature, "reading", None),
                "kanji": word.surface,
                "pos": word.feature.pos,
                "confidence": 1.0
            })
        return tokens


class SudachiPyTokenizer(JapaneseTokenizer):
    def __init__(self):
        super().__init__("SudachiPy")

    def tokenize(self, selected_text):
        pass
