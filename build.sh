#!/usr/bin/env bash
# exit on error
set -o errexit

# Print Python version and pip version
python --version
pip --version

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt

# Install reportlab explicitly
python -m pip install --no-cache-dir reportlab==4.1.0

# Print Python path and verify reportlab installation
python -c "import sys; print(f'Python path: {sys.path}')"
python -c "import reportlab; print(f'ReportLab version: {reportlab.__version__}')"

# Run database migrations
python -m flask db upgrade

# Create necessary directories
mkdir -p instance
mkdir -p migrations

# Initialize the database
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Create database tables
python -c "
from app import create_app
from app.models.database import db
app = create_app()
with app.app_context():
    db.create_all()
" 