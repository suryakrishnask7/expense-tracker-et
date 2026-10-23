from datetime import date, timedelta
from app.models import db, Transaction, Category, paise_to_rupees, rupees_to_paise


def test_create_income_transaction(client, app, sample_categories):
    """Test creating an income transaction and verifying database persistence."""
    with app.app_context():
        salary_cat = Category.query.filter_by(name="Salary").first()

        data = {
            "type": "income",
            "amount": "65000.00",
            "description": "Consulting Retainer Fee",
            "category_id": salary_cat.id,
            "transaction_date": "2026-10-15",
            "payment_method": "Net Banking",
            "notes": "Q4 retainer",
        }
        response = client.post("/transactions/new", data=data, follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Successfully recorded income of" in html
        assert "Consulting Retainer Fee" in html

        # Verify database record directly
        txn = Transaction.query.filter_by(description="Consulting Retainer Fee").first()
        assert txn is not None
        assert txn.type == "income"
        assert txn.amount_paise == 6500000
        assert txn.payment_method == "Net Banking"
        assert txn.category_id == salary_cat.id


def test_create_expense_transaction(client, app, sample_categories):
    """Test creating an expense transaction with decimal rupees."""
    with app.app_context():
        food_cat = Category.query.filter_by(name="Food & Dining").first()

        data = {
            "type": "expense",
            "amount": "450.75",
            "description": "Lunch at Cafe",
            "category_id": food_cat.id,
            "transaction_date": "2026-10-18",
            "payment_method": "UPI",
            "notes": "With team",
        }
        response = client.post("/transactions/new", data=data, follow_redirects=True)
        assert response.status_code == 200

        txn = Transaction.query.filter_by(description="Lunch at Cafe").first()
        assert txn is not None
        assert txn.type == "expense"
        assert txn.amount_paise == 45075
        assert txn.amount_rupees == 450.75


def test_invalid_transaction_inputs(client, app, sample_categories):
    """Test that negative, zero, and malformed amounts are cleanly rejected with validation errors."""
    with app.app_context():
        food_cat = Category.query.filter_by(name="Food & Dining").first()

        # 1. Negative amount
        data_neg = {
            "type": "expense",
            "amount": "-500.00",
            "description": "Invalid Negative",
            "category_id": food_cat.id,
            "transaction_date": "2026-10-18",
            "payment_method": "Cash",
        }
        res_neg = client.post("/transactions/new", data=data_neg)
        assert res_neg.status_code == 200
        assert "Invalid amount format" in res_neg.get_data(as_text=True) or "must be greater than zero" in res_neg.get_data(as_text=True)

        # 2. Zero amount
        data_zero = {
            "type": "expense",
            "amount": "0",
            "description": "Invalid Zero",
            "category_id": food_cat.id,
            "transaction_date": "2026-10-18",
            "payment_method": "Cash",
        }
        res_zero = client.post("/transactions/new", data=data_zero)
        assert res_zero.status_code == 200
        assert "greater than zero" in res_zero.get_data(as_text=True)

        # 3. Non-numeric amount
        data_abc = {
            "type": "expense",
            "amount": "invalid_abc",
            "description": "Invalid Non-numeric",
            "category_id": food_cat.id,
            "transaction_date": "2026-10-18",
            "payment_method": "Cash",
        }
        res_abc = client.post("/transactions/new", data=data_abc)
        assert res_abc.status_code == 200
        assert "Invalid amount format" in res_abc.get_data(as_text=True)


def test_edit_transaction(client, app, sample_transactions):
    """Test modifying transaction amount, date, and description."""
    txn_id = sample_transactions[1]  # Supermarket Grocery Run (3250.50)

    # View edit form
    res_get = client.get(f"/transactions/{txn_id}/edit")
    assert res_get.status_code == 200
    assert "Supermarket Grocery Run" in res_get.get_data(as_text=True)

    with app.app_context():
        txn = db.session.get(Transaction, txn_id)
        food_id = txn.category_id

    # Post update
    update_data = {
        "type": "expense",
        "amount": "3500.00",
        "description": "Supermarket Grocery Run (Updated)",
        "category_id": food_id,
        "transaction_date": "2026-10-20",
        "payment_method": "Credit Card",
        "notes": "Added home supplies",
    }
    res_post = client.post(f"/transactions/{txn_id}/edit", data=update_data, follow_redirects=True)
    assert res_post.status_code == 200
    assert "Transaction updated successfully" in res_post.get_data(as_text=True)

    with app.app_context():
        updated_txn = db.session.get(Transaction, txn_id)
        assert updated_txn.amount_paise == 350000
        assert updated_txn.description == "Supermarket Grocery Run (Updated)"
        assert updated_txn.payment_method == "Credit Card"


def test_view_transaction_details(client, sample_transactions):
    """Test viewing individual transaction details."""
    txn_id = sample_transactions[0]
    response = client.get(f"/transactions/{txn_id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Monthly Salary Credit" in html
    assert "75,000.00" in html
    assert "Net Banking" in html


def test_delete_transaction(client, app, sample_transactions):
    """Test deleting a transaction."""
    txn_id = sample_transactions[2]  # Electricity Utility Bill

    res_del = client.post(f"/transactions/{txn_id}/delete", follow_redirects=True)
    assert res_del.status_code == 200
    assert "deleted successfully" in res_del.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(Transaction, txn_id) is None


def test_search_and_filter_transactions(client, sample_transactions):
    """Test searching transactions by keyword, filtering by type, and filtering by category."""
    # 1. Search by keyword
    res_search = client.get("/transactions/?q=Electricity")
    assert res_search.status_code == 200
    html_search = res_search.get_data(as_text=True)
    assert "Electricity Utility Bill" in html_search
    assert "Monthly Salary Credit" not in html_search

    # 2. Filter by type = income
    res_income = client.get("/transactions/?type=income")
    assert res_income.status_code == 200
    html_income = res_income.get_data(as_text=True)
    assert "Monthly Salary Credit" in html_income
    assert "Supermarket Grocery Run" not in html_income

    # 3. Filter by type = expense
    res_expense = client.get("/transactions/?type=expense")
    assert res_expense.status_code == 200
    html_expense = res_expense.get_data(as_text=True)
    assert "Supermarket Grocery Run" in html_expense
    assert "Electricity Utility Bill" in html_expense
    assert "Monthly Salary Credit" not in html_expense


def test_transaction_sorting(client, sample_transactions):
    """Test sorting transactions by amount ascending and descending."""
    res_asc = client.get("/transactions/?sort_by=amount&order=asc")
    assert res_asc.status_code == 200
    html_asc = res_asc.get_data(as_text=True)
    tbody_asc = html_asc[html_asc.find("<tbody>"):html_asc.find("</tbody>")]
    pos_low = tbody_asc.find("1,450.00")
    pos_high = tbody_asc.find("75,000.00")
    assert pos_low != -1 and pos_high != -1
    assert pos_low < pos_high

    res_desc = client.get("/transactions/?sort_by=amount&order=desc")
    assert res_desc.status_code == 200
    html_desc = res_desc.get_data(as_text=True)
    tbody_desc = html_desc[html_desc.find("<tbody>"):html_desc.find("</tbody>")]
    pos_desc_high = tbody_desc.find("75,000.00")
    pos_desc_low = tbody_desc.find("1,450.00")
    assert pos_desc_high != -1 and pos_desc_low != -1
    assert pos_desc_high < pos_desc_low
