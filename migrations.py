from app import create_app
from app.models.database import db
from flask_migrate import Migrate

app = create_app()

# Ensure migrate is registered in this context as well
migrate = Migrate(app, db) 