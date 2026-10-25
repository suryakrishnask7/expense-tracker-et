from datetime import date, datetime, timedelta
import calendar
from flask import Blueprint, render_template, jsonify
from sqlalchemy import func, extract
from app.models import db, Transaction, Category, AppSetting, paise_to_rupees

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Main dashboard showing current month metrics, charts, and recent activity."""
    today = date.today()
    current_year = today.year
    current_month = today.month

    # First and last day of current month
    first_day = date(current_year, current_month, 1)
    last_day_num = calendar.monthrange(current_year, current_month)[1]
    last_day = date(current_year, current_month, last_day_num)

    # Current month statistics
    month_expense_paise = (
        db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .filter(
            Transaction.type == "expense",
            Transaction.transaction_date >= first_day,
            Transaction.transaction_date <= last_day,
        )
        .scalar()
    )

    month_income_paise = (
        db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .filter(
            Transaction.type == "income",
            Transaction.transaction_date >= first_day,
            Transaction.transaction_date <= last_day,
        )
        .scalar()
    )

    month_transaction_count = (
        Transaction.query.filter(
            Transaction.transaction_date >= first_day,
            Transaction.transaction_date <= last_day,
        ).count()
    )

    net_balance_paise = month_income_paise - month_expense_paise

    # Budget calculation
    budget_paise = AppSetting.get_int("monthly_budget_paise", 5000000)
    budget_rupees = paise_to_rupees(budget_paise)
    month_expense_rupees = paise_to_rupees(month_expense_paise)

    budget_utilization = 0.0
    budget_status = "safe"  # safe, warning, exceeded
    if budget_paise > 0:
        budget_utilization = round((month_expense_paise / budget_paise) * 100, 1)
        if budget_utilization >= 100:
            budget_status = "exceeded"
        elif budget_utilization >= 80:
            budget_status = "warning"

    # Recent transactions (latest 7)
    recent_transactions = (
        Transaction.query.order_by(
            Transaction.transaction_date.desc(), Transaction.id.desc()
        )
        .limit(7)
        .all()
    )

    # 6-Month Income vs Expense Trend
    # Build last 6 months list (chronological)
    trend_labels = []
    trend_income = []
    trend_expense = []

    # Calculate month offsets: 5 months ago to current month
    for offset in range(5, -1, -1):
        # Calculate target year and month
        y = current_year
        m = current_month - offset
        while m <= 0:
            m += 12
            y -= 1

        m_first = date(y, m, 1)
        m_last = date(y, m, calendar.monthrange(y, m)[1])
        label = m_first.strftime("%b %Y")
        trend_labels.append(label)

        inc_paise = (
            db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
            .filter(
                Transaction.type == "income",
                Transaction.transaction_date >= m_first,
                Transaction.transaction_date <= m_last,
            )
            .scalar()
        )
        exp_paise = (
            db.session.query(func.coalesce(func.sum(Transaction.amount_paise), 0))
            .filter(
                Transaction.type == "expense",
                Transaction.transaction_date >= m_first,
                Transaction.transaction_date <= m_last,
            )
            .scalar()
        )

        trend_income.append(paise_to_rupees(inc_paise))
        trend_expense.append(paise_to_rupees(exp_paise))

    # Category breakdown for current month (or all-time fallback if no current month expenses)
    cat_query = (
        db.session.query(
            Category.name,
            Category.color,
            func.coalesce(func.sum(Transaction.amount_paise), 0).label("total_paise"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.type == "expense",
            Transaction.transaction_date >= first_day,
            Transaction.transaction_date <= last_day,
        )
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount_paise).desc())
        .all()
    )

    # Fallback to recent 90 days if this month has no expenses yet
    if not cat_query:
        cat_query = (
            db.session.query(
                Category.name,
                Category.color,
                func.coalesce(func.sum(Transaction.amount_paise), 0).label("total_paise"),
            )
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(Transaction.type == "expense")
            .group_by(Category.id, Category.name, Category.color)
            .order_by(func.sum(Transaction.amount_paise).desc())
            .all()
        )

    cat_labels = [row[0] for row in cat_query]
    cat_colors = [row[1] for row in cat_query]
    cat_values = [paise_to_rupees(row[2]) for row in cat_query]

    # Daily spending trend for current month (up to today or month end)
    days_in_month = min(today.day, last_day_num)
    daily_labels = [f"Day {d}" for d in range(1, days_in_month + 1)]
    daily_spending = []

    # Get daily spending via group by
    daily_query = dict(
        db.session.query(
            extract("day", Transaction.transaction_date),
            func.sum(Transaction.amount_paise),
        )
        .filter(
            Transaction.type == "expense",
            Transaction.transaction_date >= first_day,
            Transaction.transaction_date <= today,
        )
        .group_by(extract("day", Transaction.transaction_date))
        .all()
    )

    running_total = 0.0
    daily_cumulative = []
    for d in range(1, days_in_month + 1):
        paise_on_d = daily_query.get(d, 0)
        rupees_on_d = paise_to_rupees(paise_on_d)
        daily_spending.append(rupees_on_d)
        running_total += rupees_on_d
        daily_cumulative.append(round(running_total, 2))

    return render_template(
        "dashboard.html",
        month_name=today.strftime("%B %Y"),
        month_expense_paise=month_expense_paise,
        month_income_paise=month_income_paise,
        net_balance_paise=net_balance_paise,
        month_transaction_count=month_transaction_count,
        budget_paise=budget_paise,
        budget_rupees=budget_rupees,
        budget_utilization=budget_utilization,
        budget_status=budget_status,
        recent_transactions=recent_transactions,
        # Chart JSON data
        chart_trend_labels=trend_labels,
        chart_trend_income=trend_income,
        chart_trend_expense=trend_expense,
        chart_cat_labels=cat_labels,
        chart_cat_colors=cat_colors,
        chart_cat_values=cat_values,
        chart_daily_labels=daily_labels,
        chart_daily_spending=daily_spending,
        chart_daily_cumulative=daily_cumulative,
    )
