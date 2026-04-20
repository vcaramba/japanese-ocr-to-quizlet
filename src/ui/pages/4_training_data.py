# src/ui/pages/4_training_data.py
import streamlit as st
from pathlib import Path
import pandas as pd
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from models.data_models import TrainingExample, VocabularyEntry, TextOrientation

st.title("🎓 Training Data Management")

st.markdown("""
Upload validated examples to improve OCR accuracy and vocabulary database.
""")

tab1, tab2, tab3 = st.tabs(["📷 OCR Examples", "📚 Vocabulary", "📊 Statistics"])

with tab1:
    st.subheader("Upload Validated OCR Examples")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        image_file = st.file_uploader("Book page image", type=['png', 'jpg', 'jpeg'])
        if image_file:
            st.image(image_file, caption="Uploaded image")
    
    with col2:
        ground_truth = st.text_area(
            "Ground truth text",
            height=200,
            help="Paste the correct text from this image"
        )
        
        orientation = st.selectbox(
            "Text orientation",
            [TextOrientation.VERTICAL, TextOrientation.HORIZONTAL, TextOrientation.AUTO_DETECT]
        )
        
        source_type = st.text_input(
            "Source type",
            placeholder="e.g., 'tategaki_novel', 'manga', 'textbook'"
        )
        
        if st.button("Save Training Example", type="primary"):
            if image_file and ground_truth:
                # Save image
                training_dir = Path("data/training/images")
                training_dir.mkdir(parents=True, exist_ok=True)
                
                image_path = training_dir / image_file.name
                image_path.write_bytes(image_file.read())
                
                # Create training example
                example = TrainingExample(
                    image_path=str(image_path),
                    ground_truth_text=ground_truth,
                    orientation=orientation,
                    source=source_type
                )
                
                # Save to JSON database
                db_path = Path("data/training/examples.jsonl")
                with open(db_path, "a") as f:
                    f.write(example.json() + "\n")
                
                st.success("Training example saved!")
            else:
                st.error("Please provide both image and ground truth text")

with tab2:
    st.subheader("Upload Vocabulary Database")
    
    st.markdown("Upload CSV with columns: `kanji`, `reading`, `translation`")
    
    vocab_file = st.file_uploader("Vocabulary CSV", type=['csv'])
    
    if vocab_file:
        df = pd.read_csv(vocab_file)
        st.dataframe(df.head(10))
        
        if st.button("Import Vocabulary"):
            vocab_dir = Path("data/training/vocabulary")
            vocab_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert to VocabularyEntry objects
            for _, row in df.iterrows():
                entry = VocabularyEntry(
                    kanji=row.get('kanji'),
                    kana=row.get('kana', row.get('reading', '')),
                    reading=row['reading'],
                    translation=row['translation'],
                    validated=True
                )
                
                # Append to database
                with open(vocab_dir / "validated_vocab.jsonl", "a") as f:
                    f.write(entry.json() + "\n")
            
            st.success(f"Imported {len(df)} vocabulary entries!")
    
    # Manual entry
    with st.expander("Add Single Entry"):
        col1, col2, col3 = st.columns(3)
        with col1:
            kanji = st.text_input("Kanji/Kana", key="vocab_kanji")
        with col2:
            reading = st.text_input("Reading", key="vocab_reading")
        with col3:
            translation = st.text_input("Translation", key="vocab_trans")
        
        if st.button("Add Entry"):
            if reading and translation:
                entry = VocabularyEntry(
                    kanji=kanji if kanji else None,
                    kana=reading,
                    reading=reading,
                    translation=translation,
                    validated=True
                )
                
                vocab_dir = Path("data/training/vocabulary")
                vocab_dir.mkdir(parents=True, exist_ok=True)
                with open(vocab_dir / "validated_vocab.jsonl", "a") as f:
                    f.write(entry.json() + "\n")
                
                st.success("Entry added!")

with tab3:
    st.subheader("Training Data Statistics")
    
    # Count training examples
    examples_path = Path("data/training/examples.jsonl")
    if examples_path.exists():
        examples_count = sum(1 for _ in open(examples_path))
        st.metric("OCR Training Examples", examples_count)
    
    # Count vocabulary entries
    vocab_path = Path("data/training/vocabulary/validated_vocab.jsonl")
    if vocab_path.exists():
        vocab_count = sum(1 for _ in open(vocab_path))
        st.metric("Vocabulary Entries", vocab_count)
    
    # Show distribution
    if examples_path.exists():
        examples = [TrainingExample.parse_raw(line) 
                   for line in open(examples_path)]
        
        orientation_dist = pd.DataFrame([
            {"Orientation": e.orientation.value} for e in examples
        ])
        
        st.bar_chart(orientation_dist['Orientation'].value_counts())