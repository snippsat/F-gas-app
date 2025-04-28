import os
import sqlite3
from app import create_app
from app.models.database import db

# Create app context
app = create_app()

with app.app_context():
    # Get database path
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"Database URI: {db_uri}")
    
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        
        # Check if path is relative and convert to absolute
        if not os.path.isabs(db_path):
            base_dir = os.path.abspath(os.path.dirname(__file__))
            db_path = os.path.join(base_dir, db_path)
        
        # Normalize path (replace forward slashes with backslashes on Windows)
        db_path = os.path.normpath(db_path)
        
        print(f"Full database path: {db_path}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Force close any existing connections by creating a new one
        try:
            print(f"Connecting to database at: {db_path}")
            test_conn = sqlite3.connect(db_path)
            test_conn.close()
            print("Successfully connected to database")
        except Exception as e:
            print(f"Could not connect to database: {e}")
    
    try:
        # Drop all tables
        db.drop_all()
        print("Dropped all tables")
        
        # Create tables with updated schema
        db.create_all()
        print("Created all tables with current schema")
        
        print("Database rebuilt successfully")
    except Exception as e:
        print(f"Error rebuilding database: {e}") 