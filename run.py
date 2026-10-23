#!/usr/bin/env python3
"""Expense Tracker ET - Local Development Entry Point."""
import os
from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")

    print(f" * Starting Expense Tracker ET at http://{host}:{port}/")
    print(f" * Health endpoint at http://{host}:{port}/health")
    app.run(host=host, port=port, debug=debug)
