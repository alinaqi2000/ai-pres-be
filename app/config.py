from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_USER = os.getenv("MYSQL_USER", "user")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "1122")
DB_NAME = os.getenv("MYSQL_DB", "ai_pres")
DB_PORT = os.getenv("MYSQL_PORT", "3306")

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "KAKAROT903")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "40"))

# Application configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# Database URL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
