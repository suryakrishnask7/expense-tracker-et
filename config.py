import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    APP_NAME = "Expense Tracker ET"
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "expense-tracker-et-dev-insecure-secret-key-replace-in-prod"
    )

    # Database configuration
    DB_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "expense_tracker.db"))
    # Ensure directory exists if it's a file path
    db_dir = os.path.dirname(os.path.abspath(DB_PATH))
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError:
            pass

    # Normalize sqlite URI
    norm_db_path = os.path.abspath(DB_PATH).replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{norm_db_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours

    # Currency and Localization defaults
    CURRENCY_SYMBOL = os.environ.get("DEFAULT_CURRENCY_SYMBOL", "₹")
    CURRENCY_CODE = os.environ.get("DEFAULT_CURRENCY_CODE", "INR")
    DATE_FORMAT = os.environ.get("DEFAULT_DATE_FORMAT", "%Y-%m-%d")
    DEFAULT_MONTHLY_BUDGET = float(os.environ.get("DEFAULT_MONTHLY_BUDGET", "50000.00"))

    # Pagination
    ITEMS_PER_PAGE = 15


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests for straightforward client requests
    ITEMS_PER_PAGE = 10


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    def __init__(self):
        super().__init__()
        # Validate that secret key is set properly in production
        if self.SECRET_KEY.startswith("expense-tracker-et-dev"):
            import warnings
            warnings.warn(
                "CRITICAL SECURITY WARNING: SECRET_KEY is set to default insecure key. "
                "Set a secure SECRET_KEY in the environment before deploying to production!"
            )


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
