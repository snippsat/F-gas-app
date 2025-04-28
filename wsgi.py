from app import create_app
from app.models.database import db
from flask_migrate import Migrate
import os

# Create app instance
app = create_app()

# Ensure migrate is registered in this context as well
migrate = Migrate(app, db)

# This is the variable that Gunicorn will look for
application = app

# Create database tables if they don't exist
with app.app_context():
    # Create instance directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance'), exist_ok=True)
    # Create all tables
    db.create_all()

if __name__ == '__main__':
    app.run() 