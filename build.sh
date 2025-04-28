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

# Remove existing migrations if any
rm -rf migrations/*

# Initialize the database
python -m flask db init
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade

# Start the application
gunicorn --bind 0.0.0.0:$PORT wsgi:application 