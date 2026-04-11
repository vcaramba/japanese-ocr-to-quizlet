# japanese-ocr-to-quizlet

A single-user OCR & NLP pipeline that converts Japanese textbooks or books
(PDF or images) into Quizlet-compatible sets of learning flashcards.

The project focuses on:
- OCR for vertically oriented Japanese text (kanji / hiragana / katakana / furigana) from various textbooks
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


#Install necessary dependencies:
- pip install -r requirements.txt
- Windows installation: py -m pip install --only-binary :all: -r requirements.txt
#Install Tesseract OCR:
- https://tesseract-ocr.github.io/tessdoc/Installation.html

#Add your DeepL API key to .env:
- DEEPL_API_KEY=your-key-here
- Get free key at: https://www.deepl.com/pro-api

#Launch the UI:
- streamlit run src/ui/app.py
- Windows: python -m streamlit run src/ui/app.py
