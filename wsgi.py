from app import create_app

# For production WSGI servers
application = create_app()

if __name__ == '__main__':
    # Only used for development
    application.run() 