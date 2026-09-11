
import re
from typing import Any

MONEY_RE = re.compile(r"[-(]?\s*[$€£₹]?\s*[\d,]+(?:\.\d+)?\s*\)?")

LABEL_MAP = {
    "invoice_number": [r"invoice\s*(?:no|number|#)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"],
    "invoice_date": [r"invoice\s*date\s*[:\-]?\s*([0-9]{1,4}[\/\-][0-9]{1,2}[\/\-][0-9]{1,4})"],
    "vendor_name": [r"(?:vendor|seller|from)\s*[:\-]\s*([^\n]+)"],
    "customer_name": [r"(?:customer|bill\s*to|client)\s*[:\-]\s*([^\n]+)"],
    "currency": [r"(?:currency)\s*[:\-]\s*([A-Z]{3})", r"\b(USD|EUR|GBP|INR|JPY|AUD|CAD)\b"],
    "subtotal": [r"sub\s*total\s*[:\-]?\s*([^\n]+)", r"subtotal\s*[:\-]?\s*([^\n]+)"],
    "tax_amount": [r"(?:tax|gst|vat)\s*(?:amount)?\s*[:\-]?\s*([^\n]+)"],
    "discount": [r"discount\s*[:\-]?\s*([^\n]+)"],
    "total_amount": [r"(?:^|\n)\s*(?:grand\s*total|total\s*amount|amount\s*due|total)\s*[:\-]?\s*([^\n]+)"],
    "revenue": [r"(?:revenue|sales)\s*[:\-]?\s*([^\n]+)"],
    "cost_of_sales": [r"(?:cost\s*of\s*(?:sales|goods\s*sold)|cogs)\s*[:\-]?\s*([^\n]+)"],
    "gross_profit": [r"gross\s*profit\s*[:\-]?\s*([^\n]+)"],
    "operating_expenses": [r"operating\s*expenses?\s*[:\-]?\s*([^\n]+)"],
    "operating_profit": [r"operating\s*profit\s*[:\-]?\s*([^\n]+)"],
    "tax": [r"(?:tax|income\s*tax)\s*[:\-]?\s*([^\n]+)"],
    "net_profit": [r"(?:net\s*profit|net\s*income|profit\s*after\s*tax)\s*[:\-]?\s*([^\n]+)"],
    "total_assets": [r"total\s*assets?\s*[:\-]?\s*([^\n]+)"],
    "total_liabilities": [r"total\s*liabilit(?:y|ies)\s*[:\-]?\s*([^\n]+)"],
    "total_equity": [r"(?:total\s*equity|shareholders?\s*equity)\s*[:\-]?\s*([^\n]+)"],
    "operating_cash_flow": [r"(?:operating\s*cash\s*flow|net\s*cash.*operating)\s*[:\-]?\s*([^\n]+)"],
    "investing_cash_flow": [r"(?:investing\s*cash\s*flow|net\s*cash.*investing)\s*[:\-]?\s*([^\n]+)"],
    "financing_cash_flow": [r"(?:financing\s*cash\s*flow|net\s*cash.*financing)\s*[:\-]?\s*([^\n]+)"],
    "opening_cash": [r"(?:opening|beginning)\s*cash(?:\s*and\s*cash\s*equivalents?)?\s*[:\-]?\s*([^\n]+)"],
    "net_change_in_cash": [r"(?:net\s*(?:change|increase|decrease)\s*in\s*cash)\s*[:\-]?\s*([^\n]+)"],
    "closing_cash": [r"(?:closing|ending)\s*cash(?:\s*and\s*cash\s*equivalents?)?\s*[:\-]?\s*([^\n]+)"],
}

def _number(value):
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    negative = "(" in s and ")" in s
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    if not m:
        return None
    n = float(m.group())
    return -abs(n) if negative else n

def _evidence(pages, pattern):
    for page_no, text in pages:
        for line in text.splitlines():
            if re.search(pattern, line, re.I):
                return line.strip(), page_no
    return None, None

