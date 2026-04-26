@echo off
REM ============================================================
REM 03_setup_infrastructure.bat
REM Creates RDS PostgreSQL, ElastiCache Redis, S3 bucket,
REM and SSM Parameter Store secrets
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 3: Setup Infrastructure
echo ============================================================
echo.

REM Load config (works from any directory)
call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

REM ── S3 Bucket ────────────────────────────────────────────────
echo [1/4] Creating S3 bucket: %S3_BUCKET%
aws s3api head-bucket --bucket %S3_BUCKET% 2>nul
if %errorlevel% neq 0 (
    if "%AWS_REGION%"=="ap-south-1" (
        aws s3api create-bucket --bucket %S3_BUCKET% --region %AWS_REGION% --create-bucket-configuration LocationConstraint=%AWS_REGION%
    ) else (
        aws s3api create-bucket --bucket %S3_BUCKET% --region %AWS_REGION% --create-bucket-configuration LocationConstraint=%AWS_REGION%
    )
    aws s3api put-bucket-versioning --bucket %S3_BUCKET% --versioning-configuration Status=Enabled
    aws s3api put-public-access-block --bucket %S3_BUCKET% --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
    echo [OK] S3 bucket created and secured
) else (
    echo [SKIP] S3 bucket already exists
)

echo.

REM ── RDS PostgreSQL ───────────────────────────────────────────
echo [2/4] RDS PostgreSQL - checking...
aws rds describe-db-instances --db-instance-identifier %RDS_IDENTIFIER% --region %AWS_REGION% >nul 2>&1
set RDS_EXISTS=%errorlevel%
if %RDS_EXISTS% neq 0 (
    echo Creating RDS instance...
    aws rds create-db-instance --db-instance-identifier %RDS_IDENTIFIER% --db-instance-class db.t3.micro --engine postgres --engine-version 15 --master-username %DB_USER% --master-user-password %DB_PASSWORD% --db-name %DB_NAME% --allocated-storage 20 --storage-type gp2 --publicly-accessible --backup-retention-period 0 --region %AWS_REGION%
    echo [OK] RDS creation initiated
) else (
    echo [SKIP] RDS instance already exists
)

echo.

REM ── ElastiCache Redis ────────────────────────────────────────
echo [3/4] ElastiCache Redis - checking...
aws elasticache describe-cache-clusters --cache-cluster-id %REDIS_CLUSTER_ID% --region %AWS_REGION% >nul 2>&1
set REDIS_EXISTS=%errorlevel%
if %REDIS_EXISTS% neq 0 (
    aws elasticache create-cache-cluster --cache-cluster-id %REDIS_CLUSTER_ID% --cache-node-type cache.t3.micro --engine redis --engine-version 7.0 --num-cache-nodes 1 --region %AWS_REGION%
    echo [OK] ElastiCache Redis creation initiated
) else (
    echo [SKIP] ElastiCache cluster already exists
)

echo.

REM ── SSM Parameter Store (secrets) ───────────────────────────
echo [4/4] Storing secrets in SSM Parameter Store...

aws ssm put-parameter --name "/vireon/GROQ_API_KEY"       --value "%GROQ_API_KEY%"       --type SecureString --overwrite --region %AWS_REGION% >nul
aws ssm put-parameter --name "/vireon/DB_PASSWORD"         --value "%DB_PASSWORD%"         --type SecureString --overwrite --region %AWS_REGION% >nul
aws ssm put-parameter --name "/vireon/SECRET_KEY"          --value "%APP_SECRET_KEY%"      --type SecureString --overwrite --region %AWS_REGION% >nul
aws ssm put-parameter --name "/vireon/COMPANY_NAME"        --value "%COMPANY_NAME%"        --type String       --overwrite --region %AWS_REGION% >nul
aws ssm put-parameter --name "/vireon/S3_BUCKET"           --value "%S3_BUCKET%"           --type String       --overwrite --region %AWS_REGION% >nul
aws ssm put-parameter --name "/vireon/AWS_REGION"          --value "%AWS_REGION%"          --type String       --overwrite --region %AWS_REGION% >nul
if not "%MERGE_API_KEY%"=="" (
    aws ssm put-parameter --name "/vireon/MERGE_API_KEY" --value "%MERGE_API_KEY%" --type SecureString --overwrite --region %AWS_REGION% >nul
)

echo [OK] Secrets stored in SSM Parameter Store
echo.
echo Infrastructure setup complete.
echo NOTE: Wait for RDS and ElastiCache to reach 'available' status before running step 4.
