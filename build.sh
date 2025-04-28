#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python -m flask db init
python -m flask db migrate -m "Initial migration"
python -m flask db upgrade

# Start the application
gunicorn --bind 0.0.0.0:$PORT wsgi:application 