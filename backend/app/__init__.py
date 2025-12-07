from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from backend.config import config
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__,
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Login manager settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Create storage directories
    os.makedirs(app.config['STORAGE_PATH'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
    
    # Register blueprints
    from backend.app.api.auth import auth_bp
    from backend.app.api.projects import projects_bp
    from backend.app.api.files import files_bp
    from backend.app.api.audit import audit_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    
    # Register main routes
    from backend.app.api.main import main_bp
    app.register_blueprint(main_bp)
    
    # User loader for Flask-Login
    from backend.app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app