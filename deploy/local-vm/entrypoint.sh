#!/bin/bash
set -e

# If application release exists, start Gunicorn background service on boot
if [ -d "/opt/expense-tracker-et/current" ] && [ -f "/opt/expense-tracker-et/venv/bin/gunicorn" ]; then
    echo "Starting Gunicorn server on port 5000..."
    cd /opt/expense-tracker-et/current
    nohup /opt/expense-tracker-et/venv/bin/gunicorn --workers 2 --bind 0.0.0.0:5000 wsgi:application > /var/log/expense-tracker-et/access.log 2> /var/log/expense-tracker-et/error.log &
fi

exec "$@"
