from app import create_app
from app.models.database import db
from flask_migrate import Migrate

# Create app instance
app = create_app()

# Ensure migrate is registered in this context as well
migrate = Migrate(app, db)

# This is the variable that Gunicorn will look for
application = app

if __name__ == '__main__':
    app.run() 