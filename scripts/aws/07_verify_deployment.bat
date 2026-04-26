@echo off
REM ============================================================
REM 07_verify_deployment.bat
REM Checks status of all deployed AWS resources
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 7: Verify Deployment
echo ============================================================
echo.

call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

set PREFIX=vireon-prod
echo Checking all resources...
echo.

REM ── RDS ──────────────────────────────────────────────────────
echo [RDS PostgreSQL]
for /f "tokens=*" %%i in ('aws rds describe-db-instances --db-instance-identifier %RDS_IDENTIFIER% --query "DBInstances[0].DBInstanceStatus" --output text --region %AWS_REGION% 2^>nul') do set RDS_STATUS=%%i
for /f "tokens=*" %%i in ('aws rds describe-db-instances --db-instance-identifier %RDS_IDENTIFIER% --query "DBInstances[0].Endpoint.Address" --output text --region %AWS_REGION% 2^>nul') do set RDS_HOST=%%i
echo   Status   : %RDS_STATUS%
echo   Endpoint : %RDS_HOST%
echo.

REM ── ElastiCache ──────────────────────────────────────────────
echo [ElastiCache Redis]
for /f "tokens=*" %%i in ('aws elasticache describe-cache-clusters --cache-cluster-id %REDIS_CLUSTER_ID% --query "CacheClusters[0].CacheClusterStatus" --output text --region %AWS_REGION% 2^>nul') do set REDIS_STATUS=%%i
for /f "tokens=*" %%i in ('aws elasticache describe-cache-clusters --cache-cluster-id %REDIS_CLUSTER_ID% --show-cache-node-info --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text --region %AWS_REGION% 2^>nul') do set REDIS_HOST=%%i
echo   Status   : %REDIS_STATUS%
echo   Endpoint : %REDIS_HOST%
echo.

REM ── S3 ───────────────────────────────────────────────────────
echo [S3 Bucket]
aws s3api head-bucket --bucket %S3_BUCKET% >nul 2>&1
set S3_EXISTS=%errorlevel%
if %S3_EXISTS% equ 0 (
    echo   Status : EXISTS and accessible
) else (
    echo   Status : NOT FOUND
)
echo.

REM ── ECS Backend ──────────────────────────────────────────────
echo [ECS Backend Service]
for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %PREFIX%-cluster --services %PREFIX%-backend --region %AWS_REGION% --query "services[0].status" --output text 2^>nul') do set BACKEND_STATUS=%%i
for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %PREFIX%-cluster --services %PREFIX%-backend --region %AWS_REGION% --query "services[0].runningCount" --output text 2^>nul') do set BACKEND_RUNNING=%%i
echo   Status        : %BACKEND_STATUS%
echo   Running Tasks : %BACKEND_RUNNING%
echo.

REM ── ALB URL ──────────────────────────────────────────────────
echo [Load Balancer]
for /f "tokens=*" %%i in ('aws elbv2 describe-load-balancers --names %PREFIX%-alb --query "LoadBalancers[0].DNSName" --output text --region %AWS_REGION% 2^>nul') do set ALB_DNS=%%i
echo   ALB DNS : %ALB_DNS%
echo.

REM ── ECS Workers ──────────────────────────────────────────────
echo [ECS Worker Services]
for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %PREFIX%-cluster --services %PREFIX%-worker --region %AWS_REGION% --query "services[0].runningCount" --output text 2^>nul') do set WORKER_RUNNING=%%i
for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %PREFIX%-cluster --services %PREFIX%-beat --region %AWS_REGION% --query "services[0].runningCount" --output text 2^>nul') do set BEAT_RUNNING=%%i
echo   Worker running : %WORKER_RUNNING%
echo   Beat running   : %BEAT_RUNNING%
echo.

REM ── ECR Images ───────────────────────────────────────────────
echo [ECR Images]
for /f "tokens=*" %%i in ('aws ecr describe-images --repository-name %ECR_REPO_BACKEND% --region %AWS_REGION% --query "imageDetails[0].imagePushedAt" --output text 2^>nul') do set ECR_PUSHED=%%i
echo   Backend image last pushed: %ECR_PUSHED%
echo.

REM ── Live health check ────────────────────────────────────────
if not "%ALB_DNS%"=="None" (
if not "%ALB_DNS%"=="" (
    echo [Live Health Check]
    echo   Pinging http://%ALB_DNS%/health/live ...
    curl -s -o nul -w "  HTTP Status: %%{http_code}" http://%ALB_DNS%/health/live
    echo.
    echo   Pinging http://%ALB_DNS%/health/ready ...
    curl -s -o nul -w "  HTTP Status: %%{http_code}" http://%ALB_DNS%/health/ready
    echo.
))

echo.
echo ============================================================
echo  Verification complete.
echo  API URL : http://%ALB_DNS%
echo  API Docs: http://%ALB_DNS%/api/v1/docs
echo ============================================================
