from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    DateField,
    TextAreaField,
    SubmitField,
    HiddenField,
)
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from datetime import date
from app.models import rupees_to_paise


PAYMENT_METHODS = [
    ("Cash", "Cash"),
    ("UPI", "UPI (Google Pay, PhonePe, Paytm)"),
    ("Credit Card", "Credit Card"),
    ("Debit Card", "Debit Card"),
    ("Net Banking", "Net Banking"),
    ("Cheque", "Cheque"),
    ("Other", "Other"),
]


class TransactionForm(FlaskForm):
    """Form for adding and editing transactions."""

    type = SelectField(
        "Transaction Type",
        choices=[("expense", "Expense"), ("income", "Income")],
        validators=[DataRequired(message="Please select transaction type.")],
        default="expense",
    )

    amount = StringField(
        "Amount (₹)",
        validators=[DataRequired(message="Please enter transaction amount.")],
        render_kw={"placeholder": "e.g. 1250.00", "step": "0.01"},
    )

    description = StringField(
        "Description",
        validators=[
            DataRequired(message="Please provide a brief description."),
            Length(max=255, message="Description cannot exceed 255 characters."),
        ],
        render_kw={"placeholder": "e.g. Grocery shopping, Client payment"},
    )

    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Please select a category.")],
    )

    transaction_date = DateField(
        "Date",
        validators=[DataRequired(message="Please choose a valid date.")],
        default=date.today,
        format="%Y-%m-%d",
    )

    payment_method = SelectField(
        "Payment Method",
        choices=PAYMENT_METHODS,
        validators=[DataRequired(message="Please select payment method.")],
        default="UPI",
    )

    notes = TextAreaField(
        "Notes (Optional)",
        validators=[
            Optional(),
            Length(max=1000, message="Notes cannot exceed 1000 characters."),
        ],
        render_kw={"rows": 3, "placeholder": "Additional context or receipt notes..."},
    )

    submit = SubmitField("Save Transaction")

    def validate_amount(self, field):
        """Ensure amount is a valid positive number convertible to paise."""
        try:
            paise = rupees_to_paise(field.data)
            if paise <= 0:
                raise ValidationError("Amount must be greater than zero.")
        except ValueError as e:
            raise ValidationError(str(e))


class CategoryForm(FlaskForm):
    """Form for creating and editing categories."""

    name = StringField(
        "Category Name",
        validators=[
            DataRequired(message="Category name is required."),
            Length(min=2, max=64, message="Name must be between 2 and 64 characters."),
        ],
        render_kw={"placeholder": "e.g. Groceries, Gym, Investments"},
    )

    type = SelectField(
        "Category Type",
        choices=[
            ("expense", "Expense Only"),
            ("income", "Income Only"),
            ("both", "Both Income and Expense"),
        ],
        validators=[DataRequired(message="Please select category type.")],
        default="expense",
    )

    icon = SelectField(
        "Icon",
        choices=[
            ("bi-tag", "🏷️ Tag"),
            ("bi-cup-hot", "☕ Food & Dining"),
            ("bi-bus-front", "🚌 Transportation"),
            ("bi-bag", "🛍️ Shopping"),
            ("bi-receipt", "🧾 Bills & Utilities"),
            ("bi-book", "📚 Education"),
            ("bi-heart-pulse", "❤️ Health"),
            ("bi-film", "🎬 Entertainment"),
            ("bi-airplane", "✈️ Travel"),
            ("bi-cash-stack", "💵 Salary"),
            ("bi-laptop", "💻 Freelance / Tech"),
            ("bi-house", "🏠 Housing / Rent"),
            ("bi-car-front", "🚗 Automobile"),
            ("bi-gift", "🎁 Gifts / Donations"),
            ("bi-graph-up-arrow", "📈 Investment"),
            ("bi-shield-check", "🛡️ Insurance"),
            ("bi-three-dots", "⚙️ Other / Miscellaneous"),
        ],
        default="bi-tag",
    )

    color = StringField(
        "Color (Hex)",
        validators=[
            DataRequired(message="Color is required."),
            Length(min=4, max=20, message="Valid hex color code required."),
        ],
        default="#0d9488",
    )

    submit = SubmitField("Save Category")


class SettingsForm(FlaskForm):
    """Form for application settings and preferences."""

    currency_symbol = StringField(
        "Currency Symbol",
        validators=[
            DataRequired(message="Currency symbol is required."),
            Length(max=5, message="Max 5 characters."),
        ],
        default="₹",
    )

    currency_code = StringField(
        "Currency Code (ISO)",
        validators=[
            DataRequired(message="Currency code is required."),
            Length(min=3, max=5, message="3-character currency code required."),
        ],
        default="INR",
    )

    date_format = SelectField(
        "Preferred Date Format",
        choices=[
            ("%Y-%m-%d", "YYYY-MM-DD (e.g. 2026-10-23)"),
            ("%d/%m/%Y", "DD/MM/YYYY (e.g. 23/10/2026)"),
            ("%m/%d/%Y", "MM/DD/YYYY (e.g. 10/23/2026)"),
            ("%d %b %Y", "DD Mon YYYY (e.g. 23 Oct 2026)"),
        ],
        default="%Y-%m-%d",
    )

    monthly_budget = StringField(
        "Monthly Spending Budget (₹)",
        validators=[DataRequired(message="Monthly budget is required.")],
        render_kw={"placeholder": "e.g. 50000.00"},
    )

    submit = SubmitField("Save Preferences")

    def validate_monthly_budget(self, field):
        try:
            paise = rupees_to_paise(field.data)
            if paise < 0:
                raise ValidationError("Budget cannot be negative.")
        except ValueError as e:
            raise ValidationError(str(e))
