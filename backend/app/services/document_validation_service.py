
import io
import mimetypes
from pathlib import Path
import fitz
from PIL import Image

SUPPORTED_MIME = {"application/pdf", "image/jpeg", "image/png"}
SUPPORTED_EXT = {".pdf", ".jpg", ".jpeg", ".png"}

class ValidationError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

def validate_document(filename: str, content: bytes, content_type: str, max_pages: int = 3):
    if not content:
        raise ValidationError("EMPTY_FILE", "The uploaded file is empty.")

    ext = Path(filename).suffix.lower()
    guessed = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    if ext not in SUPPORTED_EXT:
        raise ValidationError("UNSUPPORTED_FILE_TYPE", "Only PDF / JPG / PNG documents are supported.")

    page_count = 1
    readable = True
    detected_type = guessed

    try:
        if ext == ".pdf":
            doc = fitz.open(stream=content, filetype="pdf")
            page_count = len(doc)
            if page_count == 0:
                raise ValidationError("CORRUPTED_FILE", "The PDF contains no readable pages.")
            # Force page parsing to catch malformed PDFs.
            for p in doc:
                _ = p.get_text()
        else:
            img = Image.open(io.BytesIO(content))
            img.verify()
            detected_type = Image.MIME.get(img.format, guessed)
            page_count = 1
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("CORRUPTED_FILE", "The uploaded file is unreadable or corrupted.")

    if page_count > max_pages:
        raise ValidationError("PAGE_LIMIT_EXCEEDED", f"Documents are limited to {max_pages} pages.")

    return {
        "file_type": detected_type,
        "is_supported": True,
        "is_readable": readable,
        "page_count": page_count,
        "status": "PASS",
        "message": None,
    }
