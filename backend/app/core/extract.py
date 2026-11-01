import io
import zipfile
from pathlib import Path
from threading import Lock
import math
import pypdfium2 as pdfium
from docx import Document
from PIL import Image
from .ocr import recognize
from ..config import settings

Image.MAX_IMAGE_PIXELS = 24_000_000
PDF_LOCK = Lock()  # PDFium must not be called concurrently from extraction threads.


def extract_pdf(data):
    warnings = []
    with PDF_LOCK:
        try:
            doc = pdfium.PdfDocument(data)
        except pdfium.PdfiumError as exc:
            if exc.err_code == pdfium.raw.FPDF_ERR_PASSWORD:
                raise ValueError("This PDF is password-protected. Please upload an unlocked copy.") from None
            raise
        with doc:
            pages = len(doc)
            if pages > settings.max_pages:
                raise ValueError(f"Please upload at most {settings.max_pages} pages.")
            chunks = []
            characters = 0
            for index in range(pages):
                page = doc[index]
                try:
                    textpage = page.get_textpage()
                    try:
                        if textpage.count_chars() + characters > settings.max_chars:
                            raise ValueError("This document contains too much text. Please upload a shorter section.")
                        part = textpage.get_text_bounded()
                    finally:
                        textpage.close()
                    if len(part.strip()) < 30:
                        width, height = page.get_size()
                        if math.ceil(width * 2) * math.ceil(height * 2) > 24_000_000:
                            raise ValueError("A PDF page is too large to OCR safely.")
                        bitmap = page.render(scale=2)
                        try:
                            picture = bitmap.to_pil().copy()
                        finally:
                            bitmap.close()
                        try:
                            part, low = recognize(picture)
                        finally:
                            picture.close()
                        warnings.append("OCR used; compare extracted text with your original document.")
                        if low:
                            warnings.append("OCR confidence is low. Some text may be inaccurate.")
                    chunks.append(part)
                    characters += len(part)
                    if characters > settings.max_chars:
                        raise ValueError("This document contains too much text. Please upload a shorter section.")
                finally:
                    page.close()
            return "\f".join(chunks), pages, warnings


def extract(data: bytes, filename: str) -> tuple[str, int, list[str]]:
    """Validate magic bytes, extract in memory, and reject oversized expanded content."""
    ext = Path(filename).suffix.lower()
    warnings = []
    if not data or len(data) > settings.max_upload:
        raise ValueError("Please upload a non-empty file under the upload size limit.")
    try:
        pages = 1
        if ext == ".pdf" and data.startswith(b"%PDF-"):
            text, pages, warnings = extract_pdf(data)
        elif ext == ".docx" and data.startswith(b"PK\x03\x04"):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(z.file_size for z in archive.infolist()) > 20_000_000 or "word/document.xml" not in archive.namelist():
                    raise ValueError("This DOCX is invalid or too large when expanded.")
            doc = Document(io.BytesIO(data))
            text = "\n\n".join(
                [p.text for p in doc.paragraphs]
                + [" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows]
            )
            warnings.append("DOCX page numbers are approximate; pagination is not available.")
        elif ext in {".png", ".jpg", ".jpeg"} and (data.startswith(b"\x89PNG\r\n\x1a\n") or data.startswith(b"\xff\xd8\xff")):
            if (ext == ".png") != data.startswith(b"\x89PNG"):
                raise ValueError("The file extension does not match its image contents.")
            with Image.open(io.BytesIO(data)) as picture:
                if picture.width * picture.height > Image.MAX_IMAGE_PIXELS:
                    raise ValueError("Please upload an image smaller than 24 megapixels.")
                text, low = recognize(picture)
            warnings.append("OCR used; compare extracted text with your original document.")
            if low:
                warnings.append("OCR confidence is low. Please check the original.")
        elif ext == ".txt" and b"\x00" not in data:
            text = data.decode("utf-8-sig")
            if any(ord(c) < 32 and c not in "\r\n\t\f" for c in text):
                raise ValueError("Please upload a UTF-8 plain text file.")
        else:
            raise ValueError("File contents do not match a supported PDF, DOCX, TXT, PNG or JPG.")
        text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if len(text) > settings.max_chars or not text.strip():
            raise ValueError("No readable text was found, or the document is too long.")
        return text, pages, list(dict.fromkeys(warnings))
    except ValueError:
        raise
    except Exception:
        raise ValueError(
            "We could not read this file. It may be corrupt, or OCR is unavailable. Try a text-based PDF or TXT file."
        ) from None
