"""MCP Tool: PDF Reader — Extracts text content from PDF files."""

import os


def read_pdf(file_path: str) -> dict:
    """
    Read and extract text from a PDF file.
    Uses PyPDF2 (free, open-source). Falls back gracefully if not installed.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        content = "\n\n".join(pages_text)
        return {
            "content": content.strip(),
            "pages": len(reader.pages),
            "chars": len(content),
            "file": os.path.basename(file_path),
            "type": "pdf",
        }
    except ImportError:
        return {"error": "PyPDF2 not installed. Run: pip install PyPDF2"}
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}
