# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
COPY requirements_agent.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements_agent.txt
RUN pip install --no-cache-dir celery redis

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

# Run emergency migrations to fix any missing columns before starting
RUN python emergency_migrations.py || true

CMD ["sh", "-c", "python emergency_migrations.py || true && uvicorn main:app --host 0.0.0.0 --port 8000"]
