
import logging
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.schemas.extraction import SUPPORTED_DOCUMENT_TYPES
from app.services.document_service import process_document
from app.services.document_validation_service import ValidationError
from app.repositories.document_repository import get_document, list_documents

router = APIRouter(tags=["documents"])
logger = logging.getLogger(__name__)

@router.post("/documents/process")
async def process(file: UploadFile = File(...), document_type: str = Form(...)):
    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_DOCUMENT_TYPE", "message": "Unsupported document_type."}
        })
    content = await file.read()
    try:
        return process_document(file.filename or "uploaded_document", content, file.content_type, document_type)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": exc.code, "message": exc.message}})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "PROCESSING_ERROR", "message": str(exc)}})
    except Exception:
        logger.exception("Unexpected processing failure")
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INTERNAL_PROCESSING_ERROR", "message": "The document could not be processed."}
        })

@router.get("/documents/{document_name}")
def get_by_name(document_name: str):
    result = get_document(document_name)
    if not result:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "DOCUMENT_NOT_FOUND", "message": "No processed document with this name was found."}
        })
    return result

@router.get("/documents")
def get_all():
    return {"documents": list_documents()}
