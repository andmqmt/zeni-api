from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Parse the database URL to detect if it's PostgreSQL
_db_url = settings.database_url

# Render uses PostgreSQL — optimize pool for their free/starter tier:
# - pool_size=5: Render free tier has limited connections (~20 max)
# - max_overflow=5: Allow small bursts without hogging connections
# - pool_recycle=1800: Recycle stale connections (Render may close idle ones)
# - pool_pre_ping=True: Detect broken connections before using them
engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    pool_timeout=10,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
