from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/health')
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "healthy"}), 200


@main_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')


@main_bp.route('/projects/<int:project_id>')
@login_required
def project_detail(project_id):
    """Project detail page"""
    return render_template('project_detail.html', project_id=project_id)


@main_bp.route('/files/<int:file_id>')
@login_required
def file_detail(file_id):
    """File detail page"""
    return render_template('file_detail.html', file_id=file_id)