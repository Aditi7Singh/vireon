@echo off
REM ============================================================
REM 09_deploy_frontend_s3.bat
REM Deploys Next.js static export to S3 + CloudFront
REM This replaces Amplify for frontend hosting
REM Run from repo root: scripts\aws\09_deploy_frontend_s3.bat
REM ============================================================

echo ============================================================
echo  Vireon Frontend Deployment - S3 + CloudFront
echo ============================================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0\09_deploy_frontend_s3.ps1"
