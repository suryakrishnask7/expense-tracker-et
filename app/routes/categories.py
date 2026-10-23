from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models import db, Category, Transaction
from app.forms import CategoryForm

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/")
def index():
    """List all categories with usage counts."""
    categories = Category.query.order_by(Category.type.asc(), Category.name.asc()).all()
    return render_template("categories/index.html", categories=categories)


@categories_bp.route("/new", methods=["GET", "POST"])
def create():
    """Create a new custom category."""
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data.strip()

        # Check case-insensitive uniqueness
        existing = Category.query.filter(
            db.func.lower(Category.name) == db.func.lower(name)
        ).first()
        if existing:
            flash(f"A category named '{name}' already exists.", "danger")
            return render_template("categories/form.html", form=form, title="New Category")

        cat = Category(
            name=name,
            type=form.type.data,
            icon=form.icon.data,
            color=form.color.data,
            is_default=False,
        )
        db.session.add(cat)
        db.session.commit()
        flash(f"Category '{cat.name}' created successfully.", "success")
        return redirect(url_for("categories.index"))

    return render_template("categories/form.html", form=form, title="New Category")


@categories_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    """Edit an existing category."""
    cat = db.session.get(Category, id)
    if not cat:
        flash("Category not found.", "warning")
        return redirect(url_for("categories.index"))

    form = CategoryForm()

    if request.method == "GET":
        form.name.data = cat.name
        form.type.data = cat.type
        form.icon.data = cat.icon
        form.color.data = cat.color

    if form.validate_on_submit():
        name = form.name.data.strip()

        # Check uniqueness against other records
        existing = Category.query.filter(
            db.func.lower(Category.name) == db.func.lower(name),
            Category.id != cat.id,
        ).first()
        if existing:
            flash(f"Another category named '{name}' already exists.", "danger")
            return render_template(
                "categories/form.html", form=form, title="Edit Category", category=cat
            )

        cat.name = name
        cat.type = form.type.data
        cat.icon = form.icon.data
        cat.color = form.color.data
        db.session.commit()
        flash(f"Category '{cat.name}' updated successfully.", "success")
        return redirect(url_for("categories.index"))

    return render_template(
        "categories/form.html", form=form, title="Edit Category", category=cat
    )


@categories_bp.route("/<int:id>/delete", methods=["POST"])
def delete(id):
    """Delete a category if it is not in use by any transaction."""
    cat = db.session.get(Category, id)
    if not cat:
        flash("Category not found.", "warning")
        return redirect(url_for("categories.index"))

    count = cat.transaction_count
    if count > 0:
        flash(
            f"Cannot delete category '{cat.name}' because it is associated with {count} "
            f"transaction{'s' if count > 1 else ''}. Please reassign or delete these "
            f"transactions before removing this category.",
            "danger",
        )
        return redirect(url_for("categories.index"))

    try:
        db.session.delete(cat)
        db.session.commit()
        flash(f"Category '{cat.name}' deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete category: {str(e)}", "danger")

    return redirect(url_for("categories.index"))
