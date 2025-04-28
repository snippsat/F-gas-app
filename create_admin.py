from app import create_app
from app.models.database import db, User

def create_admin_user(username, email, password):
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username=username).first()
        if admin:
            print(f"Admin user '{username}' already exists.")
            return
        
        # Create new admin user
        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password) 