# file_loader.py
import fitz  # PyMuPDF
import docx2txt
import os
import tempfile

# Disable ICC warnings (optional)
fitz.TOOLS.set_icc(False)

def extract_from_pdf(file_bytes):
    """Extract text from PDF bytes"""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_from_docx(file_bytes):
    """Extract text from DOCX bytes"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    text = docx2txt.process(tmp_path)
    os.unlink(tmp_path)
    return text

def extract_from_txt(file_bytes):
    """Extract text from TXT bytes"""
    return file_bytes.decode('utf-8')

def load_file(uploaded_file):
    """Main entry: detect type and extract text"""
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)  # reset for later use
    name = uploaded_file.name
    ext = name.split('.')[-1].lower()
    
    if ext == 'pdf':
        return extract_from_pdf(file_bytes)
    elif ext == 'docx':
        return extract_from_docx(file_bytes)
    elif ext == 'txt':
        return extract_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")