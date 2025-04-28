#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

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

# Start the application
gunicorn --bind 0.0.0.0:$PORT wsgi:application 