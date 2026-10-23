import logging
import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template
from flask_wtf.csrf import CSRFProtect, CSRFError

from config import config_by_name
from app.models import db, Category, AppSetting, format_currency_amount, paise_to_rupees

csrf = CSRFProtect()

DEFAULT_CATEGORIES = [
    {"name": "Food & Dining", "type": "expense", "icon": "bi-cup-hot", "color": "#f97316"},
    {"name": "Transportation", "type": "expense", "icon": "bi-bus-front", "color": "#0284c7"},
    {"name": "Shopping", "type": "expense", "icon": "bi-bag", "color": "#ec4899"},
    {"name": "Bills & Utilities", "type": "expense", "icon": "bi-receipt", "color": "#eab308"},
    {"name": "Education", "type": "expense", "icon": "bi-book", "color": "#8b5cf6"},
    {"name": "Health", "type": "expense", "icon": "bi-heart-pulse", "color": "#ef4444"},
    {"name": "Entertainment", "type": "expense", "icon": "bi-film", "color": "#a855f7"},
    {"name": "Travel", "type": "expense", "icon": "bi-airplane", "color": "#06b6d4"},
    {"name": "Salary", "type": "income", "icon": "bi-cash-stack", "color": "#10b981"},
    {"name": "Freelance", "type": "income", "icon": "bi-laptop", "color": "#14b8a6"},
    {"name": "Other", "type": "both", "icon": "bi-three-dots", "color": "#64748b"},
]


def seed_database():
    """Seed initial categories and default settings if table is empty."""
    # Seed default categories
    if Category.query.count() == 0:
        for cat_data in DEFAULT_CATEGORIES:
            cat = Category(
                name=cat_data["name"],
                type=cat_data["type"],
                icon=cat_data["icon"],
                color=cat_data["color"],
                is_default=True,
            )
            db.session.add(cat)
        db.session.commit()

    # Seed default settings
    default_settings = [
        ("currency_symbol", "₹", "Display symbol for currency"),
        ("currency_code", "INR", "Three-letter ISO currency code"),
        ("date_format", "%Y-%m-%d", "Default date display format"),
        ("monthly_budget_paise", "5000000", "Monthly expense budget in paise (₹50,000.00)"),
        ("app_title", "Expense Tracker ET", "Application display title"),
    ]
    for key, val, desc in default_settings:
        if not db.session.get(AppSetting, key):
            db.session.add(AppSetting(key=key, value=val, description=desc))
    db.session.commit()


def create_app(config_name=None):
    """Application factory for Expense Tracker ET."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    if isinstance(config_name, str):
        config_class = config_by_name.get(config_name, config_by_name["default"])
        app.config.from_object(config_class)
    else:
        app.config.from_object(config_name)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Configure logging
    if not app.testing:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        )
        app.logger.setLevel(logging.INFO)

    # Custom Jinja template filters
    @app.template_filter("currency")
    def currency_filter(paise):
        symbol = app.config.get("CURRENCY_SYMBOL", "₹")
        return format_currency_amount(paise, symbol=symbol)

    @app.template_filter("format_date")
    def date_filter(date_val, fmt=None):
        if not date_val:
            return ""
        if fmt is None:
            fmt = app.config.get("DATE_FORMAT", "%Y-%m-%d")
        if isinstance(date_val, str):
            try:
                date_val = datetime.fromisoformat(date_val)
            except ValueError:
                return date_val
        return date_val.strftime(fmt)

    @app.template_filter("rupees")
    def rupees_filter(paise):
        return f"{paise_to_rupees(paise):.2f}"

    # Global template context processor
    @app.context_processor
    def inject_global_vars():
        try:
            curr_symbol = AppSetting.get("currency_symbol", "₹")
            curr_code = AppSetting.get("currency_code", "INR")
            date_fmt = AppSetting.get("date_format", "%Y-%m-%d")
            budget_paise = AppSetting.get_int("monthly_budget_paise", 5000000)
        except Exception:
            curr_symbol = "₹"
            curr_code = "INR"
            date_fmt = "%Y-%m-%d"
            budget_paise = 5000000

        return {
            "app_name": "Expense Tracker ET",
            "currency_symbol": curr_symbol,
            "currency_code": curr_code,
            "date_format": date_fmt,
            "monthly_budget_paise": budget_paise,
            "monthly_budget_rupees": paise_to_rupees(budget_paise),
            "current_year": datetime.now(timezone.utc).year,
        }

    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.transactions import transactions_bp
    from app.routes.categories import categories_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp, url_prefix="/transactions")
    app.register_blueprint(categories_bp, url_prefix="/categories")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint to verify app running and DB connectivity."""
        try:
            # Simple query to verify DB connection
            db.session.execute(db.text("SELECT 1")).scalar()
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "app": "Expense Tracker ET",
                "version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }), 500

    # Error Handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template("400.html", error=error), 400

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template(
            "400.html",
            error="Your session or form security token has expired. Please refresh the page and try again.",
        ), 400

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    # Initialize tables and seeds automatically
    with app.app_context():
        db.create_all()
        try:
            seed_database()
        except Exception as e:
            app.logger.warning(f"Database seeding notice: {e}")

    return app
