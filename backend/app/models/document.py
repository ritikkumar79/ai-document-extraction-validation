
from dataclasses import dataclass

@dataclass
class StoredDocument:
    document_name: str
    document_type: str
    processing_status: str
    result_json: str
    processed_at: str
    processing_time_ms: int
