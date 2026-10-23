from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import db, AppSetting, paise_to_rupees, rupees_to_paise
from app.forms import SettingsForm

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    """Manage application preferences and monthly spending budget."""
    form = SettingsForm()

    if request.method == "GET":
        form.currency_symbol.data = AppSetting.get("currency_symbol", "₹")
        form.currency_code.data = AppSetting.get("currency_code", "INR")
        form.date_format.data = AppSetting.get("date_format", "%Y-%m-%d")

        budget_paise = AppSetting.get_int("monthly_budget_paise", 5000000)
        form.monthly_budget.data = f"{paise_to_rupees(budget_paise):.2f}"

    if form.validate_on_submit():
        try:
            budget_paise = rupees_to_paise(form.monthly_budget.data)

            AppSetting.set(
                "currency_symbol",
                form.currency_symbol.data.strip(),
                "Display symbol for currency",
            )
            AppSetting.set(
                "currency_code",
                form.currency_code.data.strip().upper(),
                "Three-letter ISO currency code",
            )
            AppSetting.set(
                "date_format",
                form.date_format.data.strip(),
                "Default date display format",
            )
            AppSetting.set(
                "monthly_budget_paise",
                str(budget_paise),
                "Monthly expense budget in paise",
            )

            flash("Preferences updated successfully.", "success")
            return redirect(url_for("settings.index"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update preferences: {str(e)}", "danger")

    return render_template("settings.html", form=form)


@settings_bp.route("/reset", methods=["POST"])
def reset():
    """Reset all settings back to application defaults."""
    try:
        AppSetting.set("currency_symbol", "₹", "Display symbol for currency")
        AppSetting.set("currency_code", "INR", "Three-letter ISO currency code")
        AppSetting.set("date_format", "%Y-%m-%d", "Default date display format")
        AppSetting.set(
            "monthly_budget_paise", "5000000", "Monthly expense budget in paise (₹50,000.00)"
        )
        flash("All preferences have been reset to factory defaults.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting settings: {str(e)}", "danger")

    return redirect(url_for("settings.index"))
