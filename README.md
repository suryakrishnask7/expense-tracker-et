# Expense Tracker ET

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Woodpecker%20CI-blue.svg)](https://woodpecker-ci.org/)
[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-teal.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20(100%25%20Passing)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)]()

**Expense Tracker ET** is a complete, modern personal expense management web application built with Python (Flask), SQLAlchemy, SQLite, Bootstrap 5, and Chart.js.

This project serves as the primary artifact for the academic project:
> **“Design and Implementation of a CI/CD Pipeline Using Woodpecker CI”**

---

## Table of Contents

1. [Overview & Core Features](#1-overview--core-features)
2. [Technology Stack](#2-technology-stack)
3. [Project Directory Structure](#3-project-directory-structure)
4. [Prerequisites](#4-prerequisites)
5. [Local Installation and Setup](#5-local-installation-and-setup)
6. [Environment Configuration](#6-environment-configuration)
7. [Running the Application](#7-running-the-application)
8. [Automated Testing](#8-automated-testing)
9. [Woodpecker CI/CD Integration](#9-woodpecker-cicd-integration)
   - [Git and GitHub Setup](#git-and-github-setup)
   - [Connecting GitHub to Woodpecker CI](#connecting-github-to-woodpecker-ci)
   - [Configuring the Pipeline](#configuring-the-pipeline)
   - [Configuring Deployment Secrets](#configuring-deployment-secrets)
10. [Production Deployment to Linux](#10-production-deployment-to-linux)
11. [Verification & Health Checks](#11-verification--health-checks)
12. [Troubleshooting & Common Errors](#12-troubleshooting--common-errors)
13. [Security Limitations & Scope](#13-security-limitations--scope)

---

## 1. Overview & Core Features

Expense Tracker ET provides a polished, intuitive financial operating dashboard with zero external paid API dependencies:

- **Financial Dashboard:**
  - Current month total expenses, income, net balance, and transaction count.
  - Interactive 6-month historical Income vs. Expense comparison chart.
  - Expense breakdown donut chart by category (with offline fallback).
  - Monthly spending budget utilization tracking with real-time warning indicators (at 80% and 100%).
  - Recent transactions activity table.
- **Transaction Management (CRUD):**
  - Add, view, edit, and delete transactions.
  - Store monetary figures precisely as integer paise (1 Rupee = 100 paise) to eliminate floating-point rounding errors.
  - Display all currencies formatted in Indian Rupees (`₹`).
  - Search transactions by description or notes.
  - Filter transactions by Type (Income/Expense), Category, and Date Range.
  - Sort transactions by date and amount (Ascending / Descending).
  - Clean pagination for transaction logs.
- **Category Management:**
  - Pre-seeded with 11 default categories (Food & Dining, Transportation, Shopping, Bills & Utilities, Education, Health, Entertainment, Travel, Salary, Freelance, Other).
  - Add, edit, and safely delete categories.
  - In-use protection: Categories with existing transactions cannot be accidentally deleted.
- **Reports & Analytics:**
  - Spending breakdowns grouped by category with percentages and visual progress bars.
  - Payment method distribution analysis (UPI, Net Banking, Credit/Debit cards, Cash).
  - Daily average spending calculation.
  - Safe CSV export with **Formula Injection Sanitization** (automatically protects against spreadsheet formula exploits by neutralising `=`, `+`, `-`, `@`, `\t`, `\r` prefixes).
- **Settings & Preferences:**
  - Configurable currency symbol (`₹`), ISO currency code (`INR`), and date format.
  - Configurable monthly spending budget.
  - One-click factory reset option with user confirmation.
- **System Monitoring & Security:**
  - Automated `/health` endpoint returning JSON HTTP 200 verifying database connectivity.
  - Server-side form validation with CSRF protection enabled via Flask-WTF.
  - Parameterized database operations through SQLAlchemy preventing SQL injection.

---

## 2. Technology Stack

- **Backend:** Python 3.12+ / Flask 3.1
- **Database & ORM:** SQLite with Flask-SQLAlchemy 3.1 (persisted outside release directories)
- **Forms & Security:** Flask-WTF / WTForms (CSRF token verification)
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons 1.11, Chart.js 4.4, Vanilla JS
- **Testing:** pytest 8.0, pytest-cov
- **Production Server:** Gunicorn, systemd, Nginx / reverse proxy
- **CI/CD:** Woodpecker CI (Pipelines, Docker agent backend)
- **Deployment:** Bash, SSH, and rsync

---

## 3. Project Directory Structure

```text
d:\ET/
├── app/
│   ├── __init__.py          # App factory, blueprints, filters & health check
│   ├── models.py            # SQLAlchemy models (Transaction, Category, AppSetting)
│   ├── forms.py             # WTForms classes with CSRF and input validation
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── dashboard.py     # Dashboard metrics and chart calculations
│   │   ├── transactions.py  # Transaction CRUD, search, filtering, and sorting
│   │   ├── categories.py    # Category CRUD and safe deletion guards
│   │   ├── reports.py       # Analytics, grouping, and formula-safe CSV export
│   │   └── settings.py      # App preferences, monthly budget, and reset logic
│   ├── templates/
│   │   ├── base.html        # Modern sidebar layout and top navigation
│   │   ├── dashboard.html   # KPI cards, charts, and recent activity
│   │   ├── transactions/
│   │   │   ├── index.html   # Paginated transaction list with filters
│   │   │   ├── create.html  # Transaction creation form
│   │   │   ├── edit.html    # Transaction editing form
│   │   │   └── view.html    # Transaction details view
│   │   ├── categories/
│   │   │   ├── index.html   # Category cards and usage counts
│   │   │   └── form.html    # Category create & edit form with color picker
│   │   ├── reports.html     # Analytics and reporting dashboard
│   │   ├── settings.html    # Currency, date format, and budget preferences
│   │   ├── 400.html         # Bad request / CSRF token expiration page
│   │   ├── 404.html         # Not found error page
│   │   └── 500.html         # Internal server error page
│   └── static/
│       ├── css/
│       │   └── style.css    # Custom dark navy & teal design system
│       └── js/
│           └── main.js      # Sidebar toggling, confirmation alerts, and chart loader
├── tests/
│   ├── conftest.py          # Isolated in-memory SQLite fixtures
│   ├── test_dashboard.py    # Dashboard stats, health endpoint, budget tests
│   ├── test_transactions.py # Transaction CRUD, validation, search, filter, sort
│   ├── test_categories.py   # Category CRUD and safe deletion checks
│   ├── test_reports.py      # Period analytics, CSV export, formula sanitization
│   └── test_settings.py     # Settings updates and factory reset
├── instance/
│   └── .gitkeep             # Local SQLite database storage directory
├── deploy/
│   ├── expense-tracker-et.service # systemd unit configuration for Gunicorn
│   └── deploy.sh            # Zero-downtime Linux deployment script
├── config.py                # Environment configuration classes
├── run.py                   # Local development server runner
├── wsgi.py                  # Production WSGI entry point
├── requirements.txt         # Production runtime dependencies
├── requirements-dev.txt     # Test and linting dependencies
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── .woodpecker.yml          # Woodpecker CI pipeline definition
└── README.md                # Comprehensive documentation
```

---

## 4. Prerequisites

- **Python:** Version 3.12 or higher.
- **Git:** Version 2.25 or higher.
- **Operating System:** Windows, macOS, or Linux.
- **Web Browser:** Modern browser (Chrome, Firefox, Safari, Edge).

---

## 5. Local Installation and Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/expense-tracker-et.git
cd expense-tracker-et
```

### Step 2: Create and Activate Virtual Environment

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 6. Environment Configuration

Copy `.env.example` to `.env`:

**On Linux / macOS:**
```bash
cp .env.example .env
```

**On Windows:**
```powershell
Copy-Item .env.example .env
```

Review and adjust variables in `.env`:
```ini
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=replace-with-a-random-32-byte-hex-string
HOST=127.0.0.1
PORT=5000
DATABASE_PATH=instance/expense_tracker.db
DEFAULT_CURRENCY_SYMBOL=₹
DEFAULT_CURRENCY_CODE=INR
DEFAULT_DATE_FORMAT=%Y-%m-%d
DEFAULT_MONTHLY_BUDGET=50000.00
```

---

## 7. Running the Application

Start the local development server:
```bash
python run.py
```

The application will start at:
- **Web Dashboard:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Health Check Endpoint:** [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

*(The SQLite database is initialized automatically with default categories and settings upon startup.)*

---

## 8. Automated Testing

All tests use an isolated in-memory SQLite database (`sqlite:///:memory:`) that will not modify or interfere with your development or production database.

Run the test suite with pytest:
```bash
pytest -q
```

Run tests with verbose output and coverage report:
```bash
pytest -v --cov=app
```

### Test Suite Summary
- **Total Tests:** 24
- **Passing:** 24 (100%)
- **Code Coverage:** > 80%
- **Tested Modules:** Startup, `/health` endpoint, income & expense creation, input validations, decimal-to-paise conversion, transaction edit & delete, search and multi-column sorting, pagination, category uniqueness, safe category deletion, budget threshold warnings, reports analytics, and CSV formula injection protection.

---

## 9. Woodpecker CI/CD Integration

### Git and GitHub Setup
Initialize Git and push code to your GitHub repository:
```bash
git init
git add .
git commit -m "feat: complete Expense Tracker ET application with CI/CD"
git branch -M main
git remote add origin https://github.com/<your-username>/expense-tracker-et.git
git push -u origin main
```

### Connecting GitHub to Woodpecker CI
1. Open your Woodpecker CI web interface (e.g., `https://ci.your-domain.com`).
2. Log in using your GitHub account via OAuth.
3. In the Woodpecker dashboard, click **Add Repository**.
4. Select `expense-tracker-et` and click **Enable Repository**.

### Configuring the Pipeline
The project includes `.woodpecker.yml` configured for Docker-based execution:
- **Test Stage (`test`):** Uses official `python:3.12-slim`, installs dependencies, and runs `pytest -v --cov=app`.
- **Deploy Stage (`deploy`):** Runs only when tests pass and code is pushed to `main`. Uses `alpine:3.19` with SSH & rsync to trigger the remote deployment script.

### Configuring Deployment Secrets
In Woodpecker CI, navigate to **Repository Settings > Secrets** and add:

| Secret Name | Value Description | Example |
|---|---|---|
| `deploy_ssh_key` | Private SSH key authorized on your Linux server (`id_rsa`) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `deploy_host` | Public IP or hostname of target Linux server | `192.168.1.100` or `vm.domain.com` |
| `deploy_user` | Linux user with deployment privileges | `ubuntu` or `deploy` |
| `deploy_path` | Target directory on Linux server | `/opt/expense-tracker-et` |

---

## 9.1 Docker Container Deployment (Fast Local & VM Option)

You can also run Expense Tracker ET as a containerized service with Docker and Docker Compose:

### Run with Docker Compose
```bash
docker compose up -d --build
```

### Check Status & Logs
```bash
docker ps
docker logs -f expense-tracker-et
```

- **Application URL:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Health Check:** [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)
- **Data Persistence:** Financial data is preserved in the Docker volume `expense_tracker_data`.

### Stop the Container
```bash
docker compose down
```

---

### Server Prerequisites
On the target Linux virtual machine (Ubuntu 22.04 / 24.04 LTS recommended):
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip rsync curl openssh-server
```

Create application directories:
```bash
sudo mkdir -p /opt/expense-tracker-et/shared
sudo mkdir -p /opt/expense-tracker-et/releases
sudo mkdir -p /var/log/expense-tracker-et
sudo chown -R $USER:$USER /opt/expense-tracker-et /var/log/expense-tracker-et
```

### Automated Deployment Flow (`deploy/deploy.sh`)
The automated script in `deploy/deploy.sh` performs zero-downtime deployment:
1. **Preserves Data:** The SQLite database is maintained at `/opt/expense-tracker-et/shared/expense_tracker.db`, safely external to replaceable release code.
2. **Versioned Release:** Code is synced to `/opt/expense-tracker-et/releases/<TIMESTAMP>`.
3. **Virtualenv:** Sets up or updates `/opt/expense-tracker-et/venv` and installs `requirements.txt`.
4. **Symlink Switch:** Atomically repoints `/opt/expense-tracker-et/current` to the new release.
5. **Systemd Service:** Updates and restarts `expense-tracker-et.service`.
6. **Health Verification:** Probes `http://127.0.0.1:5000/health`. If healthy (HTTP 200), deployment succeeds and cleans up old releases (keeps latest 5). If health check fails, it automatically rolls back to the previous release symlink.

---

## 11. Verification & Health Checks

### Check Systemd Service Status
```bash
sudo systemctl status expense-tracker-et
```

### Test `/health` Endpoint
```bash
curl -i http://127.0.0.1:5000/health
```

**Expected Response (HTTP 200 OK):**
```json
{
  "app": "Expense Tracker ET",
  "database": "connected",
  "status": "healthy",
  "timestamp": "2026-10-23T04:00:00.000000Z",
  "version": "1.0.0"
}
```

---

## 12. Troubleshooting & Common Errors

| Issue | Cause | Resolution |
|---|---|---|
| **Port 5000 already in use** | Another service or Flask instance running | Run `set PORT=5001` (Windows) or `export PORT=5001` (Linux) and restart. |
| **CSRF Error / 400 Bad Request** | Form token expired or session cookie cleared | Refresh the page and re-submit the form. |
| **Health Check Timeout during deployment** | Gunicorn failed to bind or database permissions issue | Check logs: `sudo journalctl -u expense-tracker-et -n 50 --no-pager` |
| **Cannot delete category** | Category has existing transactions | Expected safety guard: Reassign or delete associated transactions first. |

---

## 13. Security Limitations & Scope

For this academic demonstration:
- **Single-User Architecture:** Intended for local evaluation or controlled demonstration virtual machines. Public registration is omitted intentionally.
- **Monetary Precision:** Stored in integer paise to eliminate binary floating-point representation anomalies.
- **CSV Formula Injection:** Neutralized by prepending formula control characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with single quotes.
- **No Hardcoded Secrets:** All credentials, keys, and database paths are loaded strictly via environment variables.
