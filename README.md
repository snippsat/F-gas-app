# F-Gas Registration System Type 72

A Flask-based web application for managing F-Gas records and documentation.

## Features

- F-Gas record registration and management
- Document management system
- Search functionality
- Gas usage tracking
- Database migrations with Flask-Migrate
- Modern UI with Tailwind CSS

## Installation

1. Clone the repository:

```bash
git clone git@github.com:snippsat/F-gas-app.git
cd F-gas-app
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp env.example .env
# Edit .env with your configuration
```

5. Initialize the database:

```bash
flask db upgrade
```

## Development

Run the development server:

```bash
flask run
```

## Production Deployment

For production deployment, use Gunicorn:

```bash
gunicorn wsgi:application
```

## Project Structure

```
F-gas-app/
├── app/                    # Application package
│   ├── models/            # Database models
│   ├── routes/            # Route handlers
│   ├── templates/         # HTML templates
│   └── __init__.py        # Application factory
├── migrations/            # Database migrations
├── instance/             # Instance-specific files
├── doc/                  # Documentation files
├── requirements.txt      # Project dependencies
├── wsgi.py              # WSGI entry point
└── README.md            # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
