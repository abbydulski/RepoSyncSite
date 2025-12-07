from backend.app import db
from datetime import datetime


class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Validation rules stored as JSON
    validation_rules = db.Column(db.JSON, default={})
    
    # Relationships
    files = db.relationship('File', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_files=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'file_count': len(self.files)
        }
        
        if include_files:
            data['files'] = [f.to_dict() for f in self.files]
        
        return data
    
    def __repr__(self):
        return f'<Project {self.name}>'