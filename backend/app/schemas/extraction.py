
SUPPORTED_DOCUMENT_TYPES = {
    "invoice",
    "balance_sheet",
    "profit_and_loss",
    "cash_flow_statement",
}

MINIMUM_FIELDS = {
    "invoice": [
        "invoice_number", "invoice_date", "vendor_name", "customer_name",
        "currency", "subtotal", "tax_amount", "discount", "total_amount", "line_items"
    ],
    "balance_sheet": [
        "statement_title", "periods", "currency", "line_items",
        "total_assets", "total_liabilities", "total_equity"
    ],
    "profit_and_loss": [
        "statement_title", "periods", "currency", "line_items",
        "revenue", "cost_of_sales", "gross_profit", "operating_expenses",
        "operating_profit", "tax", "net_profit"
    ],
    "cash_flow_statement": [
        "statement_title", "periods", "currency", "line_items",
        "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
        "opening_cash", "net_change_in_cash", "closing_cash"
    ],
}
