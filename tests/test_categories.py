from app.models import db, Category, Transaction


def test_default_categories_seeded(client, sample_categories):
    """Test that default categories exist and are accessible."""
    response = client.get("/categories/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Food &amp; Dining" in html or "Food & Dining" in html
    assert "Transportation" in html
    assert "Salary" in html


def test_create_category(client, app):
    """Test adding a custom category with valid parameters."""
    cat_data = {
        "name": "Cloud Subscriptions",
        "type": "expense",
        "icon": "bi-laptop",
        "color": "#6366f1",
    }
    response = client.post("/categories/new", data=cat_data, follow_redirects=True)
    assert response.status_code == 200
    assert "created successfully" in response.get_data(as_text=True)

    with app.app_context():
        cat = Category.query.filter_by(name="Cloud Subscriptions").first()
        assert cat is not None
        assert cat.type == "expense"
        assert cat.color == "#6366f1"


def test_duplicate_category_name_rejected(client, app, sample_categories):
    """Test that creating a category with duplicate name is prevented."""
    dup_data = {
        "name": "Food & Dining",  # Already exists
        "type": "expense",
        "icon": "bi-cup-hot",
        "color": "#f97316",
    }
    response = client.post("/categories/new", data=dup_data)
    assert response.status_code == 200
    assert "already exists" in response.get_data(as_text=True)


def test_edit_category(client, app, sample_categories):
    """Test updating category details."""
    with app.app_context():
        cat = Category.query.filter_by(name="Transportation").first()
        cat_id = cat.id

    edit_data = {
        "name": "Transit & Cab",
        "type": "expense",
        "icon": "bi-car-front",
        "color": "#0ea5e9",
    }
    response = client.post(f"/categories/{cat_id}/edit", data=edit_data, follow_redirects=True)
    assert response.status_code == 200
    assert "updated successfully" in response.get_data(as_text=True)

    with app.app_context():
        updated = db.session.get(Category, cat_id)
        assert updated.name == "Transit & Cab"


def test_safe_category_deletion(client, app, sample_transactions):
    """Test that categories in use cannot be deleted, while unused categories can be safely removed."""
    with app.app_context():
        food = Category.query.filter_by(name="Food & Dining").first()
        assert food.transaction_count > 0
        food_id = food.id

    # Attempt to delete in-use category -> should be rejected with clear warning
    res_in_use = client.post(f"/categories/{food_id}/delete", follow_redirects=True)
    assert res_in_use.status_code == 200
    assert "Cannot delete category" in res_in_use.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(Category, food_id) is not None

    # Now create an unused category and delete it -> should succeed
    with app.app_context():
        unused = Category(name="Temporary Unused", type="expense", icon="bi-tag", color="#000000")
        db.session.add(unused)
        db.session.commit()
        unused_id = unused.id

    res_unused = client.post(f"/categories/{unused_id}/delete", follow_redirects=True)
    assert res_unused.status_code == 200
    assert "deleted successfully" in res_unused.get_data(as_text=True)

    with app.app_context():
        assert db.session.get(Category, unused_id) is None
