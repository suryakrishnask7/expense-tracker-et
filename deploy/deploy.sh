#!/usr/bin/env bash
# ==============================================================================
# Expense Tracker ET - Automated Zero-Downtime Linux Deployment Script
# CI/CD Pipeline Artifact for Woodpecker CI
# ==============================================================================
set -euo pipefail

# ------------------------------------------------------------------------------
# 1. Configuration & Path Setup
# ------------------------------------------------------------------------------
APP_NAME="expense-tracker-et"
BASE_DIR="${DEPLOY_PATH:-/opt/expense-tracker-et}"
RELEASES_DIR="${BASE_DIR}/releases"
SHARED_DIR="${BASE_DIR}/shared"
CURRENT_LINK="${BASE_DIR}/current"
VENV_DIR="${BASE_DIR}/venv"
LOG_DIR="/var/log/${APP_NAME}"
SERVICE_NAME="${APP_NAME}.service"
RELEASE_TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_RELEASE_DIR="${RELEASES_DIR}/${RELEASE_TIMESTAMP}"

HEALTH_URL="http://127.0.0.1:5000/health"
HEALTH_TIMEOUT_SECS=30

echo "=========================================================="
echo " Starting Deployment for ${APP_NAME}"
echo " Timestamp: ${RELEASE_TIMESTAMP}"
echo " Target Directory: ${BASE_DIR}"
echo "=========================================================="

# ------------------------------------------------------------------------------
# 2. Directory Structure & Permissions Setup
# ------------------------------------------------------------------------------
echo "--> Creating required directories..."
sudo mkdir -p "${BASE_DIR}" "${LOG_DIR}"
sudo chown -R "$(id -un):$(id -gn)" "${BASE_DIR}" "${LOG_DIR}"
mkdir -p "${RELEASES_DIR}"
mkdir -p "${SHARED_DIR}"

# ------------------------------------------------------------------------------
# 3. Persistent SQLite Database Preservation
# Database is stored strictly in the persistent shared/ directory, NOT inside
# the release folder, so code updates never overwrite existing financial data.
# ------------------------------------------------------------------------------
SHARED_ENV_FILE="${SHARED_DIR}/.env"
SHARED_DB_FILE="${SHARED_DIR}/expense_tracker.db"

if [ ! -f "${SHARED_ENV_FILE}" ]; then
    echo "--> Generating initial production .env in shared directory..."
    cat <<EOF > "${SHARED_ENV_FILE}"
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_PATH=${SHARED_DB_FILE}
DEFAULT_CURRENCY_SYMBOL=₹
DEFAULT_CURRENCY_CODE=INR
DEFAULT_DATE_FORMAT=%Y-%m-%d
DEFAULT_MONTHLY_BUDGET=50000.00
EOF
    chmod 600 "${SHARED_ENV_FILE}"
fi

# ------------------------------------------------------------------------------
# 4. Code Checkout / Copy to Release Directory
# ------------------------------------------------------------------------------
echo "--> Preparing release directory: ${NEW_RELEASE_DIR}"
mkdir -p "${NEW_RELEASE_DIR}"

# If deploying from local workspace or transferred source directory
SOURCE_DIR="${DEPLOY_SOURCE_DIR:-.}"
if [ -d "${SOURCE_DIR}/app" ] && [ -f "${SOURCE_DIR}/requirements.txt" ]; then
    rsync -av --exclude='.git' \
              --exclude='venv' \
              --exclude='instance/*.db' \
              --exclude='__pycache__' \
              --exclude='.pytest_cache' \
              --exclude='.coverage' \
              "${SOURCE_DIR}/" "${NEW_RELEASE_DIR}/"
else
    echo "ERROR: No source files found in ${SOURCE_DIR} to deploy!"
    exit 1
fi

# Symlink persistent .env into the new release
ln -sfn "${SHARED_ENV_FILE}" "${NEW_RELEASE_DIR}/.env"

# ------------------------------------------------------------------------------
# 5. Virtual Environment & Dependency Installation
# ------------------------------------------------------------------------------
echo "--> Setting up Python virtual environment..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

