# src/ui/pages/3_edit_flashcards.py
import streamlit as st
from pathlib import Path
import pandas as pd
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from models.data_models import ProcessingSession, Flashcard
from pipeline import FlashcardPipeline

st.title("📝 Edit Flashcards")

if not st.session_state.session_id:
    st.warning("No active session.")
    st.stop()

session_path = Path(f"data/processing/session_{st.session_state.session_id}")
session = ProcessingSession.parse_file(session_path / "session.json")

# Generate flashcards if not already done
if not session.flashcard_set:
    with st.spinner("Generating flashcards from validated OCR..."):
        pipeline = FlashcardPipeline()
        session.flashcard_set = pipeline.generate_flashcards(session)
        (session_path / "session.json").write_text(session.json())

flashcards = session.flashcard_set.cards

# Filter controls
col1, col2, col3 = st.columns(3)
with col1:
    show_only = st.selectbox("Show", ["All", "Pending Review", "Low Confidence"])
with col2:
    sort_by = st.selectbox("Sort by", ["Order", "Confidence", "Frequency"])
with col3:
    search = st.text_input("Search", placeholder="Filter cards...")

# Filter flashcards
filtered_cards = flashcards
if show_only == "Pending Review":
    filtered_cards = [c for c in flashcards if not c.user_edited]
elif show_only == "Low Confidence":
    filtered_cards = [c for c in flashcards if c.confidence_score < 0.7]

if search:
    filtered_cards = [c for c in filtered_cards 
                     if search.lower() in c.front.lower() or 
                        search.lower() in c.back_translation.lower()]

st.caption(f"Showing {len(filtered_cards)} of {len(flashcards)} cards")

# Editable table
df = pd.DataFrame([
    {
        "Front (Kanji/Kana)": c.front,
        "Reading": c.back_reading,
        "Translation": c.back_translation,
        "Confidence": f"{c.confidence_score:.0%}",
        "ID": c.id
    }
    for c in filtered_cards
])

edited_df = st.data_editor(
    df,
    hide_index=True,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Confidence": st.column_config.ProgressColumn(
            "Confidence",
            min_value=0,
            max_value=1,
        )
    }
)

# Save changes
if st.button("💾 Save Changes", type="primary"):
    # Update flashcards from edited dataframe
    for idx, row in edited_df.iterrows():
        card = next(c for c in flashcards if c.id == row["ID"])
        card.front = row["Front (Kanji/Kana)"]
        card.back_reading = row["Reading"]
        card.back_translation = row["Translation"]
        card.user_edited = True
    
    (session_path / "session.json").write_text(session.json())
    st.success("Changes saved!")

# Export section
st.divider()
st.subheader("📥 Export")


if st.button("Export to Quizlet CSV", use_container_width=True):
    csv_data = session.flashcard_set.to_quizlet_csv()
    st.download_button(
            "Download CSV",
            csv_data,
            f"flashcards_{session.session_id}.csv",
            "text/csv"
    )
        