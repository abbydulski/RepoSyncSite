from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.app import db
from backend.app.models.project import Project
from backend.app.models.audit_log import AuditLog

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET'])
@login_required
def list_projects():
    """List all projects"""
    projects = Project.query.order_by(Project.updated_at.desc()).all()
    
    return jsonify({
        'projects': [p.to_dict() for p in projects]
    }), 200


@projects_bp.route('', methods=['POST'])
@login_required
def create_project():
    """Create a new project"""
    if not current_user.can_edit():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    name = data.get('name')
    description = data.get('description', '')
    validation_rules = data.get('validation_rules', {})
    
    if not name:
        return jsonify({'error': 'Project name is required'}), 400
    
    project = Project(
        name=name,
        description=description,
        created_by=current_user.id,
        validation_rules=validation_rules
    )
    
    db.session.add(project)
    db.session.commit()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='project_created',
        project_id=project.id,
        details={'name': name},
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'Project created successfully',
        'project': project.to_dict()
    }), 201


@projects_bp.route('/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    """Get a specific project"""
    project = Project.query.get_or_404(project_id)
    
    return jsonify({
        'project': project.to_dict(include_files=True)
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    """Update a project"""
    if not current_user.can_edit():
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    if 'name' in data:
        project.name = data['name']
    if 'description' in data:
        project.description = data['description']
    if 'validation_rules' in data:
        project.validation_rules = data['validation_rules']
    
    db.session.commit()
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='project_updated',
        project_id=project.id,
        details={'updates': list(data.keys())},
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'Project updated successfully',
        'project': project.to_dict()
    }), 200


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin permissions required'}), 403
    
    project = Project.query.get_or_404(project_id)
    project_name = project.name
    
    AuditLog.log_action(
        user_id=current_user.id,
        action='project_deleted',
        project_id=project.id,
        details={'name': project_name},
        ip_address=request.remote_addr
    )
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({
        'message': 'Project deleted successfully'
    }), 200


@projects_bp.route('/<int:project_id>/files', methods=['GET'])
@login_required
def list_project_files(project_id):
    """List all files in a project"""
    project = Project.query.get_or_404(project_id)
    
    return jsonify({
        'files': [f.to_dict() for f in project.files]
    }), 200