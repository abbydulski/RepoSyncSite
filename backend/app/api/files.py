from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from backend.app import db
from backend.app.models.file import File
from backend.app.models.version import Version
from backend.app.models.project import Project
from backend.app.models.audit_log import AuditLog
from backend.app.services.excel_validator import ExcelValidator
import os
from datetime import datetime

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a new file or new version"""
    if not current_user.can_edit():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    project_id = request.form.get('project_id')
    commit_message = request.form.get('commit_message')
    file_id = request.form.get('file_id')
    
    if not project_id or not commit_message:
        return jsonify({'error': 'Missing required fields'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(uploaded_file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    project = Project.query.get_or_404(project_id)
    filename = secure_filename(uploaded_file.filename)
    
    if file_id:
        file_obj = File.query.get_or_404(file_id)
        if file_obj.checked_out_by != current_user.id:
            return jsonify({'error': 'File must be checked out by you'}), 403
    else:
        file_obj = File(project_id=project_id, filename=filename)
        db.session.add(file_obj)
        db.session.flush()
    
    next_version = len(file_obj.versions) + 1
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    stored_filename = f"{file_obj.id}_v{next_version}_{timestamp}_{filename}"
    file_path = os.path.join(current_app.config['STORAGE_PATH'], stored_filename)
    
    uploaded_file.save(file_path)
    file_size = os.path.getsize(file_path)
    
    version = Version(
        file_id=file_obj.id,
        version_number=next_version,
        file_path=file_path,
        file_size=file_size,
        commit_message=commit_message,
        uploaded_by=current_user.id
    )
    
    db.session.add(version)
    db.session.flush()
    
    validator = ExcelValidator()
    validation_result = validator.validate(file_path, project.validation_rules)
    
    version.validation_status = 'passed' if validation_result['passed'] else 'failed'
    version.validation_errors = validation_result['errors']
    version.validated_at = datetime.utcnow()
    
    if validation_result['passed']:
        file_obj.current_version_id = version.id
        if file_obj.is_checked_out:
            file_obj.checkin()
    
    db.session.commit()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='file_uploaded',
        file_id=file_obj.id,
        project_id=project_id,
        details={'filename': filename, 'version': next_version},
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'File uploaded successfully',
        'file': file_obj.to_dict(include_versions=True),
        'validation': validation_result
    }), 201


@files_bp.route('/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """Download current version of a file"""
    file_obj = File.query.get_or_404(file_id)
    
    if not file_obj.current_version:
        return jsonify({'error': 'No version available'}), 404
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='file_downloaded',
        file_id=file_id,
        details={'version': file_obj.current_version.version_number},
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return send_file(
        file_obj.current_version.file_path,
        as_attachment=True,
        download_name=file_obj.filename
    )


@files_bp.route('/<int:file_id>/checkout', methods=['POST'])
@login_required
def checkout_file(file_id):
    """Check out a file for editing"""
    if not current_user.can_edit():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    file_obj = File.query.get_or_404(file_id)
    
    success, message = file_obj.checkout(current_user.id)
    
    if not success:
        return jsonify({'error': message}), 400
    
    db.session.commit()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='file_checked_out',
        file_id=file_id,
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': message,
        'file': file_obj.to_dict()
    }), 200


@files_bp.route('/<int:file_id>/checkin', methods=['POST'])
@login_required
def checkin_file(file_id):
    """Check in a file"""
    file_obj = File.query.get_or_404(file_id)
    
    if file_obj.checked_out_by != current_user.id:
        return jsonify({'error': 'File is not checked out by you'}), 403
    
    file_obj.checkin()
    db.session.commit()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='file_checked_in',
        file_id=file_id,
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'File checked in successfully',
        'file': file_obj.to_dict()
    }), 200


@files_bp.route('/<int:file_id>', methods=['GET'])
@login_required
def get_file(file_id):
    """Get file details with versions"""
    file_obj = File.query.get_or_404(file_id)
    file_dict = file_obj.to_dict(include_versions=True)
    file_dict['is_checked_out_by_me'] = file_obj.checked_out_by == current_user.id
    return jsonify({'file': file_dict}), 200


@files_bp.route('/<int:file_id>/status', methods=['GET'])
@login_required
def get_file_status(file_id):
    """Get file status"""
    file_obj = File.query.get_or_404(file_id)
    return jsonify({'file': file_obj.to_dict()}), 200


@files_bp.route('/<int:file_id>/versions', methods=['GET'])
@login_required
def get_file_versions(file_id):
    """Get all versions of a file"""
    file_obj = File.query.get_or_404(file_id)
    
    return jsonify({
        'versions': [v.to_dict() for v in sorted(file_obj.versions, key=lambda x: x.version_number, reverse=True)]
    }), 200