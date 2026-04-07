"""
Setup configuration for Japanese Flashcard ETL Pipeline
Allows installation as a package: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

def install_requirements():
    """Read requirements from requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, "r", encoding="utf-8") as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith("#")
            ]
    else:
        raise FileNotFoundError("requirements.txt not found")

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        install_requires = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]
else:
    # Fallback to minimal requirements
    install_requires = [
        "pydantic==2.7.0",
        "pydantic-settings==2.7.0",
        "python-dotenv==1.0.1",
        "streamlit==1.56.0",
        "pillow==11.0.0",
        "pdf2image==1.17.0",
        "pypdf==5.1.0",
        "pytesseract==0.3.10",
        "easyocr==1.7.2",
        "fugashi==1.3.2",
        "unidic-lite==1.0.8",
        "jaconv==0.3.4",
        "deepl==1.19.1",
        "pandas==2.2.3",
        "tqdm==4.67.1",
    ]




# =========================================================================
# Post-Install Instructions
# =========================================================================

def print_post_install_message():
    """Print helpful message after installation"""
    print("\n" + "=" * 70)
    print("Japanese Flashcard ETL Pipeline - Installation Complete!")
    print("=" * 70)
    
    print("\n📦 Package installed successfully!")
    
    print("\n🚀 Next Steps:")
    print("  1. Copy .env.example to .env:")
    print("     cp .env.example .env")
    
    print("\n  2. Add your DeepL API key to .env:")
    print("     DEEPL_API_KEY=your-key-here")
    print("     Get free key at: https://www.deepl.com/pro-api")
    
    print("\n  3. Install system dependencies:")
    print("     # Ubuntu/Debian:")
    print("     sudo apt-get install tesseract-ocr tesseract-ocr-jpn poppler-utils")
    print()
    print("     # macOS:")
    print("     brew install tesseract tesseract-lang poppler")
    
    print("\n  4. Test the installation:")
    print("     python test_pipeline.py data/uploads/your_image.jpg")
    
    print("\n  5. Launch the UI:")
    print("     streamlit run src/ui/app.py")
    
    print("\n📚 Documentation:")
    print("  - README.md - Getting started guide")
    print("\n" + "=" * 70)
    print()


# Print message if running setup.py install directly
if __name__ == "__main__":
    install_requirements()    
    print_post_install_message()
