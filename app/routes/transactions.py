from datetime import datetime, date
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from sqlalchemy import desc, asc, func
from app.models import db, Transaction, Category, rupees_to_paise, paise_to_rupees
from app.forms import TransactionForm

transactions_bp = Blueprint("transactions", __name__)


def populate_category_choices(form, transaction_type=None):
    """Populate category dropdown options dynamically."""
    query = Category.query
    if transaction_type in ["income", "expense"]:
        query = query.filter(
            Category.type.in_([transaction_type, "both"])
        )
    categories = query.order_by(Category.name.asc()).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]


@transactions_bp.route("/")
def index():
    """List transactions with search, filtering, sorting, and pagination."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "").strip()
    txn_type = request.args.get("type", "").strip()
    category_id = request.args.get("category_id", type=int)
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    sort_by = request.args.get("sort_by", "date").strip()
    order = request.args.get("order", "desc").strip()

    per_page = current_app.config.get("ITEMS_PER_PAGE", 15)

    # Base query
    query = Transaction.query

    # Search filter
    if search_query:
        query = query.filter(
            (Transaction.description.ilike(f"%{search_query}%"))
            | (Transaction.notes.ilike(f"%{search_query}%"))
        )

    # Type filter
    if txn_type in ["income", "expense"]:
        query = query.filter(Transaction.type == txn_type)

    # Category filter
    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    # Date range filters
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Transaction.transaction_date <= end_date)
        except ValueError:
            pass

    # Calculate filtered summary metrics (before pagination)
    total_income_paise = (
        query.filter(Transaction.type == "income")
        .with_entities(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .scalar()
        or 0
    )
    total_expense_paise = (
        query.filter(Transaction.type == "expense")
        .with_entities(func.coalesce(func.sum(Transaction.amount_paise), 0))
        .scalar()
        or 0
    )
    net_paise = total_income_paise - total_expense_paise
    total_count = query.count()

    # Sorting
    sort_col = Transaction.transaction_date
    if sort_by == "amount":
        sort_col = Transaction.amount_paise
    elif sort_by == "created_at":
        sort_col = Transaction.created_at
    elif sort_by == "description":
        sort_col = Transaction.description

    if order == "asc":
        query = query.order_by(asc(sort_col), asc(Transaction.id))
    else:
        query = query.order_by(desc(sort_col), desc(Transaction.id))

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    transactions = pagination.items

    all_categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        "transactions/index.html",
        transactions=transactions,
        pagination=pagination,
        categories=all_categories,
        search_query=search_query,
        txn_type=txn_type,
        category_id=category_id,
        start_date=start_date_str,
        end_date=end_date_str,
        sort_by=sort_by,
        order=order,
        total_income_paise=total_income_paise,
        total_expense_paise=total_expense_paise,
        net_paise=net_paise,
        total_count=total_count,
    )


@transactions_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new income or expense transaction."""
    form = TransactionForm()
    
    # Pre-select type from query parameter if provided (e.g. ?type=expense)
    req_type = request.args.get("type", "expense").lower()
    if req_type not in ["income", "expense"]:
        req_type = "expense"

    if request.method == "GET":
        form.type.data = req_type
        form.transaction_date.data = date.today()

    # Populate categories
    selected_type = form.type.data if request.method == "POST" else req_type
    populate_category_choices(form, selected_type)

    if form.validate_on_submit():
        try:
            amount_paise = rupees_to_paise(form.amount.data)
            category = db.session.get(Category, form.category_id.data)

            if not category:
                flash("Selected category does not exist.", "danger")
                return render_template("transactions/create.html", form=form)

            txn = Transaction(
                type=form.type.data,
                description=form.description.data.strip(),
                amount_paise=amount_paise,
                category_id=category.id,
                transaction_date=form.transaction_date.data,
                payment_method=form.payment_method.data,
                notes=form.notes.data.strip() if form.notes.data else None,
            )
            db.session.add(txn)
            db.session.commit()
            flash(
                f"Successfully recorded {txn.type} of {txn.formatted_amount}.",
                "success",
            )
            return redirect(url_for("transactions.index"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating transaction: {str(e)}", "danger")

    return render_template("transactions/create.html", form=form)


@transactions_bp.route("/<int:id>")
def view(id):
    """View transaction details."""
    transaction = db.session.get(Transaction, id)
    if not transaction:
        flash("Transaction not found.", "warning")
        return redirect(url_for("transactions.index"))
    return render_template("transactions/view.html", transaction=transaction)


@transactions_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    """Edit an existing transaction."""
    transaction = db.session.get(Transaction, id)
    if not transaction:
        flash("Transaction not found.", "warning")
        return redirect(url_for("transactions.index"))

    form = TransactionForm()
    selected_type = form.type.data if request.method == "POST" else transaction.type
    populate_category_choices(form, selected_type)

    if request.method == "GET":
        form.type.data = transaction.type
        form.amount.data = f"{transaction.amount_rupees:.2f}"
        form.description.data = transaction.description
        form.category_id.data = transaction.category_id
        form.transaction_date.data = transaction.transaction_date
        form.payment_method.data = transaction.payment_method
        form.notes.data = transaction.notes

    if form.validate_on_submit():
        try:
            transaction.type = form.type.data
            transaction.amount_paise = rupees_to_paise(form.amount.data)
            transaction.description = form.description.data.strip()
            transaction.category_id = form.category_id.data
            transaction.transaction_date = form.transaction_date.data
            transaction.payment_method = form.payment_method.data
            transaction.notes = form.notes.data.strip() if form.notes.data else None

            db.session.commit()
            flash("Transaction updated successfully.", "success")
            return redirect(url_for("transactions.view", id=transaction.id))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating transaction: {str(e)}", "danger")

    return render_template("transactions/edit.html", form=form, transaction=transaction)


@transactions_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    """Delete a transaction with confirmation."""
    transaction = db.session.get(Transaction, id)
    if not transaction:
        flash("Transaction not found.", "warning")
        return redirect(url_for("transactions.index"))

    desc = transaction.description
    amt = transaction.formatted_amount
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash(f"Transaction '{desc}' ({amt}) deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete transaction: {str(e)}", "danger")

    return redirect(url_for("transactions.index"))
