# japanese-ocr-to-quizlet

A single-user OCR & NLP pipeline that converts Japanese textbooks or books
(PDF or images) into Quizlet-compatible sets of learning flashcards.

The project focuses on:
- OCR for vertically oriented Japanese text (kanji / hiragana / katakana / furigana) from Minna no Nihongo & So-Matome books
- OCR kanji / furigana detection from tategaki text (horizontal, up-to-down, right-to-left as in Japanese novels) 
- Tokenization and reading (furigana)
- Manual validation via UI
- Comparing multiple OCR / NLP models by accuracy and confidence

---

## 🚀 Features

- Upload **PDF or images**
- Extract Japanese text using OCR
- Convert text into the set of **flashcards**:
  - Side A: Kanji / hiragana / katakana
  - Side B: Reading in hiragana (mandatory for kanji only, otherwise skipped) & English translation
- Export to **Quizlet-compatible CSV**
- **Manual validation UI** (edit OCR results before export)
- **Multi-model comparison**:
  - Different OCR engines
  - Different NLP/tokenization pipelines
  - Accuracy & confidence evaluation

---

## 🧠 Use cases

### 1. Textbook → Quizlet cards
Upload photos or PDF pages from a Japanese textbook.
Translation is already present in the book.
Extract vocabulary and according translation, generate study cards.

### 2. Japanese book → Vocabulary cards
Upload photos of page(s) from a Japanese book with tategaki.
Extract kanji-based vocabulary, translate into English, and generate study cards.

---

## 🏗 Architecture (High-level)

Input (PDF / Images)
|
v
OCR Layer
(Tesseract / EasyOCR / etc.)
|
v
NLP Layer
(Tokenization, readings)
|
v
Card Generator
|
v
Manual Validation UI
(Streamlit / Gradio)
|
v
Quizlet CSV Export
