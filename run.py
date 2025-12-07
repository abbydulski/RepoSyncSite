#!/usr/bin/env python
"""
Main entry point for RepoSync application
"""
import os
from backend.app import create_app, db
from backend.app.models import User, Project, File, Version, AuditLog

app = create_app()

# Auto-create database tables on startup (for Railway/production)
with app.app_context():
    db.create_all()


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Project': Project,
        'File': File,
        'Version': Version,
        'AuditLog': AuditLog
    }


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print("Database initialized!")


@app.cli.command()
def create_admin():
    """Create an admin user"""
    username = input("Admin username: ")
    email = input("Admin email: ")
    password = input("Admin password: ")
    
    user = User(username=username, email=email, role='admin')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)