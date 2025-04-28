from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class FGasRecord(db.Model):
    __tablename__ = 'fgas_records'
    
    id = db.Column(db.String, primary_key=True)
    date = db.Column(db.Date, primary_key=True)
    comments = db.Column(db.Text, nullable=True)
    filled_kg = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active', nullable=False)
    location = db.Column(db.String(100), nullable=True)
    
    def __init__(self, id, date, comments, filled_kg, status='active', location=None):
        self.id = id
        self.date = date
        self.comments = comments
        self.filled_kg = filled_kg
        self.status = status
        self.location = location
    
    def __repr__(self):
        return f'<FGasRecord {self.id} on {self.date}>'
    
    @staticmethod
    def get_all_records():
        return FGasRecord.query.order_by(FGasRecord.date.desc()).all()
    
    @staticmethod
    def get_record_by_id(id):
        return FGasRecord.query.filter_by(id=id).order_by(FGasRecord.date.desc()).all()
    
    @staticmethod
    def get_record_by_id_and_date(id, date):
        return FGasRecord.query.filter_by(id=id, date=date).first() 