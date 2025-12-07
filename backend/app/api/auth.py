from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.app import db
from backend.app.models.user import User
from backend.app.models.audit_log import AuditLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('auth/register.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(username=username, email=email, role='editor')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    AuditLog.log_action(
        user_id=user.id,
        action='user_registered',
        details={'username': username, 'email': email},
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not all([username, password]):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    login_user(user, remember=remember)
    
    AuditLog.log_action(
        user_id=user.id,
        action='user_login',
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    user_id = current_user.id
    
    AuditLog.log_action(
        user_id=user_id,
        action='user_logout',
        ip_address=request.remote_addr
    )
    db.session.commit()
    
    logout_user()
    
    return jsonify({'message': 'Logout successful'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        'user': current_user.to_dict()
    }), 200