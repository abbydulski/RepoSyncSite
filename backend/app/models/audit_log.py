from backend.app import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, default={})
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_id': self.file_id,
            'project_id': self.project_id,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address
        }
    
    @staticmethod
    def log_action(user_id, action, file_id=None, project_id=None, details=None, ip_address=None):
        """Helper method to create audit log entry"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            file_id=file_id,
            project_id=project_id,
            details=details or {},
            ip_address=ip_address
        )
        db.session.add(log)
        return log
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'