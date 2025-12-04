import streamlit as st
from pathlib import Path
from src.pdf_extractor import extract_text_from_pdf
from src.text_cleaner import clean_text, split_by_headings
from src.summarizer_model import (
    extract_methodology,
    extract_contributions,
    extract_results,
    generate_summary,
)

st.set_page_config(page_title="Autonomous Research Paper Summarizer", layout="wide")

st.title("Autonomous Research Paper Summarizer")
st.caption("Generates Methodology, Contributions, Results, and a concise Summary from uploaded research papers.")

sample_pdf_path = Path("data/HMM3.pdf")

# Sidebar / options
with st.sidebar:
    st.header("Options")
    use_openai = st.checkbox("Use OpenAI for abstractive summaries (optional)", value=False)


uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])

col1, col2 = st.columns([2,1])
with col1:
    if uploaded_file is None:
        st.info("You can also test with the sample PDF included in the project.")
        if st.button("Use sample PDF"):
            uploaded_path = sample_pdf_path
        else:
            uploaded_path = None
    else:
        # Save the uploaded file to a temp path for processing
        tmp_dir = Path("data")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = tmp_dir / uploaded_file.name
        with open(tmp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())
        uploaded_path = tmp_file

    if uploaded_path:
        st.info(f"Processing: `{uploaded_path}`")
        # Extract and process
        with st.spinner("Extracting text from PDF..."):
            try:
                raw = extract_text_from_pdf(str(uploaded_path))
            except Exception as e:
                st.error("Could not extract text from PDF: " + str(e))
                raw = ""
        if not raw.strip():
            st.warning("No text found or extraction failed. If this is a scanned PDF, OCR is required (not included).")

        # Clean
        with st.spinner("Cleaning text..."):
            cleaned = clean_text(raw)

        # Show word/page stats                          
        words = len(cleaned.split())
        st.write(f"**Word count (approx):** {words}")

        # Extract sections by headings heuristics
        headings = split_by_headings(cleaned)

        # Generate outputs
        with st.spinner("Generating Methodology, Contributions, Results and Summary..."):
            methodology = extract_methodology(cleaned, headings=headings, use_openai=use_openai)
            contributions = extract_contributions(cleaned, headings=headings, use_openai=use_openai)
            results = extract_results(cleaned, headings=headings, use_openai=use_openai)
            summary = generate_summary(cleaned, use_openai=use_openai)

        # Display in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Methodology", "Contributions", "Results"])
        with tab1:
            st.header("Summary")
            st.write(summary)
            st.download_button("Download Summary", data=summary, file_name="summary.txt", mime="text/plain")
        with tab2:
            st.header("Methodology")
            st.write(methodology)
            st.download_button("Download Methodology", data=methodology, file_name="methodology.txt", mime="text/plain")
        with tab3:
            st.header("Contributions")
            st.write(contributions)
            st.download_button("Download Contributions", data=contributions, file_name="contributions.txt", mime="text/plain")
        with tab4:
            st.header("Results")
            st.write(results)
            st.download_button("Download Results", data=results, file_name="results.txt", mime="text/plain")

        st.markdown("---")
        st.write("**Full extracted text (hidden by default)**")
        if st.checkbox("Show full extracted text"):
            st.text_area("Extracted text", value=cleaned[:100000], height=400)

    else:
     st.write("Upload a PDF to start (or use the sample).")