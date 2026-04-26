@echo off
REM ============================================================
REM 00_prerequisites_check.bat
REM Checks that all required tools are installed before deploying
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Prerequisites Check
echo ============================================================
echo.

set ERRORS=0

REM Check AWS CLI
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] AWS CLI - Install from https://aws.amazon.com/cli/
    set ERRORS=1
) else (
    for /f "tokens=*" %%i in ('aws --version 2^>^&1') do echo [OK]     AWS CLI: %%i
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] Docker - Install from https://www.docker.com/products/docker-desktop
    set ERRORS=1
) else (
    for /f "tokens=*" %%i in ('docker --version') do echo [OK]     Docker: %%i
)

REM Check AWS credentials configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] AWS credentials not configured - Run: aws configure
    set ERRORS=1
) else (
    for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Account" --output text') do echo [OK]     AWS Account: %%i
    for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Arn" --output text') do echo [OK]     AWS Identity: %%i
)

REM Check AWS region is set
for /f "tokens=*" %%i in ('aws configure get region') do set AWS_REGION=%%i
if "%AWS_REGION%"=="" (
    echo [MISSING] AWS region not set - Run: aws configure
    set ERRORS=1
) else (
    echo [OK]     AWS Region: %AWS_REGION%
)

echo.
if %ERRORS%==0 (
    echo All prerequisites met. You can proceed with deployment.
) else (
    echo One or more prerequisites are missing. Please fix them before proceeding.
    exit /b 1
)
