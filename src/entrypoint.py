from config.settings import settings
from src.pipeline import FlashcardPipeline

def main():
    # 1. Settings loaded from .env automatically
    print(f"Using {settings.default_translator} for translation")
    
    # 2. Create directories if needed
    settings.ensure_directories()
    
    # 3. Initialize pipeline with settings
    pipeline = FlashcardPipeline(
        ocr_engines=settings.default_ocr_engines,
        use_gpu=settings.use_gpu,
        deepl_api_key=settings.deepl_api_key
    )
    
    # 4. Process document
    # TODO: path of file uploaded via UI
    input_path = settings.input_dir / "book.pdf"
    session = pipeline.process_document(input_path)
    
    # 5. Export to configured output directory
    output_path = settings.output_dir / "flashcards.csv"
    session.flashcard_set.to_quizlet_csv()

if __name__ == "__main__":
    main()