echo "--> Installing / upgrading dependencies..."
"${VENV_DIR}/bin/pip" install --no-cache-dir --upgrade pip
"${VENV_DIR}/bin/pip" install --no-cache-dir -r "${NEW_RELEASE_DIR}/requirements.txt"

# ------------------------------------------------------------------------------
# 6. Database Migrations / Schema Validation
# ------------------------------------------------------------------------------
echo "--> Initializing / validating database schema..."
PYTHONPATH="${NEW_RELEASE_DIR}" DATABASE_PATH="${SHARED_DB_FILE}" "${VENV_DIR}/bin/python" -c "from app import create_app, db; app = create_app('production');"


# ------------------------------------------------------------------------------
# 7. Atomic Release Switch via Symlink
# ------------------------------------------------------------------------------
PREVIOUS_RELEASE=""
if [ -L "${CURRENT_LINK}" ]; then
    PREVIOUS_RELEASE=$(readlink "${CURRENT_LINK}")
fi

echo "--> Switching active release symlink to ${NEW_RELEASE_DIR}..."
ln -sfn "${NEW_RELEASE_DIR}" "${CURRENT_LINK}"

# ------------------------------------------------------------------------------
# 8. Service Installation & Restart
# ------------------------------------------------------------------------------
echo "--> Updating and restarting service..."
if command -v systemctl >/dev/null 2>&1 && [ "$(systemctl is-system-running 2>/dev/null || true)" != "offline" ]; then
    sudo cp "${CURRENT_LINK}/deploy/${SERVICE_NAME}" "/etc/systemd/system/${SERVICE_NAME}"
    sudo systemctl daemon-reload
    sudo systemctl enable "${SERVICE_NAME}"
    sudo systemctl restart "${SERVICE_NAME}"
else
    # Container / non-systemd fallback: start Gunicorn background daemon
    pkill -f gunicorn 2>/dev/null || true
    sleep 1
    cd "${CURRENT_LINK}"
    nohup "${VENV_DIR}/bin/gunicorn" --workers 2 --bind 0.0.0.0:5000 wsgi:application > "${LOG_DIR}/access.log" 2> "${LOG_DIR}/error.log" &
fi

# ------------------------------------------------------------------------------
# 9. Automated Post-Deployment Health Check
# ------------------------------------------------------------------------------
echo "--> Verifying application health at ${HEALTH_URL}..."
START_TIME=$(date +%s)
HEALTHY=false

while [ $(($(date +%s) - START_TIME)) -lt "${HEALTH_TIMEOUT_SECS}" ]; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${HEALTH_URL}" || true)
    if [ "${HTTP_CODE}" = "200" ]; then
        HEALTHY=true
        break
    fi
    echo "    Waiting for service... (HTTP: ${HTTP_CODE})"
    sleep 2
done

if [ "${HEALTHY}" = true ]; then
    echo "=========================================================="
    echo " Deployment SUCCESSFUL! Service is healthy (HTTP 200)."
    echo " Active Release: ${NEW_RELEASE_DIR}"
    echo "=========================================================="

    # Cleanup old releases (keep latest 5)
    echo "--> Pruning old releases (retaining last 5)..."
    cd "${RELEASES_DIR}"
    ls -dt */ | tail -n +6 | xargs -I {} rm -rf "{}"
    exit 0
else
    echo "=========================================================="
    echo " ERROR: Health check failed! Rollback initiated..."
    echo "=========================================================="
    sudo journalctl -u "${SERVICE_NAME}" -n 25 --no-pager

    # Rollback symlink
    if [ -n "${PREVIOUS_RELEASE}" ] && [ -d "${PREVIOUS_RELEASE}" ]; then
        echo "--> Rolling back to previous release: ${PREVIOUS_RELEASE}"
        ln -sfn "${PREVIOUS_RELEASE}" "${CURRENT_LINK}"
        sudo systemctl restart "${SERVICE_NAME}"
    fi

    exit 1
fi
