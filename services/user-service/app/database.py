from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get MySQL connection details from environment variables (fallback to default values for dev)
MYSQL_USER = os.getenv("MYSQL_USER", "user_service_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "user_service_password")
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "user_service_db")

# Create the connection string
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Create the SQLAlchemy engine with retry logic
def get_engine(max_retries=5, retry_interval=2):
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Attempting to connect to MySQL (attempt {attempt+1}/{max_retries})...")
            engine = create_engine(SQLALCHEMY_DATABASE_URL)
            # Verify connection by executing a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to MySQL")
            return engine
        except Exception as e:
            last_error = e
            attempt += 1
            if attempt < max_retries:
                logger.warning(f"Failed to connect to MySQL: {e}. Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error(f"Failed to connect to MySQL after {max_retries} attempts: {e}")
    
    # If we get here, all attempts failed
    raise last_error

# Initialize engine with retry mechanism
try:
    engine = get_engine()
except Exception as e:
    logger.error(f"Could not establish connection to database: {e}")
    # Continue anyway - the application will try again when handling requests
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()