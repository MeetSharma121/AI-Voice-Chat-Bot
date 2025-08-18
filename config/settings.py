"""
Configuration settings for the Healthcare Chatbot
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Azure Cognitive Services
    AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION', 'westeurope')
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4')
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', '1000'))
    
    # Vector Database Configuration
    PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
    PINECONE_ENVIRONMENT = os.environ.get('PINECONE_ENVIRONMENT', 'us-west1-gcp')
    PINECONE_INDEX_NAME = os.environ.get('PINECONE_INDEX_NAME', 'nhs-healthcare')
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///healthcare_chatbot.db')
    DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
    
    # Security and Compliance
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'dev-encryption-key')
    GDPR_COMPLIANCE = os.environ.get('GDPR_COMPLIANCE', 'True').lower() == 'true'
    NHS_COMPLIANCE = os.environ.get('NHS_COMPLIANCE', 'True').lower() == 'true'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    
    # Voice Configuration
    VOICE_ENABLED = os.environ.get('VOICE_ENABLED', 'True').lower() == 'true'
    DEFAULT_VOICE = os.environ.get('DEFAULT_VOICE', 'en-GB')
    SPEECH_RECOGNITION_TIMEOUT = int(os.environ.get('SPEECH_RECOGNITION_TIMEOUT', '5'))
    TTS_SPEED = float(os.environ.get('TTS_SPEED', '1.0'))
    
    # RAG Configuration
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-ada-002')
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '200'))
    TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', '5'))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/healthcare_chatbot.log')
    
    # Monitoring Configuration
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'True').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', '9090'))
    
    # Twilio Configuration (for phone calls)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'ogg'}
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_DEFAULT = "100 per minute"
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # WebSocket Configuration
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        # Set up additional configurations
        if app.config['DATABASE_TYPE'] == 'sqlite':
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE_URL']
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = app.config['DATABASE_URL']
        
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    DATABASE_URL = 'sqlite:///dev_healthcare_chatbot.db'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///test_healthcare_chatbot.db'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    SESSION_COOKIE_SECURE = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/healthcare_chatbot.log', maxBytes=10240000, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Healthcare Chatbot startup')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 