from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FGasRecord(db.Model):
    __tablename__ = 'fgas_records'
    
    id = db.Column(db.String(20), primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    comments = db.Column(db.Text)
    filled_kg = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    location = db.Column(db.String(100))
    
    def __init__(self, id, date, comments, filled_kg, status='active', location=None):
        self.id = id
        self.date = date
        self.comments = comments
        self.filled_kg = filled_kg
        self.status = status
        self.location = location
    
    def __repr__(self):
        return f'<FGasRecord {self.id} on {self.date}>'
    
    @classmethod
    def get_all_records(cls):
        return cls.query.order_by(cls.date.desc()).all()
    
    @classmethod
    def get_record_by_id(cls, id):
        return cls.query.filter_by(id=id).order_by(cls.date.desc()).all()
    
    @classmethod
    def get_record_by_id_and_date(cls, id, date):
        return cls.query.filter_by(id=id, date=date).first() 