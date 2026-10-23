from datetime import datetime, timezone
import re
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def rupees_to_paise(rupees_val) -> int:
    """Safely convert rupees (string, int, or float) to integer paise.

    Avoids floating-point rounding errors and enforces reasonable limits.
    Raises ValueError on negative, zero, excessively large, or invalid input.
    """
    if rupees_val is None:
        raise ValueError("Amount is required.")

    # Convert to string and clean up
    s_val = str(rupees_val).strip()
    if not s_val:
        raise ValueError("Amount cannot be empty.")

    # Validate numeric format (allows optional decimal up to 2 places)
    if not re.match(r"^\d+(\.\d{1,2})?$", s_val):
        raise ValueError("Invalid amount format. Please enter a positive number with up to 2 decimal places.")

    try:
        f_val = float(s_val)
    except (ValueError, TypeError):
        raise ValueError("Invalid monetary amount.")

    if f_val <= 0:
        raise ValueError("Amount must be greater than zero.")

    # Guard against excessively large amount (limit: ₹1,000,000,000 = 100 Crore)
    if f_val > 1_000_000_000:
        raise ValueError("Amount exceeds maximum allowed limit (₹1,000,000,000).")

    # Round to nearest integer paise
    return int(round(f_val * 100))


def paise_to_rupees(paise_val: int) -> float:
    """Convert integer paise back to rupees as a float."""
    if paise_val is None:
        return 0.0
    return paise_val / 100.0


def format_currency_amount(paise_val: int, symbol: str = "₹") -> str:
    """Format integer paise into human-readable currency string: ₹1,234.56"""
    if paise_val is None:
        return f"{symbol}0.00"
    rupees = paise_val / 100.0
    # Standard 2 decimal places with comma separation
    return f"{symbol}{rupees:,.2f}"


class Category(db.Model):
    """Category model for transactions."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    # Type can be: 'expense', 'income', or 'both'
    type = db.Column(db.String(20), nullable=False, default="expense")
    icon = db.Column(db.String(40), nullable=False, default="bi-tag")
    color = db.Column(db.String(20), nullable=False, default="#0d9488")
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transactions = db.relationship(
        "Transaction",
        backref="category",
        lazy="dynamic",
        cascade="all",
        passive_deletes=False,
    )

    @property
    def transaction_count(self) -> int:
        return self.transactions.count()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "icon": self.icon,
            "color": self.color,
            "is_default": self.is_default,
            "transaction_count": self.transaction_count,
        }

    def __repr__(self):
        return f"<Category {self.name} ({self.type})>"


class Transaction(db.Model):
    """Transaction model representing an income or expense record."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    # 'expense' or 'income'
    type = db.Column(db.String(20), nullable=False, index=True)
    description = db.Column(db.String(255), nullable=False, index=True)
    amount_paise = db.Column(db.BigInteger, nullable=False)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    transaction_date = db.Column(db.Date, nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False, default="Cash")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    @property
    def amount_rupees(self) -> float:
        return paise_to_rupees(self.amount_paise)

    @property
    def formatted_amount(self) -> str:
        return format_currency_amount(self.amount_paise)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "amount_paise": self.amount_paise,
            "amount_rupees": self.amount_rupees,
            "formatted_amount": self.formatted_amount,
            "category": self.category.name if self.category else "Uncategorized",
            "category_id": self.category_id,
            "category_color": self.category.color if self.category else "#64748b",
            "category_icon": self.category.icon if self.category else "bi-tag",
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else "",
            "payment_method": self.payment_method,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self):
        return f"<Transaction {self.id}: {self.type} ₹{self.amount_rupees:.2f} - {self.description}>"


class AppSetting(db.Model):
    """Key-value application settings storage."""

    __tablename__ = "app_settings"

    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        record = db.session.get(cls, key)
        return record.value if record else default

    @classmethod
    def set(cls, key: str, value: str, description: str = None) -> None:
        record = db.session.get(cls, key)
        if record:
            record.value = str(value)
            if description:
                record.description = description
        else:
            record = cls(key=key, value=str(value), description=description)
            db.session.add(record)
        db.session.commit()

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        val = cls.get(key, str(default))
        try:
            return float(val)
        except ValueError:
            return default

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        val = cls.get(key, str(default))
        try:
            return int(val)
        except ValueError:
            return default
