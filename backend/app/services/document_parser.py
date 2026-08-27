from __future__ import annotations

import base64
import io

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return _extract_pdf(content)
    if lower.endswith(".docx"):
        return _extract_docx(content)
    if lower.endswith((".txt", ".md")):
        return content.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {filename}")


def extract_images_from_pdf(content: bytes, max_pages: int = 10) -> list[str]:
    """Extract individual distinct embedded images and diagrams from PDF pages into base64 data URLs."""
    extracted_images: list[str] = []
    try:
        reader = PdfReader(io.BytesIO(content))
        for page_num, page in enumerate(reader.pages[:max_pages]):
            if hasattr(page, "images"):
                for img in page.images:
                    img_data = img.data
                    # Include diagrams and graphic elements down to 1.5 KB
                    if len(img_data) < 1500:
                        continue
                    mime = "image/png"
                    if img.name.lower().endswith((".jpg", ".jpeg")):
                        mime = "image/jpeg"
                    elif img.name.lower().endswith(".svg"):
                        mime = "image/svg+xml"
                    b64 = base64.b64encode(img_data).decode("utf-8")
                    extracted_images.append(f"data:{mime};base64,{b64}")
                    if len(extracted_images) >= 8:
                        break
            if len(extracted_images) >= 8:
                break
    except Exception:
        pass
    return extracted_images


def extract_images_from_docx(content: bytes) -> list[str]:
    """Extract embedded images and diagrams from DOCX documents into base64 data URLs."""
    extracted_images: list[str] = []
    try:
        doc = DocxDocument(io.BytesIO(content))
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                img_part = rel.target_part
                img_bytes = img_part.blob
                if len(img_bytes) < 1500:
                    continue
                content_type = img_part.content_type
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                extracted_images.append(f"data:{content_type};base64,{b64}")
                if len(extracted_images) >= 8:
                    break
    except Exception:
        pass
    return extracted_images


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
        if start <= 0:
            start = end
    return chunks
