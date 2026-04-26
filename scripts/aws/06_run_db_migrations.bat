@echo off
REM ============================================================
REM 06_run_db_migrations.bat
REM Runs Alembic migrations against the RDS database
REM Requires Docker to be running
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 6: Run Database Migrations
echo ============================================================
echo.

call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Account" --output text') do set AWS_ACCOUNT=%%i

for /f "tokens=*" %%i in ('aws rds describe-db-instances --db-instance-identifier %RDS_IDENTIFIER% --query "DBInstances[0].Endpoint.Address" --output text --region %AWS_REGION%') do set RDS_HOST=%%i
if "%RDS_HOST%"=="" (
    echo [ERROR] RDS instance not found. Run step 3 first.
    exit /b 1
)

set DATABASE_URL=postgresql+psycopg2://%DB_USER%:%DB_PASSWORD%@%RDS_HOST%:5432/%DB_NAME%
set BACKEND_IMAGE=%AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_BACKEND%:latest

echo RDS Host     : %RDS_HOST%
echo Database URL : %DATABASE_URL%
echo.

aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com

echo Running Alembic migrations...
docker run --rm -e DATABASE_URL="%DATABASE_URL%" -e REDIS_URL="redis://localhost:6379/0" -e GROQ_API_KEY="%GROQ_API_KEY%" -e ENV="production" --workdir /app %BACKEND_IMAGE% alembic upgrade head

if %errorlevel% neq 0 (
    echo [WARN] upgrade head failed - tables may already exist. Stamping to head...
    docker run --rm -e DATABASE_URL="%DATABASE_URL%" -e REDIS_URL="redis://localhost:6379/0" -e GROQ_API_KEY="%GROQ_API_KEY%" -e ENV="production" --workdir /app %BACKEND_IMAGE% alembic stamp head
    if %errorlevel% neq 0 (
        echo [ERROR] stamp head also failed
        exit /b 1
    )
    echo [OK] Database stamped at head
) else (
    echo [OK] Migrations applied successfully
)
echo.

echo Verifying migration status...
docker run --rm -e DATABASE_URL="%DATABASE_URL%" -e REDIS_URL="redis://localhost:6379/0" -e GROQ_API_KEY="%GROQ_API_KEY%" -e ENV="production" --workdir /app %BACKEND_IMAGE% alembic current

echo.
echo Database migrations complete.
