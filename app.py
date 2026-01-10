import streamlit as st
import os
import json
import tempfile
from src.extractor import PDFExtractor
from src.utils import setup_logging

# Page Config
st.set_page_config(
    page_title="Bengali Voter List Extractor",
    page_icon="🇧🇩",
    layout="wide"
)

# Title and Intro
st.title("🇧🇩 Bengali Voter List Extractor")
st.write("Upload a scanned Voter List PDF to extract data into structured JSON.")

# Sidebar for options
with st.sidebar:
    st.header("Settings")
    use_ocr = st.checkbox("Enable OCR", value=True, help="Required for scanned PDFs")
    page_range = st.text_input("Page Range (Optional)", placeholder="e.g., 1-5 or 10", help="Leave empty to process all pages")

# File Uploader
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Display file info
    st.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
    
    # Save uploaded file to a temporary path because extractor expects a file path
    # and pdf2image requires a real path for Poppler usually.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # Extraction Button
    if st.button("Start Extraction", type="primary"):
        st_progress = st.progress(0, text="Initializing...")
        
        try:
            # Setup logging
            setup_logging("streamlit_extractor.log")
            
            # Initialize Extractor
            extractor = PDFExtractor(tmp_file_path, use_ocr=use_ocr)
            
            # Parse pages argument
            pages_arg = None
            if page_range:
                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                    pages_arg = range(start, end + 1)
                else:
                    pages_arg = [int(page_range)]
            
            # Run Extraction
            st_progress.progress(10, text="Analyzing PDF structure...")
            # Note: We can't easily hook into the progress inside extractor without modifying it to accept a callback.
            # For now, we just run it.
            st_progress.progress(25, text="Running Extraction (This may take a while for large files)...")
            
            data = extractor.process(pages=pages_arg)
            
            st_progress.progress(100, text="Extraction Complete!")
            st.success(f"Successfully extracted {len(data)} voters.")
            
            # Display Result
            st.subheader("Extracted Data Preview")
            st.json(data[:5] if len(data) > 5 else data)
            if len(data) > 5:
                st.caption(f"...and {len(data)-5} more items.")

            # Download Button
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name="output_voters.json",
                mime="application/json"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)
        
        finally:
            # Cleanup temp file
            try:
                os.remove(tmp_file_path)
            except:
                pass
