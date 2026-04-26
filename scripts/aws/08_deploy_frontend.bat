@echo off
REM ============================================================
REM 08_deploy_frontend.bat
REM Builds Next.js frontend and deploys to AWS Amplify
REM No Git connection required - uses manual zip deployment
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 8: Deploy Frontend (Amplify)
echo ============================================================
echo.

set REGION=ap-south-1
set AMPLIFY_APP_NAME=vireon-frontend
set BRANCH_NAME=main
set FRONTEND_DIR=%~dp0..\..\frontend
set ZIP_PATH=%~dp0..\..\deployment.zip

REM ── Step 1: Build the frontend ───────────────────────────────
echo [1/6] Installing dependencies and building frontend...
pushd "%FRONTEND_DIR%"
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed
    popd
    exit /b 1
)
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] npm run build failed
    popd
    exit /b 1
)
popd
echo [OK] Frontend built successfully
echo.

REM ── Step 2: Create or get Amplify app ────────────────────────
echo [2/6] Checking for existing Amplify app...
for /f "tokens=*" %%i in ('aws amplify list-apps --region %REGION% --query "apps[?name==`%AMPLIFY_APP_NAME%`].appId" --output text 2^>nul') do set APP_ID=%%i

if "%APP_ID%"=="" (
    echo Creating new Amplify app: %AMPLIFY_APP_NAME%
    for /f "tokens=*" %%i in ('aws amplify create-app --name %AMPLIFY_APP_NAME% --platform WEB_COMPUTE --region %REGION% --query "app.appId" --output text') do set APP_ID=%%i
    echo [OK] Created Amplify app: %APP_ID%
) else (
    echo [SKIP] Amplify app already exists: %APP_ID%
)

REM ── Step 3: Create or get branch ─────────────────────────────
echo [3/6] Checking for branch: %BRANCH_NAME%...
aws amplify get-branch --app-id %APP_ID% --branch-name %BRANCH_NAME% --region %REGION% >nul 2>&1
if %errorlevel% neq 0 (
    aws amplify create-branch --app-id %APP_ID% --branch-name %BRANCH_NAME% --region %REGION% >nul
    echo [OK] Branch created: %BRANCH_NAME%
) else (
    echo [SKIP] Branch already exists: %BRANCH_NAME%
)
echo.

REM ── Step 4: Zip the build output ─────────────────────────────
echo [4/6] Zipping build output (static export)...
if exist "%ZIP_PATH%" del "%ZIP_PATH%"
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%FRONTEND_DIR%\out', '%ZIP_PATH%')"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create zip
    exit /b 1
)
echo [OK] Zip created: deployment.zip
echo.

REM ── Step 5: Create deployment and upload ─────────────────────
echo [5/6] Creating deployment slot and uploading zip...
powershell -Command "$d = (aws amplify create-deployment --app-id %APP_ID% --branch-name %BRANCH_NAME% --region %REGION% --output json | ConvertFrom-Json); $d.jobId | Out-File -FilePath ([System.IO.Path]::GetTempPath() + 'amp_job.txt') -Encoding ASCII -NoNewline; Invoke-WebRequest -Uri $d.zipUploadUrl -Method Put -InFile '%ZIP_PATH%' -ContentType 'application/zip' -UseBasicParsing | Out-Null; Write-Host 'Upload OK'"
if %errorlevel% neq 0 (
    echo [ERROR] Upload failed
    exit /b 1
)
set /p JOB_ID=<"%TEMP%\amp_job.txt"
echo Job ID: %JOB_ID%
echo [OK] Zip uploaded
echo.

REM ── Step 6: Start deployment ─────────────────────────────────
echo [6/6] Starting deployment...
aws amplify start-deployment --app-id %APP_ID% --branch-name %BRANCH_NAME% --job-id %JOB_ID% --region %REGION%
if %errorlevel% neq 0 (
    echo [ERROR] Deployment failed to start
    exit /b 1
)
echo [OK] Deployment started
echo.

REM ── Poll status ──────────────────────────────────────────────
echo Waiting for deployment to complete...
:POLL
timeout /t 15 /nobreak >nul
for /f "tokens=*" %%i in ('aws amplify get-job --app-id %APP_ID% --branch-name %BRANCH_NAME% --job-id %JOB_ID% --region %REGION% --query "job.summary.status" --output text') do set STATUS=%%i
echo   Status: %STATUS%
if "%STATUS%"=="RUNNING" goto POLL
if "%STATUS%"=="PENDING" goto POLL

echo.
if "%STATUS%"=="SUCCEED" (
    for /f "tokens=*" %%i in ('aws amplify get-app --app-id %APP_ID% --region %REGION% --query "app.defaultDomain" --output text') do set DOMAIN=%%i
    echo ============================================================
    echo  Deployment successful!
    echo  URL: https://%BRANCH_NAME%.%DOMAIN%
    echo ============================================================
) else (
    echo [ERROR] Deployment ended with status: %STATUS%
    echo Check logs: aws amplify get-job --app-id %APP_ID% --branch-name %BRANCH_NAME% --job-id %JOB_ID% --region %REGION%
    exit /b 1
)
