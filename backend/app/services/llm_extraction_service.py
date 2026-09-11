
import json
import logging
import urllib.request
import urllib.error
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL, LLM_PROVIDER

logger = logging.getLogger(__name__)

def llm_extract(document_type: str, pages: list[tuple[int, str]]):
    if LLM_PROVIDER != "gemini" or not GEMINI_API_KEY:
        return None

    joined = "\n\n".join(f"[PAGE {p}]\n{text}" for p, text in pages)
    prompt = f"""
You are a financial document extraction engine.
Document type: {document_type}

Extract ALL meaningful information visible in the source text. Do not invent values.
Missing/unreadable values must be null. Preserve comparative periods and every financial line item.
For invoices, extract line_items as an array with description, quantity, unit_price, amount when present.
For financial statements, extract line_items as an array of label/value/period values.

Return ONLY valid JSON with this shape:
{{
  "document_type": "{document_type}",
  "fields": {{}},
  "line_items": []
}}

Source:
{joined}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode())
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as exc:
        logger.exception("LLM extraction failed: %s", exc)
        return None
