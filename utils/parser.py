"""
utils/parser.py
Handles resume (PDF/DOCX) and plain text JD extraction.
"""

import pdfplumber
import docx
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file given its raw bytes."""
    text = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file given its raw bytes."""
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs).strip()


def parse_resume(uploaded_file) -> str:
    """
    Parse an uploaded Streamlit file object.
    Supports PDF and DOCX. Returns extracted text or raises ValueError.
    """
    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.read()
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")