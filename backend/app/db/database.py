import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

db_url = settings.DATABASE_URL

if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

if db_url and db_url.startswith("postgresql"):
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        # Verify connection
        with engine.connect() as conn:
            pass
        logger.info(f"Connected to PostgreSQL database: {db_url.split('@')[-1] if '@' in db_url else 'configured'}")
    except Exception as e:
        logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database.")
        db_url = "sqlite:///./graphguard.db"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
else:
    logger.info("DATABASE_URL unconfigured or using SQLite. Initializing embedded SQLite database.")
    db_url = "sqlite:///./graphguard.db"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for obtaining database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
