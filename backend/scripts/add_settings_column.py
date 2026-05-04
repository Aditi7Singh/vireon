#!/usr/bin/env python
"""Add missing 'settings' column to companies table. Run when database is accessible."""

import os
import sys
from sqlalchemy import create_engine, Column, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("POSTGRES_USER", "vireon")
    db_password = os.getenv("POSTGRES_PASSWORD", "vireon123")
    db_name = os.getenv("POSTGRES_DB", "vireon")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"Connecting to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else '', '')}")

engine = create_engine(DATABASE_URL)

# Check if column exists
inspector = inspect(engine)
columns = [col["name"] for col in inspector.get_columns("companies")]

if "settings" in columns:
    print("Column 'settings' already exists. No action needed.")
    sys.exit(0)

# Add column using raw SQL for maximum compatibility
with engine.connect() as conn:
    conn.execute("""
        ALTER TABLE companies 
        ADD COLUMN settings JSONB NULL DEFAULT '{}';
    """)
    conn.commit()
    print("Successfully added 'settings' column to companies table.")
