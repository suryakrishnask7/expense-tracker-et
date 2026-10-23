from app.models import db, AppSetting, paise_to_rupees, rupees_to_paise


def test_settings_page_render(client):
    """Test preferences page renders with current default configuration."""
    response = client.get("/settings/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Settings & Preferences" in html
    assert "Currency Symbol" in html
    assert "Preferred Date Format" in html
    assert "Monthly Spending Budget" in html


def test_update_settings(client, app):
    """Test modifying preferences updates the database values."""
    new_settings = {
        "currency_symbol": "₹",
        "currency_code": "INR",
        "date_format": "%d/%m/%Y",
        "monthly_budget": "65000.00",
    }
    response = client.post("/settings/", data=new_settings, follow_redirects=True)
    assert response.status_code == 200
    assert "Preferences updated successfully" in response.get_data(as_text=True)

    with app.app_context():
        assert AppSetting.get("currency_symbol") == "₹"
        assert AppSetting.get("date_format") == "%d/%m/%Y"
        budget_paise = AppSetting.get_int("monthly_budget_paise")
        assert budget_paise == 6500000


def test_reset_settings_to_defaults(client, app):
    """Test resetting preferences restores standard factory defaults."""
    with app.app_context():
        AppSetting.set("monthly_budget_paise", "10000000")  # Set to ₹1,00,000

    response = client.post("/settings/reset", follow_redirects=True)
    assert response.status_code == 200
    assert "reset to factory defaults" in response.get_data(as_text=True)

    with app.app_context():
        # Default budget is ₹50,000.00 (5000000 paise)
        assert AppSetting.get_int("monthly_budget_paise") == 5000000
        assert AppSetting.get("currency_symbol") == "₹"
