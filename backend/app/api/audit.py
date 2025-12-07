from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from backend.app import db
from backend.app.models.audit_log import AuditLog
from backend.app.models.user import User
from backend.app.models.file import File
from datetime import datetime
import csv
import io

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('', methods=['GET'])
@login_required
def get_audit_logs():
    """Get audit logs with optional filters"""
    if not current_user.can_approve():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user_id = request.args.get('user_id', type=int)
    file_id = request.args.get('file_id', type=int)
    project_id = request.args.get('project_id', type=int)
    action = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 100, type=int)
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if file_id:
        query = query.filter_by(file_id=file_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if action:
        query = query.filter_by(action=action)
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(AuditLog.timestamp >= start)
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(AuditLog.timestamp <= end)
    
    query = query.order_by(AuditLog.timestamp.desc())
    logs = query.limit(limit).all()
    
    enriched_logs = []
    for log in logs:
        log_dict = log.to_dict()
        
        if log.user:
            log_dict['username'] = log.user.username
        
        if log.file_id:
            file_obj = File.query.get(log.file_id)
            if file_obj:
                log_dict['filename'] = file_obj.filename
        
        enriched_logs.append(log_dict)
    
    return jsonify({
        'logs': enriched_logs,
        'count': len(enriched_logs)
    }), 200


@audit_bp.route('/export', methods=['GET'])
@login_required
def export_audit_logs():
    """Export audit logs as CSV"""
    if not current_user.can_approve():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    user_id = request.args.get('user_id', type=int)
    file_id = request.args.get('file_id', type=int)
    project_id = request.args.get('project_id', type=int)
    action = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if file_id:
        query = query.filter_by(file_id=file_id)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if action:
        query = query.filter_by(action=action)
    if start_date:
        start = datetime.fromisoformat(start_date)
        query = query.filter(AuditLog.timestamp >= start)
    if end_date:
        end = datetime.fromisoformat(end_date)
        query = query.filter(AuditLog.timestamp <= end)
    
    logs = query.order_by(AuditLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Timestamp', 'User', 'Action', 'File', 'Project', 'Details', 'IP Address'])
    
    for log in logs:
        user = User.query.get(log.user_id)
        username = user.username if user else 'Unknown'
        
        filename = ''
        if log.file_id:
            file_obj = File.query.get(log.file_id)
            filename = file_obj.filename if file_obj else ''
        
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else '',
            username,
            log.action,
            filename,
            log.project_id or '',
            str(log.details),
            log.ip_address or ''
        ])
    
    output.seek(0)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=audit_log_{timestamp}.csv'}
    )