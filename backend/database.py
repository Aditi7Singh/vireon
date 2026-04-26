import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback for local development when DATABASE_URL is not set.
    # Defaults align with docker-compose.yml:
    # POSTGRES_USER=vireon, POSTGRES_PASSWORD=vireon123, POSTGRES_DB=vireon, host-port 5433.
    db_user = os.getenv("POSTGRES_USER", "vireon")
    db_password = os.getenv("POSTGRES_PASSWORD", "vireon123")
    db_name = os.getenv("POSTGRES_DB", "vireon")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
