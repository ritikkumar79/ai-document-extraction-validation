
from app.services.extraction_service import extract
from app.services.financial_validation_service import validate

def test_invoice_extraction_and_validation():
    pages = [(1, """
    Invoice Number: INV-100
    Invoice Date: 2026-08-15
    Vendor: ABC Technologies
    Customer: Demo Corp
    Currency: USD
    Subtotal: 1000.00
    Tax: 100.00
    Discount: 0.00
    Total Amount: 1100.00
    """)]
    data = extract("invoice", pages)
    result = validate("invoice", data)
    assert data["invoice_number"]["value"] == "INV-100"
    assert result["overall_status"] == "PASS"
