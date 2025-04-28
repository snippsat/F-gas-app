from app import create_app
from app.models.database import db
from flask_migrate import Migrate

# Create app instance
application = create_app()

# Ensure migrate is registered in this context as well
migrate = Migrate(application, db)

if __name__ == '__main__':
    # Only used for development
    application.run() 