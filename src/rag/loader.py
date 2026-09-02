from pypdf import PdfReader
from docx import Document


def load_text(path):
    with open(path, "r") as f:
        return f.read()


def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def load_docx(path):
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return text


def load_document(path):
    if path.endswith(".md") or path.endswith(".txt"):
        return load_text(path)
    elif path.endswith(".pdf"):
        return load_pdf(path)
    elif path.endswith(".docx"):
        return load_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")
