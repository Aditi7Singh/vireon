@echo off
REM ============================================================
REM 02_build_and_push.bat
REM Builds Docker images and pushes them to ECR
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 2: Build and Push Images
echo ============================================================
echo.

REM Load config (works from any directory)
call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

REM Get AWS account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Account" --output text') do set AWS_ACCOUNT=%%i
echo AWS Account: %AWS_ACCOUNT%
echo AWS Region : %AWS_REGION%
echo.

REM Set full image URIs
set BACKEND_IMAGE=%AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_BACKEND%:latest
set WORKER_IMAGE=%AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_WORKER%:latest

REM Login to ECR
echo Logging in to ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com
if %errorlevel% neq 0 (
    echo [ERROR] ECR login failed
    exit /b 1
)
echo [OK] ECR login successful
echo.

REM Build backend image
echo Building backend image...
docker build -t %ECR_REPO_BACKEND%:latest ./backend
if %errorlevel% neq 0 (
    echo [ERROR] Backend image build failed
    exit /b 1
)
echo [OK] Backend image built
echo.

REM Tag and push backend
echo Pushing backend image to ECR...
docker tag %ECR_REPO_BACKEND%:latest %BACKEND_IMAGE%
docker push %BACKEND_IMAGE%
if %errorlevel% neq 0 (
    echo [ERROR] Backend image push failed
    exit /b 1
)
echo [OK] Backend image pushed: %BACKEND_IMAGE%
echo.

REM Worker uses the same Dockerfile, just a different CMD at runtime
REM Tag the same image as worker too
echo Tagging backend image as worker image...
docker tag %ECR_REPO_BACKEND%:latest %WORKER_IMAGE%
docker push %WORKER_IMAGE%
if %errorlevel% neq 0 (
    echo [ERROR] Worker image push failed
    exit /b 1
)
echo [OK] Worker image pushed: %WORKER_IMAGE%
echo.

echo Images pushed successfully.
echo Backend : %BACKEND_IMAGE%
echo Worker  : %WORKER_IMAGE%
