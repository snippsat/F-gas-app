from app import create_app
from app.models.database import db
from flask_migrate import Migrate, upgrade
import os

app = create_app()

# Print database location
with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Apply migrations manually
    base_dir = os.path.abspath(os.path.dirname(__file__))
    migrations_dir = os.path.join(base_dir, 'migrations')
    
    # Create database tables
    db.create_all()
    
    # Try to apply migrations
    migrate = Migrate(app, db, directory=migrations_dir)
    
    # Print success message
    print("Database setup complete. Tables created directly.") 