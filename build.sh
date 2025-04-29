#!/usr/bin/env bash
# exit on error
set -o errexit

# Print Python version and pip version
python --version
pip --version

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies with verbose output
pip install -v -r requirements.txt

# Install reportlab explicitly with verbose output
pip install -v reportlab==4.1.0

# Verify reportlab installation
python -c "import reportlab; print(f'ReportLab version: {reportlab.__version__}')"

# Run any other build steps if needed
python -m flask db upgrade

# Create necessary directories
mkdir -p instance
mkdir -p migrations

# Initialize the database
export FLASK_APP=wsgi.py
export FLASK_ENV=production

# Create database tables directly
python -c "
from app import create_app
from app.models.database import db
app = create_app()
with app.app_context():
    db.create_all()
" 