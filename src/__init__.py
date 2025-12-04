# This file makes the src folder a Python package.
# You can also define package-level imports here if needed.

from .pdf_extractor import extract_text_from_pdf
from .text_cleaner import clean_text
from .summarizer_model import generate_summary, extract_methodology, extract_contributions, extract_results
