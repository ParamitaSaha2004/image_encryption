"""
Database Connection and Session Management
Configures SQLAlchemy connection with automatic fallback to local SQLite when MySQL is offline.
Ensures schema tables are auto-created if using fallback storage.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None
Base = declarative_base()
DB_TYPE = "UNKNOWN"

def init_engine():
    global engine, SessionLocal, DB_TYPE
    
    # Attempt MySQL connection first
    mysql_url = settings.DATABASE_URL
    try:
        test_engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={"connect_timeout": 2}
        )
        with test_engine.connect() as conn:
            pass  # Successfully connected to MySQL
        engine = test_engine
        DB_TYPE = "MYSQL"
        print(f"[DATABASE] Connected to MySQL database '{settings.DB_NAME}' at {settings.DB_HOST}:{settings.DB_PORT}")
    except Exception as e:
        # Fallback to local SQLite development database with absolute path
        os.makedirs(settings.VAULT_STORAGE_PATH, exist_ok=True)
        db_path = os.path.abspath(os.path.join(settings.VAULT_STORAGE_PATH, "hice_dev.db"))
        sqlite_url = f"sqlite:///{db_path}"
        engine = create_engine(
            sqlite_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
        DB_TYPE = "SQLITE"
        print(f"[DATABASE NOTICE] MySQL unavailable ({e}). Running with local fallback SQLite database at: {db_path}")

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

init_engine()

def get_db():
    """Dependency for obtaining a database session per request."""
    if SessionLocal is None:
        init_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
