"""
modules/parser.py
Resume file parsing — supports PDF and DOCX.
"""

import io


def parse_uploaded_file(uploaded_file) -> tuple[str, str]:
    """
    Parse a Streamlit UploadedFile object.
    Returns (extracted_text, error_message).
    On success, error_message is "".
    On failure, extracted_text is "".
    """
    if uploaded_file is None:
        return "", "No file provided."

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    if filename.endswith(".pdf"):
        return _parse_pdf(file_bytes)
    elif filename.endswith(".docx"):
        return _parse_docx(file_bytes)
    else:
        return "", "Unsupported format. Please upload a PDF or DOCX file."


def _parse_pdf(file_bytes: bytes) -> tuple[str, str]:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n".join(text_parts).strip()
        if not text:
            return "", "Could not extract text from the PDF. Try a non-scanned PDF."
        return text, ""
    except Exception as e:
        return "", f"PDF parsing error: {e}"


def _parse_docx(file_bytes: bytes) -> tuple[str, str]:
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs).strip()
        if not text:
            return "", "Could not extract text from the DOCX file."
        return text, ""
    except Exception as e:
        return "", f"DOCX parsing error: {e}"