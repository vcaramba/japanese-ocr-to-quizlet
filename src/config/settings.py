"""
Configuration settings for Japanese Flashcard ETL Pipeline
Loads settings from environment variables with sensible defaults
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file
    
    Usage:
        from config.settings import settings
        
        # Access settings
        api_key = settings.deepl_api_key
        ocr_engines = settings.default_ocr_engines
    """
    
    # =========================================================================
    # Application Metadata
    # =========================================================================
    
    app_name: str = "Japanese Flashcard ETL Pipeline"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # =========================================================================
    # API Keys
    # =========================================================================
    
    deepl_api_key: Optional[str] = Field(default=None, env="DEEPL_API_KEY")
    google_application_credentials: Optional[str] = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_translate_project_id: Optional[str] = Field(
        default=None,
        env="GOOGLE_TRANSLATE_PROJECT_ID"
    )
    
    # =========================================================================
    # OCR Configuration
    # =========================================================================
    
    default_ocr_engines: List[str] = Field(
        default=["easyocr"],
        env="DEFAULT_OCR_ENGINES"
    )
    
    ocr_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        env="OCR_CONFIDENCE_THRESHOLD",
        description="Threshold for auto-approving OCR results (0.0-1.0)"
    )
    
    use_gpu: bool = Field(
        default=False,
        env="USE_GPU",
        description="Enable GPU acceleration for OCR and ML models"
    )
    
    # =========================================================================
    # Translation Configuration
    # =========================================================================
    
    default_translator: str = Field(
        default="deepl",
        env="DEFAULT_TRANSLATOR",
        description="Translation service: deepl, google, or local"
    )
    
    translation_target_lang: str = Field(
        default="EN-US",
        env="TRANSLATION_TARGET_LANG",
        description="Target language code (e.g., EN-US, EN-GB)"
    )
    
    translation_fallback_to_local: bool = Field(
        default=True,
        env="TRANSLATION_FALLBACK_TO_LOCAL",
        description="Use local models if API fails"
    )
    
    translation_batch_size: int = Field(
        default=50,
        ge=1,
        le=100,
        env="TRANSLATION_BATCH_SIZE",
        description="Number of items to translate in one batch"
    )
    
    # =========================================================================
    # Japanese NLP Configuration
    # =========================================================================
    
    default_tokenizer: str = Field(
        default="fugashi",
        env="DEFAULT_TOKENIZER",
        description="Tokenizer to use: fugashi or sudachi"
    )
    
    reading_extractor: str = Field(
        default="cutlet",
        env="READING_EXTRACTOR",
        description="Reading extraction method: pykakasi or cutlet"
    )
    
    # =========================================================================
    # Data Paths
    # =========================================================================
    
    # Base directories (relative to project root)
    data_dir: Path = Field(default=Path("data"), env="DATA_DIR")
    upload_dir: Path = Field(default=Path("data/uploads"), env="UPLOAD_DIR")
    processing_dir: Path = Field(
        default=Path("data/processing"),
        env="PROCESSING_DIR"
    )
    training_dir: Path = Field(
        default=Path("data/training"),
        env="TRAINING_DIR"
    )
    input_dir: Path = Field(default=Path("data/input"), env="INPUT_DIR")
    output_dir: Path = Field(default=Path("data/output"), env="OUTPUT_DIR")
    models_dir: Path = Field(default=Path("models"), env="MODELS_DIR")
    
    @validator("data_dir", "upload_dir", "processing_dir", "training_dir", 
               "output_dir", "models_dir", pre=True)
    def convert_to_path(cls, v):
        """Convert string to Path object"""
        return Path(v) if isinstance(v, str) else v
    
    # =========================================================================
    # Processing Options
    # =========================================================================
    
    include_context: bool = Field(
        default=True,
        env="INCLUDE_CONTEXT",
        description="Include context sentences in flashcards"
    )
    
    deduplicate_cards: bool = Field(
        default=True,
        env="DEDUPLICATE_CARDS",
        description="Remove duplicate flashcards"
    )
    
    min_word_frequency: int = Field(
        default=0,
        ge=0,
        env="MIN_WORD_FREQUENCY",
        description="Minimum word frequency to include (0 = all words)"
    )
    
    max_flashcards: int = Field(
        default=0,
        ge=0,
        env="MAX_FLASHCARDS",
        description="Maximum flashcards per session (0 = unlimited)"
    )
    
    # =========================================================================
    # Streamlit UI Configuration
    # =========================================================================
    
    streamlit_server_port: int = Field(
        default=8501,
        ge=1024,
        le=65535,
        env="STREAMLIT_SERVER_PORT"
    )
    
    max_upload_size_mb: int = Field(
        default=200,
        ge=1,
        le=500,
        env="MAX_UPLOAD_SIZE_MB",
        description="Maximum file upload size in MB"
    )
    
    session_timeout_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        env="SESSION_TIMEOUT_MINUTES"
    )
    
    # =========================================================================
    # Advanced Settings
    # =========================================================================
    
    worker_threads: int = Field(
        default=4,
        ge=1,
        le=16,
        env="WORKER_THREADS",
        description="Number of worker threads for parallel processing"
    )
    
    cache_expiration_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        env="CACHE_EXPIRATION_HOURS",
        description="OCR result cache expiration in hours"
    )
    
    enable_experimental: bool = Field(
        default=False,
        env="ENABLE_EXPERIMENTAL",
        description="Enable experimental features"
    )
    
    # =========================================================================
    # Development Settings
    # =========================================================================
    
    dev_hot_reload: bool = Field(
        default=False,
        env="DEV_HOT_RELOAD",
        description="Enable hot reload for code changes (dev only)"
    )
    
    dev_enable_profiling: bool = Field(
        default=False,
        env="DEV_ENABLE_PROFILING",
        description="Enable profiling (dev only)"
    )
    
    dev_mock_apis: bool = Field(
        default=False,
        env="DEV_MOCK_APIS",
        description="Mock API calls for testing (dev only)"
    )
    
    # =========================================================================
    # Validators
    # =========================================================================
    
    @validator("default_ocr_engines", pre=True)
    def parse_ocr_engines(cls, v):
        """Parse comma-separated OCR engines"""
        if isinstance(v, str):
            return [engine.strip() for engine in v.split(",")]
        return v
    
    @validator("default_translator")
    def validate_translator(cls, v):
        """Validate translator choice"""
        allowed = ["deepl", "google", "local"]
        if v not in allowed:
            raise ValueError(f"Translator must be one of {allowed}")
        return v
    
    @validator("default_tokenizer")
    def validate_tokenizer(cls, v):
        """Validate tokenizer choice"""
        allowed = ["fugashi", "sudachi"]
        if v not in allowed:
            raise ValueError(f"Tokenizer must be one of {allowed}")
        return v
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def ensure_directories(self):
        """
        Create all necessary directories if they don't exist
        
        Usage:
            from config.settings import settings
            settings.ensure_directories()
        """
        directories = [
            self.data_dir,
            self.upload_dir,
            self.processing_dir,
            self.training_dir / "images",
            self.training_dir / "vocabulary",
            self.output_dir,
            self.models_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_ocr_selector_weights_path(self) -> Path:
        """Get path to OCR selector weights file"""
        return self.models_dir / "ocr_selector_weights.json"
    
    def get_session_dir(self, session_id: str) -> Path:
        """
        Get directory for a specific session
        
        Args:
            session_id: UUID of the session
            
        Returns:
            Path to session directory
        """
        return self.processing_dir / f"session_{session_id}"
    
    def is_api_configured(self, service: str) -> bool:
        """
        Check if API credentials are configured
        
        Args:
            service: Service name (deepl, google_vision, google_translate)
            
        Returns:
            True if credentials are configured
        """
        if service == "deepl":
            return self.deepl_api_key is not None
        elif service == "google_vision":
            return self.google_application_credentials is not None
        elif service == "google_translate":
            return (self.google_application_credentials is not None and
                    self.google_translate_project_id is not None)
        else:
            return False
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Allow extra fields for future compatibility
        extra = "allow"


# Global settings instance
# Import this in your modules:
# from config.settings import settings
settings = Settings()


# =========================================================================
# Usage Examples
# =========================================================================

if __name__ == "__main__":
    """
    Example usage of settings module
    Run: python -m config.settings
    """
    
    print("=" * 60)
    print("Japanese Flashcard ETL - Configuration")
    print("=" * 60)
    
    print(f"\nApplication: {settings.app_name} v{settings.app_version}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    
    print("\n" + "=" * 60)
    print("API Configuration")
    print("=" * 60)
    
    print(f"DeepL API: {'✓ Configured' if settings.is_api_configured('deepl') else '✗ Not configured'}")
    print(f"Google Vision: {'✓ Configured' if settings.is_api_configured('google_vision') else '✗ Not configured'}")
    print(f"Google Translate: {'✓ Configured' if settings.is_api_configured('google_translate') else '✗ Not configured'}")
    
    print("\n" + "=" * 60)
    print("OCR Configuration")
    print("=" * 60)
    
    print(f"Engines: {', '.join(settings.default_ocr_engines)}")
    print(f"Confidence Threshold: {settings.ocr_confidence_threshold:.0%}")
    print(f"GPU Enabled: {settings.use_gpu}")
    
    print("\n" + "=" * 60)
    print("Translation Configuration")
    print("=" * 60)
    
    print(f"Service: {settings.default_translator}")
    print(f"Target Language: {settings.translation_target_lang}")
    print(f"Batch Size: {settings.translation_batch_size}")
    print(f"Fallback to Local: {settings.translation_fallback_to_local}")
    
    print("\n" + "=" * 60)
    print("Data Directories")
    print("=" * 60)
    
    print(f"Data: {settings.data_dir}")
    print(f"Uploads: {settings.upload_dir}")
    print(f"Processing: {settings.processing_dir}")
    print(f"Training: {settings.training_dir}")
    print(f"Output: {settings.output_dir}")
    print(f"Models: {settings.models_dir}")
    
    print("\n" + "=" * 60)
    print("Processing Options")
    print("=" * 60)
    
    print(f"Include Context: {settings.include_context}")
    print(f"Deduplicate Cards: {settings.deduplicate_cards}")
    print(f"Min Word Frequency: {settings.min_word_frequency}")
    print(f"Max Flashcards: {settings.max_flashcards if settings.max_flashcards > 0 else 'Unlimited'}")
    
    print("\n" + "=" * 60)
    print("Creating Directories...")
    print("=" * 60)
    
    try:
        settings.ensure_directories()
        print("✓ All directories created successfully")
    except Exception as e:
        print(f"✗ Error creating directories: {e}")
    
    print()
