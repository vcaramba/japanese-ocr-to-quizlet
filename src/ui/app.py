# src/ui/app.py
import streamlit as st
from pathlib import Path
import os

st.set_page_config(
    page_title="Japanese Flashcard Generator",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None

st.title("🇯🇵 Japanese Flashcard Generator")
st.markdown("""
Generate Quizlet flashcards from Japanese book images with OCR validation.
Supports tategaki (vertical text), furigana, and mixed scripts.
""")

# Sidebar for navigation and settings
with st.sidebar:
    st.header("Navigation")
    st.page_link("pages/1_upload_and_process.py", label="📤 Upload & Process")
    st.page_link("pages/2_validate_ocr.py", label="✅ Validate OCR")
    st.page_link("pages/3_edit_flashcards.py", label="📝 Edit Flashcards")
    st.page_link("pages/4_training_data.py", label="🎓 Training Data")
    
    st.divider()
    
    st.header("Settings")
    st.selectbox("OCR Engines", ["All", "Tesseract + EasyOCR", "Manga-OCR Only"])
    st.slider("Confidence Threshold", 0.0, 1.0, 0.7)
    st.checkbox("Auto-translate", value=True)
    
    if st.session_state.session_id:
        st.divider()
        st.success(f"Session: {str(st.session_state.session_id)[:8]}...")
        if st.button("Clear Session"):
            st.session_state.session_id = None
            st.rerun()
