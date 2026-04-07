# src/ui/pages/1_upload_and_process.py
import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from pipeline import FlashcardPipeline
from models.data_models import ProcessingSession

st.title("📤 Upload & Process Documents")

# File upload
uploaded_files = st.file_uploader(
    "Upload Japanese book pages (PDF or images)",
    type=['pdf', 'png', 'jpg', 'jpeg'],
    accept_multiple_files=True
)

# Text orientation hint
orientation = st.radio(
    "Text orientation",
    ["Auto-detect", "Vertical (tategaki)", "Horizontal (yokogaki)"],
    horizontal=True
)

# Processing options
with st.expander("Advanced Options"):
    col1, col2 = st.columns(2)
    with col1:
        ocr_engines = st.multiselect(
            "OCR Engines",
            ["Tesseract", "EasyOCR"],
            default=["EasyOCR"]
        )
    with col2:
        create_context = st.checkbox("Include context sentences", value=True)
        deduplicate = st.checkbox("Remove duplicate cards", value=True)

if st.button("🚀 Process Documents", type="primary", disabled=not uploaded_files):
    with st.spinner("Processing..."):
        # Save uploaded files
        session = ProcessingSession(source_files=[f.name for f in uploaded_files])
        st.session_state.session_id = session.session_id
        
        # Initialize pipeline
        pipeline = FlashcardPipeline(
            ocr_engines=ocr_engines,
            orientation_hint=orientation
        )
        
        # Process each file
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Processing {file.name}...")
            
            # Save temp file and process
            temp_path = Path(f"data/uploads/{file.name}")
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_bytes(file.read())
            
            # Run pipeline (non-blocking preview)
            result = pipeline.process_document(str(temp_path))
            session.page_extractions.extend(result.page_extractions)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status_text.text("Processing complete!")
        st.success(f"Extracted {len(session.page_extractions)} pages. Proceed to validation.")
        
        # Save session
        session_path = Path(f"data/processing/session_{session.session_id}")
        session_path.mkdir(parents=True, exist_ok=True)
        (session_path / "session.json").write_text(session.json())
        
        st.session_state.processing_status = "validating"

# Show current session status
if st.session_state.session_id:
    st.divider()
    st.subheader("Current Session")
    
    session_path = Path(f"data/processing/session_{st.session_state.session_id}")
    if session_path.exists():
        session_data = ProcessingSession.parse_file(session_path / "session.json")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Pages Processed", len(session_data.page_extractions))
        col2.metric("Validated", sum(1 for p in session_data.page_extractions 
                                     if p.validation_status.value == "validated"))
        col3.metric("Pending", sum(1 for p in session_data.page_extractions 
                                   if p.validation_status.value == "pending"))