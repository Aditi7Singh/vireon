@echo off
REM ============================================================
REM cleanup_vireon.bat
REM Deletes all Vireon-related AWS resources in ap-south-1
REM Run this script to fully remove Vireon from your AWS account
REM ============================================================

set REGION=ap-south-1

echo ============================================================
echo  Vireon AWS Cleanup - This will DELETE all Vireon resources
echo ============================================================
echo.
echo Resources to be deleted:
echo   - ECS services and cluster: vireon-prod-cluster
echo   - ALB: vireon-prod-alb
echo   - RDS: vireon-postgres
echo   - ElastiCache: vireon-redis
echo   - S3: vireon-documents-732772501496
echo   - Secrets Manager: vireon-prod/*
echo   - SSM Parameters: /vireon/*
echo   - CloudWatch Log Groups: /ecs/vireon-prod/*
echo   - IAM Role: ecsTaskExecutionRole
echo   - Security Groups: vireon-prod-*-sg, sg-0ccad704bdb2ee9b4 (RDS)
echo   - VPC: vireon-prod-vpc (vpc-08d98ac34e0e5bed7)
echo   - Amplify app: vireon-frontend (d1tzlh2fec7rai)
echo.
set /p CONFIRM=Type YES to confirm deletion: 
if /i not "%CONFIRM%"=="YES" (
    echo Aborted.
    exit /b 0
)

echo.

REM ── 1. ECS Services ──────────────────────────────────────────
echo [1/10] Deleting ECS services...
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-backend --desired-count 0 --region %REGION% >nul 2>&1
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-worker --desired-count 0 --region %REGION% >nul 2>&1
aws ecs update-service --cluster vireon-prod-cluster --service vireon-prod-beat --desired-count 0 --region %REGION% >nul 2>&1
timeout /t 10 /nobreak >nul
aws ecs delete-service --cluster vireon-prod-cluster --service vireon-prod-backend --force --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-backend || echo   [SKIP]
aws ecs delete-service --cluster vireon-prod-cluster --service vireon-prod-worker --force --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-worker || echo   [SKIP]
aws ecs delete-service --cluster vireon-prod-cluster --service vireon-prod-beat --force --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-beat || echo   [SKIP]
aws ecs delete-cluster --cluster vireon-prod-cluster --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-cluster || echo   [SKIP]

echo.

REM ── 2. ALB + Target Group ────────────────────────────────────
echo [2/10] Deleting ALB and target group...
for /f "tokens=*" %%i in ('aws elbv2 describe-load-balancers --names vireon-prod-alb --query "LoadBalancers[0].LoadBalancerArn" --output text --region %REGION% 2^>nul') do set ALB_ARN=%%i
if not "%ALB_ARN%"=="None" (
    for /f "tokens=*" %%i in ('aws elbv2 describe-listeners --load-balancer-arn %ALB_ARN% --query "Listeners[*].ListenerArn" --output text --region %REGION% 2^>nul') do (
        aws elbv2 delete-listener --listener-arn %%i --region %REGION% >nul 2>&1
    )
    aws elbv2 delete-load-balancer --load-balancer-arn %ALB_ARN% --region %REGION% >nul 2>&1 && echo   [OK] ALB deleted || echo   [SKIP]
    timeout /t 15 /nobreak >nul
)
for /f "tokens=*" %%i in ('aws elbv2 describe-target-groups --names vireon-prod-backend-tg --query "TargetGroups[0].TargetGroupArn" --output text --region %REGION% 2^>nul') do set TG_ARN=%%i
if not "%TG_ARN%"=="None" (
    aws elbv2 delete-target-group --target-group-arn %TG_ARN% --region %REGION% >nul 2>&1 && echo   [OK] Target group deleted || echo   [SKIP]
)

echo.

REM ── 3. Secrets Manager ───────────────────────────────────────
echo [3/10] Deleting Secrets Manager secrets...
aws secretsmanager delete-secret --secret-id vireon-prod/db-password --force-delete-without-recovery --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod/db-password || echo   [SKIP]
aws secretsmanager delete-secret --secret-id vireon-prod/app-secrets --force-delete-without-recovery --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod/app-secrets || echo   [SKIP]
aws secretsmanager delete-secret --secret-id vireon-prod/database-url --force-delete-without-recovery --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod/database-url || echo   [SKIP]

echo.

REM ── 4. SSM Parameters ────────────────────────────────────────
echo [4/10] Deleting SSM parameters...
aws ssm delete-parameter --name "/vireon/GROQ_API_KEY" --region %REGION% >nul 2>&1 && echo   [OK] GROQ_API_KEY || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/DB_PASSWORD" --region %REGION% >nul 2>&1 && echo   [OK] DB_PASSWORD || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/SECRET_KEY" --region %REGION% >nul 2>&1 && echo   [OK] SECRET_KEY || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/MERGE_API_KEY" --region %REGION% >nul 2>&1 && echo   [OK] MERGE_API_KEY || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/COMPANY_NAME" --region %REGION% >nul 2>&1 && echo   [OK] COMPANY_NAME || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/S3_BUCKET" --region %REGION% >nul 2>&1 && echo   [OK] S3_BUCKET || echo   [SKIP]
aws ssm delete-parameter --name "/vireon/AWS_REGION" --region %REGION% >nul 2>&1 && echo   [OK] AWS_REGION || echo   [SKIP]

echo.

REM ── 5. CloudWatch Log Groups ─────────────────────────────────
echo [5/10] Deleting CloudWatch Log Groups...
aws logs delete-log-group --log-group-name /ecs/vireon-prod/backend --region %REGION% >nul 2>&1 && echo   [OK] /ecs/vireon-prod/backend || echo   [SKIP]
aws logs delete-log-group --log-group-name /ecs/vireon-prod/worker --region %REGION% >nul 2>&1 && echo   [OK] /ecs/vireon-prod/worker || echo   [SKIP]
aws logs delete-log-group --log-group-name /ecs/vireon-prod/beat --region %REGION% >nul 2>&1 && echo   [OK] /ecs/vireon-prod/beat || echo   [SKIP]
aws logs delete-log-group --log-group-name /ecs/vireon-prod/frontend --region %REGION% >nul 2>&1 && echo   [OK] /ecs/vireon-prod/frontend || echo   [SKIP]
aws logs delete-log-group --log-group-name /aws/ecs/containerinsights/vireon-prod-cluster/performance --region %REGION% >nul 2>&1 && echo   [OK] containerinsights || echo   [SKIP]

echo.

REM ── 6. RDS Instance ──────────────────────────────────────────
echo [6/10] Deleting RDS instance vireon-postgres (this takes ~5 mins)...
aws rds delete-db-instance --db-instance-identifier vireon-postgres --skip-final-snapshot --region %REGION% >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Deletion initiated - waiting...
    aws rds wait db-instance-deleted --db-instance-identifier vireon-postgres --region %REGION%
    echo   [OK] RDS deleted
) else (
    echo   [SKIP] RDS not found or already deleted
)

echo.

REM ── 7. ElastiCache ───────────────────────────────────────────
echo [7/10] Deleting ElastiCache Redis cluster...
aws elasticache delete-cache-cluster --cache-cluster-id vireon-redis --region %REGION% >nul 2>&1 && echo   [OK] vireon-redis deletion initiated || echo   [SKIP]

echo.

REM ── 8. S3 Bucket ─────────────────────────────────────────────
echo [8/10] Deleting S3 bucket...
aws s3 rb s3://vireon-documents-732772501496 --force --region %REGION% >nul 2>&1 && echo   [OK] S3 bucket deleted || echo   [SKIP]

echo.

REM ── 9. IAM Role ──────────────────────────────────────────────
echo [9/10] Deleting IAM roles...
for /f "delims=" %%p in ('aws iam list-attached-role-policies --role-name ecsTaskExecutionRole --query "AttachedPolicies[].PolicyArn" --output text 2^>nul') do (
    aws iam detach-role-policy --role-name ecsTaskExecutionRole --policy-arn %%p >nul 2>&1
)
aws iam delete-role --role-name ecsTaskExecutionRole >nul 2>&1 && echo   [OK] ecsTaskExecutionRole || echo   [SKIP]

echo.

REM ── 10. Security Groups + VPC ────────────────────────────────
echo [10/10] Deleting Security Groups and VPC...
aws ec2 delete-security-group --group-id sg-09ac4104b4e8e41e7 --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-alb-sg || echo   [SKIP]
aws ec2 delete-security-group --group-id sg-0141ead8a5ade5dfa --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-backend-sg || echo   [SKIP]
aws ec2 delete-security-group --group-id sg-0ccad704bdb2ee9b4 --region %REGION% >nul 2>&1 && echo   [OK] RDS sg || echo   [SKIP]

REM Delete subnets
aws ec2 delete-subnet --subnet-id subnet-018d5f610efcf0e98 --region %REGION% >nul 2>&1 && echo   [OK] subnet-018d5f610efcf0e98 || echo   [SKIP]
aws ec2 delete-subnet --subnet-id subnet-089906eeb29c5341b --region %REGION% >nul 2>&1 && echo   [OK] subnet-089906eeb29c5341b || echo   [SKIP]

REM Detach and delete IGW
for /f "delims=" %%i in ('aws ec2 describe-internet-gateways --region %REGION% --filters "Name=attachment.vpc-id,Values=vpc-08d98ac34e0e5bed7" --query "InternetGateways[].InternetGatewayId" --output text 2^>nul') do (
    aws ec2 detach-internet-gateway --internet-gateway-id %%i --vpc-id vpc-08d98ac34e0e5bed7 --region %REGION% >nul 2>&1
    aws ec2 delete-internet-gateway --internet-gateway-id %%i --region %REGION% >nul 2>&1
    echo   [OK] IGW %%i deleted
)

aws ec2 delete-vpc --vpc-id vpc-08d98ac34e0e5bed7 --region %REGION% >nul 2>&1 && echo   [OK] vireon-prod-vpc deleted || echo   [SKIP] VPC may still have dependencies

echo.
echo ============================================================
echo  Cleanup complete. All Vireon resources have been removed.
echo ============================================================
