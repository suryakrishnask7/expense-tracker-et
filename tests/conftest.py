import pytest
from datetime import date, timedelta
from app import create_app
from app.models import db, Category, Transaction, AppSetting, rupees_to_paise


@pytest.fixture
def app():
    """Create and configure a clean Flask application instance for each test."""
    app_instance = create_app("testing")

    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def sample_categories(app):
    """Ensure default categories are seeded and return reference dictionary."""
    with app.app_context():
        cats = {c.name: c for c in Category.query.all()}
        # If empty, add essential categories
        if not cats:
            food = Category(name="Food & Dining", type="expense", icon="bi-cup-hot", color="#f97316")
            salary = Category(name="Salary", type="income", icon="bi-cash-stack", color="#10b981")
            bills = Category(name="Bills & Utilities", type="expense", icon="bi-receipt", color="#eab308")
            db.session.add_all([food, salary, bills])
            db.session.commit()
            cats = {c.name: c for c in Category.query.all()}
        return cats


@pytest.fixture
def sample_transactions(app, sample_categories):
    """Seed sample income and expense transactions for testing calculations and filters."""
    with app.app_context():
        food = Category.query.filter_by(name="Food & Dining").first()
        salary = Category.query.filter_by(name="Salary").first()
        bills = Category.query.filter_by(name="Bills & Utilities").first()

        today = date.today()
        yesterday = today - timedelta(days=1)

        t1 = Transaction(
            type="income",
            description="Monthly Salary Credit",
            amount_paise=rupees_to_paise(75000.00),
            category_id=salary.id,
            transaction_date=today,
            payment_method="Net Banking",
            notes="Regular employment income",
        )
        t2 = Transaction(
            type="expense",
            description="Supermarket Grocery Run",
            amount_paise=rupees_to_paise(3250.50),
            category_id=food.id,
            transaction_date=today,
            payment_method="UPI",
            notes="Weekly vegetables and groceries",
        )
        t3 = Transaction(
            type="expense",
            description="Electricity Utility Bill",
            amount_paise=rupees_to_paise(1450.00),
            category_id=bills.id,
            transaction_date=yesterday,
            payment_method="Credit Card",
            notes="September bill",
        )

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        return [t1.id, t2.id, t3.id]
