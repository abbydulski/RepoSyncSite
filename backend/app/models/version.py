from backend.app import db
from datetime import datetime


class Version(db.Model):
    __tablename__ = 'versions'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    
    # File storage
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    
    # Metadata
    commit_message = db.Column(db.Text, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Validation
    validation_status = db.Column(db.String(20), default='pending')
    validation_errors = db.Column(db.JSON, default=[])
    validated_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'version_number': self.version_number,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'commit_message': self.commit_message,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'validation_status': self.validation_status,
            'validation_errors': self.validation_errors,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None
        }
    
    def __repr__(self):
        return f'<Version {self.version_number} of File {self.file_id}>'