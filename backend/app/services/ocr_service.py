
import io
import logging
import fitz
from PIL import Image

logger = logging.getLogger(__name__)

def extract_text(content: bytes, filename: str):
    """Return [(page_number, text)] and whether OCR was used."""
    is_pdf = filename.lower().endswith(".pdf")
    pages = []
    ocr_used = False

    if is_pdf:
        doc = fitz.open(stream=content, filetype="pdf")
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                pages.append((i, text))
            else:
                text = _ocr_image(page.get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png"))
                pages.append((i, text))
                ocr_used = True
        return pages, ocr_used

    image = Image.open(io.BytesIO(content))
    text = _ocr_pil(image)
    return [(1, text)], True

def _ocr_image(png_bytes):
    return _ocr_pil(Image.open(io.BytesIO(png_bytes)))

def _ocr_pil(image):
    try:
        import pytesseract
        return pytesseract.image_to_string(image)
    except Exception as exc:
        logger.warning("Tesseract unavailable: %s", exc)
        return ""
