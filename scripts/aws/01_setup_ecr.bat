@echo off
REM ============================================================
REM 01_setup_ecr.bat
REM Creates ECR repositories for backend and worker images
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 1: Create ECR Repositories
echo ============================================================
echo.

REM Load config (works from any directory)
call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

echo Creating ECR repository: %ECR_REPO_BACKEND%
aws ecr describe-repositories --repository-names %ECR_REPO_BACKEND% --region %AWS_REGION% >nul 2>&1
if %errorlevel% neq 0 (
    aws ecr create-repository ^
        --repository-name %ECR_REPO_BACKEND% ^
        --region %AWS_REGION% ^
        --image-scanning-configuration scanOnPush=true
    echo [OK] Created %ECR_REPO_BACKEND%
) else (
    echo [SKIP] %ECR_REPO_BACKEND% already exists
)

echo.
echo Creating ECR repository: %ECR_REPO_WORKER%
aws ecr describe-repositories --repository-names %ECR_REPO_WORKER% --region %AWS_REGION% >nul 2>&1
if %errorlevel% neq 0 (
    aws ecr create-repository ^
        --repository-name %ECR_REPO_WORKER% ^
        --region %AWS_REGION% ^
        --image-scanning-configuration scanOnPush=true
    echo [OK] Created %ECR_REPO_WORKER%
) else (
    echo [SKIP] %ECR_REPO_WORKER% already exists
)

echo.
echo ECR repositories ready.
echo.
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Account" --output text') do set AWS_ACCOUNT=%%i
echo Backend image URI : %AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_BACKEND%:latest
echo Worker image URI  : %AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_WORKER%:latest
