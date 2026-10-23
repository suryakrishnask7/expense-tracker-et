from datetime import date
from app.models import db, Transaction, Category, rupees_to_paise
from app.routes.reports import sanitize_csv_cell


def test_reports_page_rendering(client, sample_transactions):
    """Test reports dashboard renders with metrics and breakdown tables."""
    response = client.get("/reports/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Reports & Analytics" in html
    assert "Expenses Grouped by Category" in html
    assert "Total Expenses" in html
    assert "Food &amp; Dining" in html or "Food & Dining" in html
    assert "Bills &amp; Utilities" in html or "Bills & Utilities" in html


def test_reports_preset_filters(client, sample_transactions):
    """Test preset time windows like this_week, this_month, and this_year."""
    res_week = client.get("/reports/?range=this_week")
    assert res_week.status_code == 200

    res_year = client.get("/reports/?range=this_year")
    assert res_year.status_code == 200


def test_csv_formula_injection_sanitization():
    """Verify that potentially dangerous spreadsheet formula triggers are prepended with single quotes."""
    # Equal sign
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    # Plus sign
    assert sanitize_csv_cell("+SUM(A1:B10)") == "'+SUM(A1:B10)"
    # Minus sign
    assert sanitize_csv_cell("-100") == "'-100"
    # At sign
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    # Tab / CR
    assert sanitize_csv_cell("\tTabbed") == "'\tTabbed"
    # Normal strings
    assert sanitize_csv_cell("Normal Text") == "Normal Text"
    assert sanitize_csv_cell("123.45") == "123.45"
    assert sanitize_csv_cell("") == ""
    assert sanitize_csv_cell(None) == ""


def test_csv_export_endpoint(client, app, sample_categories):
    """Test CSV export endpoint with proper headers and escaped formula data."""
    with app.app_context():
        food = Category.query.filter_by(name="Food & Dining").first()
        # Create a transaction with an injection payload
        txn = Transaction(
            type="expense",
            description="=1+1 Formula Injection Attempt",
            amount_paise=rupees_to_paise(150.00),
            category_id=food.id,
            transaction_date=date.today(),
            payment_method="Cash",
            notes="+cmd|' /C calc'!A0",
        )
        db.session.add(txn)
        db.session.commit()

    response = client.get("/reports/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["Content-Type"]
    assert "attachment; filename=" in response.headers["Content-Disposition"]

    csv_text = response.get_data(as_text=True)
    # Ensure header row is present
    assert "Transaction ID,Date,Type,Category,Description,Amount (INR),Payment Method,Notes,Created At" in csv_text
    # Ensure dangerous payload is safely neutralized with a leading single quote
    assert "'=1+1 Formula Injection Attempt" in csv_text
    assert "'+cmd|' /C calc'!A0" in csv_text
