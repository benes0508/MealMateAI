#!/usr/bin/env python3
"""
Local development script for the User Service.
This script helps set up a local development environment without Docker.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

# Add the current directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent))

def setup_env_vars(db_type="sqlite"):
    """Set up environment variables for local development"""
    if db_type == "sqlite":
        # Use SQLite for simplest local development
        os.environ["DATABASE_URL"] = "sqlite:///./user_service.db"
        os.environ["MYSQL_HOST"] = "localhost"  # Not used with SQLite but set for completeness
    else:
        # Use MySQL - requires a local MySQL instance
        os.environ["MYSQL_USER"] = "root"  # Change as needed
        os.environ["MYSQL_PASSWORD"] = "password"  # Change as needed
        os.environ["MYSQL_HOST"] = "localhost"
        os.environ["MYSQL_PORT"] = "3306"
        os.environ["MYSQL_DB"] = "user_service_db"
    
    # Set other required environment variables
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "local_development_secret_key"
    if "ALGORITHM" not in os.environ:
        os.environ["ALGORITHM"] = "HS256"
    if "ACCESS_TOKEN_EXPIRE_MINUTES" not in os.environ:
        os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

def patch_database_for_sqlite():
    """Patch the database.py file to use SQLite for local development"""
    db_file = Path(__file__).parent / "app" / "database.py"
    
    # Read the existing database.py content
    with open(db_file, "r") as f:
        content = f.read()
    
    # Check if we've already patched it
    if "sqlite_support" in content:
        return
    
    # Add SQLite support
    sqlite_patch = """
# Local development SQLite support
sqlite_support = os.getenv("DATABASE_URL", "").startswith("sqlite")
if sqlite_support:
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
    # SQLite specific configurations for engine
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # Original MySQL configuration
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
"""
    
    # Replace the engine creation part
    content = content.replace(
        '# Create the connection string\nSQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"\n\n# Create the SQLAlchemy engine\nengine = create_engine(SQLALCHEMY_DATABASE_URL)',
        '# Create the connection string\n' + sqlite_patch
    )
    
    # Write the patched content back
    with open(db_file, "w") as f:
        f.write(content)
    
    print("Patched database.py to support SQLite")

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        from dotenv import load_dotenv
        print("All required dependencies are installed.")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install requirements with: pip install -r requirements.txt")
        return False

def run_app():
    """Run the FastAPI app"""
    try:
        print("Starting user service on http://localhost:8000")
        print("API documentation available at http://localhost:8000/docs")
        # Run the app using the module approach
        subprocess.run([
            "python", "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error running server: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run User Service locally")
    parser.add_argument("--db", choices=["sqlite", "mysql"], default="sqlite",
                        help="Database to use (sqlite is easier for local development)")
    args = parser.parse_args()
    
    if not check_dependencies():
        return
    
    setup_env_vars(args.db)
    
    if args.db == "sqlite":
        patch_database_for_sqlite()
    
    run_app()

if __name__ == "__main__":
    main()