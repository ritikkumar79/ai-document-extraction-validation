import json
from typing import Optional

from app.core.config import DATABASE_URL
from app.core.database import get_connection


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _placeholder() -> str:
    return "%s" if _is_postgres() else "?"


def upsert_document(result: dict):
    p = _placeholder()
    query = f"""
        INSERT INTO documents(
            document_name, document_type, processing_status,
            result_json, processed_at, processing_time_ms
        )
        VALUES ({p}, {p}, {p}, {p}, {p}, {p})
        ON CONFLICT(document_name) DO UPDATE SET
            document_type=excluded.document_type,
            processing_status=excluded.processing_status,
            result_json=excluded.result_json,
            processed_at=excluded.processed_at,
            processing_time_ms=excluded.processing_time_ms
    """
    values = (
        result["document_name"],
        result["document_type"],
        result["processing_status"],
        json.dumps(result),
        result["processing_metadata"]["processed_at"],
        result["processing_metadata"]["processing_time_ms"],
    )
    with get_connection() as conn:
        conn.execute(query, values)
        conn.commit()


def get_document(document_name: str) -> Optional[dict]:
    p = _placeholder()
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT result_json FROM documents WHERE document_name = {p}",
            (document_name,),
        ).fetchone()
    if not row:
        return None
    return json.loads(row["result_json"])


def list_documents():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT document_name, document_type, processing_status,
                   processed_at, processing_time_ms
            FROM documents ORDER BY processed_at DESC
        """).fetchall()
    return [dict(r) for r in rows]
