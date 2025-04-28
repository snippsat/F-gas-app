from flask import Flask
from app.models.database import db, FGasRecord, User
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Get absolute path to the database file
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(base_dir, 'instance', 'fgas.db')
    
    # Normalize path (use correct slashes for the OS)
    db_path = os.path.normpath(db_path)
    
    # Get database path from environment or use default
    database_url = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    
    # Print database path for debugging
    print(f"Database URL: {database_url}")
    print(f"Database path: {db_path}")
    print(f"Directory exists: {os.path.exists(os.path.dirname(db_path))}")
    
    # Use environment variables for sensitive settings
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 os.environ.get('UPLOAD_FOLDER', 'uploads'))
    )
    
    # Ensure instance directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main.bp)
    
    # Register auth blueprint
    from app.routes import auth
    app.register_blueprint(auth.bp)
    
    # Ensure the uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app 