def _extract_label(key, pages):
    patterns = LABEL_MAP.get(key, [])
    for pattern in patterns:
        for page_no, text in pages:
            m = re.search(pattern, text, re.I)
            if m:
                raw = m.group(1).strip()
                evidence = next((ln.strip() for ln in text.splitlines() if re.search(pattern, ln, re.I)), raw)
                if key in {"invoice_number", "invoice_date", "vendor_name", "customer_name", "currency"}:
                    value = raw.splitlines()[0].strip()
                else:
                    value = _number(raw)
                return {"value": value, "confidence": 0.85, "evidence": {"source_text": evidence, "page_number": page_no}}
    return {"value": None, "confidence": 0.0, "evidence": None}

def _all_financial_lines(pages):
    items = []
    known = re.compile(r"^\s*([A-Za-z][A-Za-z0-9&(),./' \-]{2,})\s{1,}(\(?\s*[$€£₹]?\s*[\d,]+(?:\.\d+)?\s*\)?)\s*$")
    for page_no, text in pages:
        for line in text.splitlines():
            line = line.strip()
            m = known.match(line)
            if m:
                label = re.sub(r"\s+", " ", m.group(1)).strip()
                value = _number(m.group(2))
                if value is not None and label.lower() not in {"page", "invoice"}:
                    items.append({"label": label, "value": value, "page_number": page_no})
    return items

def _invoice_line_items(pages):
    items = []
    # Flexible extraction for rows such as "Service A 2 100.00 200.00"
    row = re.compile(r"^\s*(.+?)\s+(\d+(?:\.\d+)?)\s+([$€£₹]?\s*[\d,]+(?:\.\d+)?)\s+([$€£₹]?\s*[\d,]+(?:\.\d+)?)\s*$")
    for page_no, text in pages:
        for line in text.splitlines():
            m = row.match(line.strip())
            if m:
                items.append({
                    "description": m.group(1).strip(),
                    "quantity": float(m.group(2)),
                    "unit_price": _number(m.group(3)),
                    "amount": _number(m.group(4)),
                    "page_number": page_no
                })
    return items

def extract(document_type, pages, llm_result=None):
    if llm_result and isinstance(llm_result, dict):
        fields = llm_result.get("fields", {})
        line_items = llm_result.get("line_items", [])
        result = {}
        for k, v in fields.items():
            if isinstance(v, dict) and "value" in v:
                result[k] = v
            else:
                result[k] = {"value": v, "confidence": None, "evidence": None}
        result["line_items"] = line_items
        # Fill required keys not returned by LLM with nulls, never invent.
    else:
        result = {}

    for key in [
        "invoice_number","invoice_date","vendor_name","customer_name","currency",
        "subtotal","tax_amount","discount","total_amount",
        "revenue","cost_of_sales","gross_profit","operating_expenses","operating_profit","tax","net_profit",
        "total_assets","total_liabilities","total_equity",
        "operating_cash_flow","investing_cash_flow","financing_cash_flow","opening_cash","net_change_in_cash","closing_cash"
    ]:
        if key not in result or result[key].get("value") is None:
            result[key] = _extract_label(key, pages)

    result.setdefault("statement_title", {"value": _title(document_type), "confidence": 0.75, "evidence": None})
    result.setdefault("periods", {"value": _periods(pages), "confidence": 0.70, "evidence": None})
    result.setdefault("line_items", _all_financial_lines(pages))
    if document_type == "invoice" and not result["line_items"]:
        result["line_items"] = _invoice_line_items(pages)

    # Remove unrelated minimum fields only at display level? Keep extracted fields comprehensive.
    return result

def _title(document_type):
    return {
        "invoice": "Invoice",
        "balance_sheet": "Balance Sheet",
        "profit_and_loss": "Profit and Loss",
        "cash_flow_statement": "Cash Flow Statement",
    }.get(document_type, document_type)

def _periods(pages):
    text = "\n".join(t for _, t in pages)
    matches = re.findall(r"\b(?:19|20)\d{2}\b", text)
    return list(dict.fromkeys(matches))

def numeric(extracted, key):
    value = extracted.get(key, {}).get("value") if isinstance(extracted.get(key), dict) else None
    return float(value) if isinstance(value, (int, float)) else None
