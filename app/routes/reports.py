import csv
import io
from datetime import date, datetime, timedelta
import calendar
from flask import (
    Blueprint,
    render_template,
    request,
    Response,
    current_app,
)
from sqlalchemy import func
from app.models import db, Transaction, Category, paise_to_rupees, format_currency_amount

reports_bp = Blueprint("reports", __name__)


def sanitize_csv_cell(val) -> str:
    """Neutralize spreadsheet formula injection by prepending dangerous characters with a single quote."""
    if val is None:
        return ""
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


@reports_bp.route("/")
def index():
    """Analytics and reporting dashboard with date range filtering."""
    today = date.today()

    # Presets or custom range
    range_preset = request.args.get("range", "this_month")
    custom_start = request.args.get("start_date", "").strip()
    custom_end = request.args.get("end_date", "").strip()

    if custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, "%Y-%m-%d").date()
            end_date = datetime.strptime(custom_end, "%Y-%m-%d").date()
            range_preset = "custom"
        except ValueError:
            start_date = date(today.year, today.month, 1)
            end_date = today
    elif range_preset == "today":
        start_date = today
        end_date = today
    elif range_preset == "this_week":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif range_preset == "last_month":
        first_this_month = date(today.year, today.month, 1)
        last_prev_month = first_this_month - timedelta(days=1)
        start_date = date(last_prev_month.year, last_prev_month.month, 1)
        end_date = last_prev_month
    elif range_preset == "this_year":
        start_date = date(today.year, 1, 1)
        end_date = today
    elif range_preset == "all_time":
        earliest_txn = (
            Transaction.query.order_by(Transaction.transaction_date.asc()).first()
        )
        start_date = earliest_txn.transaction_date if earliest_txn else date(today.year, 1, 1)
        end_date = today
    else:  # default 'this_month'
        start_date = date(today.year, today.month, 1)
        end_date = today
        range_preset = "this_month"

    # Base query for period
    period_query = Transaction.query.filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
    )

    # Total income and expense in period
    total_income_paise = (
        period_query.filter(Transaction.type == "income")
        .with_entities(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .scalar()
        or 0
    )
    total_expense_paise = (
        period_query.filter(Transaction.type == "expense")
        .with_entities(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .scalar()
        or 0
    )
    net_balance_paise = total_income_paise - total_expense_paise
    transaction_count = period_query.count()

    # Savings rate
    savings_rate = 0.0
    if total_income_paise > 0:
        savings_rate = round((net_balance_paise / total_income_paise) * 100, 1)

    # Days in period and daily average
    num_days = max(1, (end_date - start_date).days + 1)
    avg_daily_expense_paise = int(round(total_expense_paise / num_days))

    # Category breakdown (expenses)
    category_stats = (
        db.session.query(
            Category.name,
            Category.icon,
            Category.color,
            func.coalesce(func.sum(Transaction.amount_paise), 0).label("total_paise"),
            func.count(Transaction.id).label("txn_count"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Category.id, Category.name, Category.icon, Category.color)
        .order_by(func.sum(Transaction.amount_paise).desc())
        .all()
    )

    # Format category rows with percentages
    category_report = []
    top_category = None
    if category_stats:
        top_category = {
            "name": category_stats[0][0],
            "amount_rupees": paise_to_rupees(category_stats[0][3]),
            "formatted": format_currency_amount(category_stats[0][3]),
        }

    for row in category_stats:
        cat_paise = row[3]
        pct = round((cat_paise / total_expense_paise * 100), 1) if total_expense_paise > 0 else 0.0
        category_report.append({
            "name": row[0],
            "icon": row[1],
            "color": row[2],
            "total_paise": cat_paise,
            "total_rupees": paise_to_rupees(cat_paise),
            "formatted_amount": format_currency_amount(cat_paise),
            "txn_count": row[4],
            "percentage": pct,
        })

    # Category chart data
    chart_cat_labels = [c["name"] for c in category_report]
    chart_cat_values = [c["total_rupees"] for c in category_report]
    chart_cat_colors = [c["color"] for c in category_report]

    # Payment method breakdown
    payment_stats = (
        db.session.query(
            Transaction.payment_method,
            func.coalesce(func.sum(Transaction.amount_paise), 0),
            func.count(Transaction.id),
        )
        .filter(
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .group_by(Transaction.payment_method)
        .order_by(func.sum(Transaction.amount_paise).desc())
        .all()
    )

    payment_report = []
    for row in payment_stats:
        p_paise = row[1]
        pct = round((p_paise / total_expense_paise * 100), 1) if total_expense_paise > 0 else 0.0
        payment_report.append({
            "method": row[0],
            "total_paise": p_paise,
            "formatted_amount": format_currency_amount(p_paise),
            "txn_count": row[2],
            "percentage": pct,
        })

    # Recent history report in period (up to 50 items)
    history_transactions = (
        period_query.order_by(
            Transaction.transaction_date.desc(), Transaction.id.desc()
        )
        .limit(50)
        .all()
    )

    return render_template(
        "reports.html",
        range_preset=range_preset,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        total_income_paise=total_income_paise,
        total_expense_paise=total_expense_paise,
        net_balance_paise=net_balance_paise,
        transaction_count=transaction_count,
        savings_rate=savings_rate,
        avg_daily_expense_paise=avg_daily_expense_paise,
        num_days=num_days,
        category_report=category_report,
        top_category=top_category,
        payment_report=payment_report,
        history_transactions=history_transactions,
        chart_cat_labels=chart_cat_labels,
        chart_cat_values=chart_cat_values,
        chart_cat_colors=chart_cat_colors,
    )


@reports_bp.route("/export-csv")
def export_csv():
    """Export filtered transactions to a safe CSV file preventing formula injection."""
    search_query = request.args.get("q", "").strip()
    txn_type = request.args.get("type", "").strip()
    category_id = request.args.get("category_id", type=int)
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    query = Transaction.query

    if search_query:
        query = query.filter(
            (Transaction.description.ilike(f"%{search_query}%"))
            | (Transaction.notes.ilike(f"%{search_query}%"))
        )
    if txn_type in ["income", "expense"]:
        query = query.filter(Transaction.type == txn_type)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date_str:
        try:
            s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date >= s_date)
        except ValueError:
            pass
    if end_date_str:
        try:
            e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date <= e_date)
        except ValueError:
            pass

    transactions = query.order_by(
        Transaction.transaction_date.desc(), Transaction.id.desc()
    ).all()

    # Build CSV output in memory
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Headers
    writer.writerow([
        "Transaction ID",
        "Date",
        "Type",
        "Category",
        "Description",
        "Amount (INR)",
        "Payment Method",
        "Notes",
        "Created At",
    ])

    for txn in transactions:
        writer.writerow([
            sanitize_csv_cell(txn.id),
            sanitize_csv_cell(txn.transaction_date.isoformat() if txn.transaction_date else ""),
            sanitize_csv_cell(txn.type.capitalize()),
            sanitize_csv_cell(txn.category.name if txn.category else "Uncategorized"),
            sanitize_csv_cell(txn.description),
            f"{txn.amount_rupees:.2f}",
            sanitize_csv_cell(txn.payment_method),
            sanitize_csv_cell(txn.notes or ""),
            sanitize_csv_cell(txn.created_at.strftime("%Y-%m-%d %H:%M:%S") if txn.created_at else ""),
        ])

    csv_data = output.getvalue()
    filename = f"expense_tracker_export_{date.today().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
