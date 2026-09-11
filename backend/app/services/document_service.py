
import logging
import time
from datetime import datetime, timezone
from app.core.config import MAX_FILE_SIZE_MB, MAX_PAGES
from app.services.document_validation_service import validate_document
from app.services.ocr_service import extract_text
from app.services.llm_extraction_service import llm_extract
from app.services.extraction_service import extract
from app.services.financial_validation_service import validate as validate_financial
from app.repositories.document_repository import upsert_document

logger = logging.getLogger(__name__)

def process_document(filename, content, content_type, document_type):
    started = time.perf_counter()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File exceeds the {MAX_FILE_SIZE_MB} MB size limit.")

    validation = validate_document(filename, content, content_type, MAX_PAGES)
    pages, ocr_used = extract_text(content, filename)

    if not any(text.strip() for _, text in pages):
        raise ValueError("No readable text could be extracted from the document.")

    llm_result = llm_extract(document_type, pages)
    extracted = extract(document_type, pages, llm_result)
    validation_result = validate_financial(document_type, extracted)

    elapsed = int((time.perf_counter() - started) * 1000)
    processed_at = datetime.now(timezone.utc).isoformat()

    confidence_values = []
    for value in extracted.values():
        if isinstance(value, dict) and isinstance(value.get("confidence"), (int, float)) and value["confidence"] > 0:
            confidence_values.append(value["confidence"])
    overall_confidence = round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else None

    result = {
        "document_name": filename,
        "document_type": document_type,
        "processing_status": "PASS" if validation_result["overall_status"] != "FAIL" else "FAILED",
        "overall_confidence": overall_confidence,
        "file_validation": validation,
        "extracted_data": extracted,
        "validation": validation_result,
        "processing_metadata": {
            "ocr_used": ocr_used,
            "processed_at": processed_at,
            "processing_time_ms": elapsed,
            "extraction_engine": "Gemini (optional) + deterministic parser",
            "llm_used": llm_result is not None,
        },
    }
    upsert_document(result)
    logger.info("Processed %s type=%s status=%s ms=%s", filename, document_type, result["processing_status"], elapsed)
    return result
