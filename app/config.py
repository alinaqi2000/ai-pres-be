from dotenv import load_dotenv
import os
from pathlib import Path
# Update this import to use pydantic-settings package
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_HOST = os.getenv("MYSQL_HOST", "db")
DB_USER = os.getenv("MYSQL_USER", "user")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
DB_NAME = os.getenv("MYSQL_DB", "ai_pres")
DB_PORT = os.getenv("MYSQL_PORT", "3306")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Application configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Base URL configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Upload configuration
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Email configuration
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@ai-pres.com")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "AI PRES")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_SERVER = os.getenv("EMAIL_SERVER", "mailhog")

# Database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


