import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the project root directory (where run.py lives)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    _database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/excel_gitlab_dev')
    if _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _database_url

    # File Storage - use absolute paths based on project root
    STORAGE_PATH = os.getenv('STORAGE_PATH', os.path.join(BASE_DIR, 'storage', 'files'))
    UPLOAD_PATH = os.getenv('UPLOAD_PATH', os.path.join(BASE_DIR, 'storage', 'uploads'))
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB
    
    # Excel Settings
    ALLOWED_EXTENSIONS = {'xlsx', 'xlsm', 'xls'}
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'RepoSync')
    APP_VERSION = os.getenv('APP_VERSION', '0.1.0')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/excel_gitlab_test'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}