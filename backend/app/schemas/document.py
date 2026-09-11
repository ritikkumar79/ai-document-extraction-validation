
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class FileValidation(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int
    status: str
    message: Optional[str] = None

class Evidence(BaseModel):
    source_text: Optional[str] = None
    page_number: Optional[int] = None

class ExtractedValue(BaseModel):
    value: Any = None
    confidence: Optional[float] = None
    evidence: Optional[Evidence] = None

class ValidationCheck(BaseModel):
    name: str
    formula: str
    operands: Dict[str, Any] = Field(default_factory=dict)
    calculated_value: Optional[float] = None
    reported_value: Optional[float] = None
    variance: Optional[float] = None
    tolerance: Optional[float] = None
    status: str
    message: Optional[str] = None

class ValidationResult(BaseModel):
    checks: List[ValidationCheck] = Field(default_factory=list)
    overall_status: str
    issues: List[str] = Field(default_factory=list)

class ProcessingMetadata(BaseModel):
    ocr_used: bool
    processed_at: str
    processing_time_ms: int
    extraction_engine: str
    llm_used: bool

class ProcessResponse(BaseModel):
    document_name: str
    document_type: str
    processing_status: str
    overall_confidence: Optional[float] = None
    file_validation: FileValidation
    extracted_data: Dict[str, Any]
    validation: ValidationResult
    processing_metadata: ProcessingMetadata

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
