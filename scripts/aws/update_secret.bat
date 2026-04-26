@echo off
REM ============================================================
REM update_secret.bat
REM Updates a secret in SSM and forces ECS service redeployment
REM Usage: update_secret.bat GROQ_API_KEY your_new_value
REM        update_secret.bat APP_SECRET_KEY your_new_value
REM        update_secret.bat DB_PASSWORD your_new_value
REM ============================================================

set SECRET_NAME=%1
set SECRET_VALUE=%2

if "%SECRET_NAME%"=="" (
    echo Usage: update_secret.bat SECRET_NAME NEW_VALUE
    echo.
    echo Available secrets:
    echo   GROQ_API_KEY
    echo   APP_SECRET_KEY
    echo   DB_PASSWORD
    echo   MERGE_API_KEY
    echo   COMPANY_NAME
    exit /b 1
)
if "%SECRET_VALUE%"=="" (
    echo [ERROR] No value provided
    echo Usage: update_secret.bat SECRET_NAME NEW_VALUE
    exit /b 1
)

set REGION=ap-south-1
set PREFIX=vireon-prod

echo [1/2] Updating /vireon/%SECRET_NAME% in SSM Parameter Store...
aws ssm put-parameter --name "/vireon/%SECRET_NAME%" --value "%SECRET_VALUE%" --type SecureString --overwrite --region %REGION%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to update SSM parameter
    exit /b 1
)
echo [OK] SSM updated

echo.
echo [2/2] Forcing ECS service redeployment to pick up new value...
aws ecs update-service --cluster %PREFIX%-cluster --service %PREFIX%-backend --force-new-deployment --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ECS backend service redeployment triggered
    echo      New tasks will start in ~2-3 minutes with the updated secret
) else (
    echo [SKIP] ECS service not found - secret updated in SSM, will take effect on next deploy
)
