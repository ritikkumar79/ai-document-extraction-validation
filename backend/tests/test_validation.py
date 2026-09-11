
import pytest
from app.services.document_validation_service import validate_document, ValidationError

def test_empty_file():
    with pytest.raises(ValidationError) as exc:
        validate_document("x.pdf", b"", "application/pdf")
    assert exc.value.code == "EMPTY_FILE"

def test_unsupported_extension():
    with pytest.raises(ValidationError) as exc:
        validate_document("x.txt", b"hello", "text/plain")
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"
