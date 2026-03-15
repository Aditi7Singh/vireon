"""
Phase 4 Local Setup - Configure PostgreSQL and test integration
"""

import os
import sys
import subprocess
import time

print("=" * 70)
print("PHASE 4 LOCAL SETUP")
print("=" * 70)

# Step 1: Check for PostgreSQL
print("\n[1/3] Checking PostgreSQL installation...")

try:
    # Try to find PostgreSQL
    result = subprocess.run(["psql", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ PostgreSQL found: {result.stdout.strip()}")
    else:
        print("✗ PostgreSQL not found, trying alternative methods...")
except FileNotFoundError:
    print("✗ PostgreSQL not in PATH")

# Step 2: Create .env file  with local PostgreSQL
print("\n[2/3] Creating .env file...")

env_content = """# Groq API Configuration
GROQ_API_KEY=your_groq_key_here

# Backend Configuration  
BACKEND_URL=http://localhost:8000
API_TOKEN=your_api_token_here

# LLM Provider Selection
USE_LOCAL_LLM=false

# Ollama Configuration (if using local LLM)
OLLAMA_BASE_URL=http://localhost:11434

# Company Configuration
COMPANY_NAME=SeedlingLabs

# Session Database Path
SESSION_DB_PATH=./data/sessions.db

# ============================================================================
# PHASE 4: ANOMALY DETECTION ENGINE
# ============================================================================

# PostgreSQL Database URL - LOCAL DEVELOPMENT
# For Docker: docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15-alpine
# Or use Neon.tech for cloud: postgresql://user:password@neon-host.neon.tech/dbname
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vireon

# Redis Configuration
# Local: redis://localhost:6379/0
# Or use: docker run -d --name redis -p 6379:6379 redis:7-alpine
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
"""

# Check if .env already exists in backend
backend_env = "backend/.env"
if os.path.exists(backend_env):
    print(f"⚠ {backend_env} already exists, skipping creation")
else:
    with open(backend_env, "w") as f:
        f.write(env_content)
    print(f"✓ Created {backend_env}")

# Check if .env exists in root
root_env = ".env"
if os.path.exists(root_env):
    print(f"⚠ {root_env} already exists")
else:
    with open(root_env, "w") as f:
        f.write(env_content)
    print(f"✓ Created {root_env}")

# Step 3: Print Quick Start Guide
print("\n[3/3] Quick Start Guide")
print("=" * 70)

print("""
To get Phase 4 running locally:

OPTION 1: Using Docker (Recommended)
-------------------------------------
1. Start PostgreSQL:
   docker run -d --name postgres \\
     -e POSTGRES_PASSWORD=postgres \\
     -p 5432:5432 \\
     postgres:15-alpine

2. Start Redis:
   docker run -d --name redis \\
     -p 6379:6379 \\
     redis:7-alpine

3. Wait 3-5 seconds for services to start, then seed data:
   python backend/anomaly/seed_alerts.py

4. Verify integration:
   python backend/anomaly/verify_agent_integration.py

5. Start the backend:
   cd backend && uvicorn main:app --reload --port 8000

OPTION 2: Local PostgreSQL & Redis
-----------------------------------
If you have PostgreSQL and Redis installed locally, simply run:

1. Verify connections:
   psql -h localhost -U postgres -c "SELECT 1;"
   redis-cli ping

2. Seed data:
   python backend/anomaly/seed_alerts.py

3. Start backend:
   cd backend && uvicorn main:app --reload

ENVIRONMENT VARIABLES:
- DATABASE_URL: PostgreSQL connection (now in .env)
- REDIS_URL: Redis connection (now in .env)
- GROQ_API_KEY: Required for Phase 3 agent (get from groq.com)

TROUBLESHOOTING:
- "Connection refused": Docker services not running
- "psycopg2.OperationalError": Database doesn't exist yet
- Run: psql $DATABASE_URL -c "SELECT 1;" to verify DB connection

Next steps:
1. Start PostgreSQL and Redis (Docker or local)
2. python backend/anomaly/seed_alerts.py
3. python backend/anomaly/verify_agent_integration.py
4. cd backend && uvicorn main:app --reload
""")

print("=" * 70)
print("Setup complete! Check the guide above for next steps.")
print("=" * 70)
