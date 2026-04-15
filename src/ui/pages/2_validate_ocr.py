# src/ui/pages/2_validate_ocr.py
import streamlit as st
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from models.data_models import ProcessingSession, ValidationStatus
from PIL import Image

st.title("✅ Validate OCR Results")

if not st.session_state.session_id:
    st.warning("No active session. Please upload documents first.")
    st.page_link("pages/1_upload_and_process.py", label="Go to Upload")
    st.stop()

# Load session
session_path = Path(f"data/processing/session_{st.session_state.session_id}")
session = ProcessingSession.parse_file(session_path / "session.json")

# Page selector
pending_pages = [p for p in session.page_extractions 
                 if p.validation_status == ValidationStatus.PENDING]

if not pending_pages:
    st.success("All pages validated! Proceed to flashcard editing.")
    st.page_link("pages/3_edit_flashcards.py", label="Edit Flashcards →")
    st.stop()

page_idx = st.selectbox(
    "Select page to validate",
    range(len(pending_pages)),
    format_func=lambda i: f"Page {(pending_pages[i].page_number or i) + 1}"
)

current_page = pending_pages[page_idx]

# Display image and OCR results side-by-side
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Original Image")
    image = Image.open(current_page.image_path)
    st.image(image, use_container_width=True)
    
    st.caption(f"Detected orientation: {current_page.orientation.value}")

with col2:
    st.subheader("OCR Results")
    
    # Show all OCR engine results
    
    if current_page.ocr_consensus and current_page.ocr_consensus.best_result:
        result = current_page.ocr_consensus.best_result
        
        with st.expander(
                f"{result.engine} (confidence: {result.confidence:.2%})",
                expanded=(result.engine == current_page.ocr_consensus.selected_engine)
            ):
                st.code(result.text, language=None)
                if st.button(f"Use {result.engine}", key=f"use_{result.engine}"):
                    current_page.ocr_consensus.selected_text = result.text
                    current_page.ocr_consensus.selected_engine = result.engine
    
        st.divider()

        # Manual correction
        st.subheader("Corrected Text")
        corrected_text = st.text_area(
            "Edit if needed",
            value=current_page.ocr_consensus.corrected_text or 
              current_page.ocr_consensus.selected_text,
            height=200,
            key="correction"
        )
    else:
        st.warning("No OCR results available for this page.")
        corrected_text = st.text_area(
            "Enter text manually",
            height=200,
            key="manual_entry"
        )    
    
    
    notes = st.text_input("Notes (optional)", key="notes")

# Validation actions
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("✅ Approve", type="primary", use_container_width=True):
        current_page.ocr_consensus.validation_status = ValidationStatus.VALIDATED
        if corrected_text != current_page.ocr_consensus.selected_text:
            current_page.ocr_consensus.corrected_text = corrected_text
            current_page.ocr_consensus.validation_status = ValidationStatus.CORRECTED
        current_page.ocr_consensus.user_notes = notes
        current_page.validation_status = ValidationStatus.VALIDATED
        
        # Save session
        (session_path / "session.json").write_text(session.json(), encoding='utf-8')
        st.success("Page validated!")
        st.rerun()

with col2:
    if st.button("⏭️ Skip", use_container_width=True):
        st.rerun()

with col3:
    if st.button("❌ Reject", use_container_width=True):
        current_page.validation_status = ValidationStatus.REJECTED
        (session_path / "session.json").write_text(session.json(), encoding='utf-8')
        st.rerun()

# Progress indicator
st.divider()
validated = len([p for p in session.page_extractions 
                if p.validation_status == ValidationStatus.VALIDATED])
total = len(session.page_extractions)
st.progress(validated / total)
st.caption(f"Progress: {validated}/{total} pages validated")