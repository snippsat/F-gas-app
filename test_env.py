import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print environment variables
print("Environment variables loaded from .env:")
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY', 'Not found')[:10]}...")
print(f"FLASK_APP: {os.environ.get('FLASK_APP', 'Not found')}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'Not found')}")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not found')}")
print(f"UPLOAD_FOLDER: {os.environ.get('UPLOAD_FOLDER', 'Not found')}") 