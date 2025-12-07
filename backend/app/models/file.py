from backend.app import db
from datetime import datetime


class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    
    # Check-out management
    checked_out_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    checked_out_at = db.Column(db.DateTime, nullable=True)
    
    # Current version tracking
    current_version_id = db.Column(db.Integer, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('Version', backref='file', lazy=True, cascade='all, delete-orphan')
    checked_out_user = db.relationship('User', foreign_keys=[checked_out_by])
    
    @property
    def is_checked_out(self):
        """Check if file is currently checked out"""
        return self.checked_out_by is not None
    
    @property
    def current_version(self):
        """Get the current version object"""
        if self.current_version_id:
            from backend.app.models.version import Version
            return Version.query.get(self.current_version_id)
        return None
    
    def checkout(self, user_id):
        """Check out the file to a user"""
        if self.is_checked_out:
            return False, "File is already checked out"
        
        self.checked_out_by = user_id
        self.checked_out_at = datetime.utcnow()
        return True, "File checked out successfully"
    
    def checkin(self):
        """Check in the file (release lock)"""
        self.checked_out_by = None
        self.checked_out_at = None
    
    def to_dict(self, include_versions=False):
        """Convert to dictionary"""
        # Determine status for UI display
        if self.is_checked_out:
            status = 'checked_out'
        elif self.current_version and self.current_version.validation_status == 'passed':
            status = 'available'
        elif self.current_version and self.current_version.validation_status == 'failed':
            status = 'validation_failed'
        else:
            status = 'pending'

        # Get username of who checked out
        checked_out_username = None
        if self.checked_out_user:
            checked_out_username = self.checked_out_user.username

        data = {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'status': status,
            'is_checked_out': self.is_checked_out,
            'checked_out_by': checked_out_username,
            'checked_out_at': self.checked_out_at.isoformat() if self.checked_out_at else None,
            'current_version_id': self.current_version_id,
            'current_version': len(self.versions),  # For display as "Version X"
            'version_count': len(self.versions),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_versions:
            data['versions'] = [v.to_dict() for v in sorted(self.versions, key=lambda x: x.version_number, reverse=True)]

        if self.current_version:
            data['current_version_data'] = self.current_version.to_dict()

        return data
    
    def __repr__(self):
        return f'<File {self.filename}>'