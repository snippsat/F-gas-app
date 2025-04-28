from app import create_app

"""
F-Gas Record Management Application

This application tracks F-Gas records with SQLAlchemy and Flask.

Database Migrations:
- Use Flask-Migrate for managing database schema changes
- Run migrations with the following commands:
  - flask db migrate -m "Description of change"  # Create migration
  - flask db upgrade                             # Apply migration
  - flask db downgrade                           # Revert migration
- See migrations/README.md for more details
"""

app = create_app()

if __name__ == '__main__':
    app.run(debug=False) 