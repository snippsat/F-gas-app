import sys
import os
from flask import Flask
from app.models.database import db, User
from app import create_app

def create_regular_user(username, email, password):
    """Create a new regular (non-admin) user."""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Error: User with username '{username}' already exists.")
            return False
            
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            print(f"Error: User with email '{email}' already exists.")
            return False
        
        # Create new regular user
        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"Regular user '{username}' created successfully!")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_user.py <username> <email> <password>")
        sys.exit(1)
        
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    success = create_regular_user(username, email, password)
    sys.exit(0 if success else 1) 