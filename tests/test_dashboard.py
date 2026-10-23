from datetime import date
from app.models import db, Transaction, Category, AppSetting, rupees_to_paise


def test_app_startup_and_health(client):
    """Test application startup and the /health monitoring endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["app"] == "Expense Tracker ET"


def test_dashboard_empty_rendering(client):
    """Test dashboard loads cleanly when no transactions have been added."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Expense Tracker ET" in html
    assert "Month Expenses" in html
    assert "Month Income" in html
    assert "Net Balance" in html
    assert "No transactions recorded yet" in html


def test_dashboard_calculations_with_data(client, sample_transactions):
    """Test that dashboard statistics reflect actual database sums."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Expected: Income = 75,000.00; Expense = 3,250.50 + 1,450.00 = 4,700.50
    # Net Balance = 75,000.00 - 4,700.50 = 70,299.50
    assert "75,000.00" in html
    assert "4,700.50" in html
    assert "70,299.50" in html
    assert "Monthly Salary Credit" in html
    assert "Supermarket Grocery Run" in html


def test_dashboard_budget_utilization_warning(client, app, sample_transactions):
    """Test budget alert displays when monthly expenses approach or exceed budget."""
    with app.app_context():
        # Set low monthly budget of ₹5,000.00 (spent is 4,700.50 -> 94% -> warning)
        AppSetting.set("monthly_budget_paise", str(rupees_to_paise(5000.00)))

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "94.0% Used" in html
    assert "Approaching budget limit" in html

    # Exceed budget: set budget to ₹4,000.00 (spent is 4,700.50 -> 117.5% -> exceeded)
    with app.app_context():
        AppSetting.set("monthly_budget_paise", str(rupees_to_paise(4000.00)))

    response2 = client.get("/")
    html2 = response2.get_data(as_text=True)
    assert "Budget exceeded by" in html2
