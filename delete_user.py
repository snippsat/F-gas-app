import sys
import os
from flask import Flask
from app.models.database import db, User
from app import create_app

def delete_user(username):
    """Delete a user by username."""
    app = create_app()
    
    with app.app_context():
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: User with username '{username}' does not exist.")
            return False
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        print(f"User '{username}' deleted successfully!")
        return True

def list_users():
    """List all users in the system."""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the system.")
            return
            
        print("\nUsers in the system:")
        print("-" * 60)
        print(f"{'Username':<20} {'Email':<30} {'Admin':<10}")
        print("-" * 60)
        
        for user in users:
            is_admin = "Yes" if user.is_admin else "No"
            print(f"{user.username:<20} {user.email:<30} {is_admin:<10}")
        
        print("-" * 60)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Available commands:")
        print("  python delete_user.py list                  - List all users")
        print("  python delete_user.py delete <username>     - Delete a user")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    elif command == "delete" and len(sys.argv) == 3:
        username = sys.argv[2]
        success = delete_user(username)
        sys.exit(0 if success else 1)
    else:
        print("Invalid command.")
        print("Available commands:")
        print("  python delete_user.py list                  - List all users")
        print("  python delete_user.py delete <username>     - Delete a user")
        sys.exit(1) 