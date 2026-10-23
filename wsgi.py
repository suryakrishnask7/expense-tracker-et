"""Expense Tracker ET - Production WSGI Entry Point for Gunicorn."""
import os
from app import create_app

# Default to production environment when executed via WSGI runner
env = os.environ.get("FLASK_ENV", "production")
app = create_app(env)
application = app

if __name__ == "__main__":
    app.run()
