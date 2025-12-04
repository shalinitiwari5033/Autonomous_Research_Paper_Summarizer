import io
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF. This uses PyPDF2 if available; fallback to pdfminer.six.
    For scanned PDFs OCR is required (not included).
    """
    from PyPDF2 import PdfReader

    p = Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(pdf_path)

    text_parts = []
    try:
        reader = PdfReader(str(p))
        for page in reader.pages:
            try:
                txt = page.extract_text()
                if txt:
                    text_parts.append(txt)
            except Exception:
                continue
    except Exception:
        # Fallback to pdfminer (if installed)
        try:
            from pdfminer.high_level import extract_text
            txt = extract_text(str(p))
            if txt:
                text_parts.append(txt)
        except Exception:
            pass

    return "\n\n".join(text_parts)
