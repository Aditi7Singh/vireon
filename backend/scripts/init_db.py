import os
from database import engine, Base
import models

def init_db():
    print("🚀 Initializing Neon database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully (or already exist).")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
