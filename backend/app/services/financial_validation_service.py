
from math import isclose
from app.services.extraction_service import numeric

DEFAULT_TOLERANCE = 1.0

def check(name, formula, operands, calculated, reported, tolerance=DEFAULT_TOLERANCE):
    if calculated is None or reported is None:
        return {
            "name": name, "formula": formula, "operands": operands,
            "calculated_value": calculated, "reported_value": reported,
            "variance": None, "tolerance": tolerance,
            "status": "NOT_APPLICABLE",
            "message": "Required source fields are not present."
        }
    variance = round(calculated - reported, 2)
    status = "PASS" if abs(variance) <= tolerance else "FAIL"
    return {
        "name": name, "formula": formula, "operands": operands,
        "calculated_value": round(calculated, 2),
        "reported_value": round(reported, 2),
        "variance": variance, "tolerance": tolerance, "status": status,
        "message": None if status == "PASS" else f"Variance {variance} exceeds tolerance {tolerance}."
    }

def validate(document_type, extracted):
    checks = []

    if document_type == "invoice":
        sub = numeric(extracted, "subtotal")
        tax = numeric(extracted, "tax_amount")
        disc = numeric(extracted, "discount")
        total = numeric(extracted, "total_amount")
        if sub is not None and tax is not None and disc is not None and total is not None:
            checks.append(check(
                "invoice_total_check",
                "subtotal + tax_amount - discount",
                {"subtotal": sub, "tax_amount": tax, "discount": disc},
                sub + tax - disc, total
            ))
        else:
            checks.append(check("invoice_total_check", "subtotal + tax_amount - discount",
                                {"subtotal": sub, "tax_amount": tax, "discount": disc},
                                None, total))
        line_items = extracted.get("line_items") or []
        if line_items and sub is not None:
            line_sum = sum(i.get("amount") or 0 for i in line_items if isinstance(i, dict))
            checks.append(check("invoice_line_items_subtotal", "sum(line_item.amount)",
                                {"line_item_amounts": [i.get("amount") for i in line_items]},
                                line_sum, sub))

    elif document_type == "balance_sheet":
        assets = numeric(extracted, "total_assets")
        liabilities = numeric(extracted, "total_liabilities")
        equity = numeric(extracted, "total_equity")
        checks.append(check("balance_sheet_equation",
                            "total_liabilities + total_equity",
                            {"total_liabilities": liabilities, "total_equity": equity},
                            liabilities + equity if liabilities is not None and equity is not None else None,
                            assets))

    elif document_type == "profit_and_loss":
        revenue = numeric(extracted, "revenue")
        cogs = numeric(extracted, "cost_of_sales")
        gross = numeric(extracted, "gross_profit")
        opex = numeric(extracted, "operating_expenses")
        op_profit = numeric(extracted, "operating_profit")
        tax = numeric(extracted, "tax")
        net = numeric(extracted, "net_profit")
        checks.append(check("gross_profit_check", "revenue - cost_of_sales",
                            {"revenue": revenue, "cost_of_sales": cogs},
                            revenue - cogs if revenue is not None and cogs is not None else None, gross))
        checks.append(check("operating_profit_check", "gross_profit - operating_expenses",
                            {"gross_profit": gross, "operating_expenses": opex},
                            gross - opex if gross is not None and opex is not None else None, op_profit))
        checks.append(check("net_profit_check", "operating_profit - tax",
                            {"operating_profit": op_profit, "tax": tax},
                            op_profit - tax if op_profit is not None and tax is not None else None, net))

    elif document_type == "cash_flow_statement":
        op = numeric(extracted, "operating_cash_flow")
        inv = numeric(extracted, "investing_cash_flow")
        fin = numeric(extracted, "financing_cash_flow")
        net = numeric(extracted, "net_change_in_cash")
        opening = numeric(extracted, "opening_cash")
        closing = numeric(extracted, "closing_cash")
        checks.append(check("net_change_in_cash_check",
                            "operating_cash_flow + investing_cash_flow + financing_cash_flow",
                            {"operating_cash_flow": op, "investing_cash_flow": inv, "financing_cash_flow": fin},
                            op + inv + fin if op is not None and inv is not None and fin is not None else None, net))
        checks.append(check("closing_cash_check",
                            "opening_cash + net_change_in_cash",
                            {"opening_cash": opening, "net_change_in_cash": net},
                            opening + net if opening is not None and net is not None else None, closing))

    applicable = [c for c in checks if c["status"] != "NOT_APPLICABLE"]
    overall = "FAIL" if any(c["status"] == "FAIL" for c in checks) else ("PASS" if applicable else "NOT_APPLICABLE")
    issues = [c["message"] for c in checks if c.get("message")]
    return {"checks": checks, "overall_status": overall, "issues": issues}
