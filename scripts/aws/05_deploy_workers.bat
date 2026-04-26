@echo off
REM ============================================================
REM 05_deploy_workers.bat
REM Deploys Celery worker and Beat scheduler to ECS Fargate
REM Uses the same VPC/subnets created by 04_deploy_backend.bat
REM ============================================================

echo ============================================================
echo  Vireon AWS Deployment - Step 5: Deploy Workers (ECS Fargate)
echo ============================================================
echo.

call "%~dp0config.bat"
if %errorlevel% neq 0 exit /b 1

for /f "tokens=*" %%i in ('aws sts get-caller-identity --query "Account" --output text') do set AWS_ACCOUNT=%%i
set PREFIX=vireon-prod

for /f "tokens=*" %%i in ('aws rds describe-db-instances --db-instance-identifier %RDS_IDENTIFIER% --query "DBInstances[0].Endpoint.Address" --output text --region %AWS_REGION%') do set RDS_HOST=%%i
for /f "tokens=*" %%i in ('aws elasticache describe-cache-clusters --cache-cluster-id %REDIS_CLUSTER_ID% --show-cache-node-info --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text --region %AWS_REGION%') do set REDIS_HOST=%%i

set WORKER_IMAGE=%AWS_ACCOUNT%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_WORKER%:latest
set DATABASE_URL=postgresql+psycopg2://%DB_USER%:%DB_PASSWORD%@%RDS_HOST%:5432/%DB_NAME%
set REDIS_URL=redis://%REDIS_HOST%:6379/0

echo Worker Image : %WORKER_IMAGE%
echo RDS Host     : %RDS_HOST%
echo Redis Host   : %REDIS_HOST%
echo.

REM ── Get VPC and subnet from step 4 ──────────────────────────
for /f "tokens=*" %%i in ('aws ec2 describe-vpcs --filters "Name=tag:Name,Values=%PREFIX%-vpc" --query "Vpcs[0].VpcId" --output text --region %AWS_REGION%') do set VPC_ID=%%i
for /f "tokens=*" %%i in ('aws ec2 describe-subnets --filters "Name=tag:Name,Values=%PREFIX%-public-0" --query "Subnets[0].SubnetId" --output text --region %AWS_REGION%') do set SUBNET_PUB1=%%i
for /f "tokens=*" %%i in ('aws ec2 describe-subnets --filters "Name=tag:Name,Values=%PREFIX%-public-1" --query "Subnets[0].SubnetId" --output text --region %AWS_REGION%') do set SUBNET_PUB2=%%i

if "%VPC_ID%"=="None" (
    echo [ERROR] VPC not found. Run step 4 first.
    exit /b 1
)
echo VPC: %VPC_ID%  Subnets: %SUBNET_PUB1% %SUBNET_PUB2%

REM ── Create worker security group ────────────────────────────
echo.
echo [1/4] Creating worker security group...
for /f "tokens=*" %%i in ('aws ec2 describe-security-groups --filters "Name=group-name,Values=%PREFIX%-worker-sg" "Name=vpc-id,Values=%VPC_ID%" --query "SecurityGroups[0].GroupId" --output text --region %AWS_REGION%') do set SG_WORKER=%%i
if "%SG_WORKER%"=="None" set SG_WORKER=
if "%SG_WORKER%"=="" (
    for /f "tokens=*" %%i in ('aws ec2 create-security-group --group-name %PREFIX%-worker-sg --description "Worker ECS SG" --vpc-id %VPC_ID% --query "GroupId" --output text --region %AWS_REGION%') do set SG_WORKER=%%i
    echo [OK] Worker SG created: %SG_WORKER%
) else (
    echo [SKIP] Worker SG exists: %SG_WORKER%
)

REM ── CloudWatch Log Groups ────────────────────────────────────
echo.
echo [2/4] Creating CloudWatch log groups...
aws logs create-log-group --log-group-name /ecs/%PREFIX%/worker --region %AWS_REGION% >nul 2>&1
aws logs create-log-group --log-group-name /ecs/%PREFIX%/beat   --region %AWS_REGION% >nul 2>&1
echo [OK] Log groups ready

REM ── Register Celery Worker Task Definition ───────────────────
echo.
echo [3/4] Registering task definitions...
set WORKER_TASK=%TEMP%\vireon_worker_task.json
(
echo {
echo   "family": "%PREFIX%-worker",
echo   "networkMode": "awsvpc",
echo   "requiresCompatibilities": ["FARGATE"],
echo   "cpu": "512",
echo   "memory": "1024",
echo   "executionRoleArn": "arn:aws:iam::%AWS_ACCOUNT%:role/ecsTaskExecutionRole",
echo   "containerDefinitions": [{
echo     "name": "celery-worker",
echo     "image": "%WORKER_IMAGE%",
echo     "command": ["celery", "-A", "anomaly.celery_app", "worker", "-l", "info"],
echo     "environment": [
echo       {"name": "DATABASE_URL", "value": "%DATABASE_URL%"},
echo       {"name": "REDIS_URL",    "value": "%REDIS_URL%"},
echo       {"name": "GROQ_API_KEY", "value": "%GROQ_API_KEY%"},
echo       {"name": "COMPANY_NAME", "value": "%COMPANY_NAME%"},
echo       {"name": "S3_BUCKET",    "value": "%S3_BUCKET%"},
echo       {"name": "AWS_REGION",   "value": "%AWS_REGION%"},
echo       {"name": "ENV",          "value": "production"}
echo     ],
echo     "logConfiguration": {
echo       "logDriver": "awslogs",
echo       "options": {
echo         "awslogs-group": "/ecs/%PREFIX%/worker",
echo         "awslogs-region": "%AWS_REGION%",
echo         "awslogs-stream-prefix": "worker"
echo       }
echo     }
echo   }]
echo }
) > %WORKER_TASK%
for /f "tokens=*" %%i in ('aws ecs register-task-definition --cli-input-json file://%WORKER_TASK% --region %AWS_REGION% --query "taskDefinition.taskDefinitionArn" --output text') do set WORKER_TASK_ARN=%%i
echo [OK] Worker task: %WORKER_TASK_ARN%

set BEAT_TASK=%TEMP%\vireon_beat_task.json
(
echo {
echo   "family": "%PREFIX%-beat",
echo   "networkMode": "awsvpc",
echo   "requiresCompatibilities": ["FARGATE"],
echo   "cpu": "256",
echo   "memory": "512",
echo   "executionRoleArn": "arn:aws:iam::%AWS_ACCOUNT%:role/ecsTaskExecutionRole",
echo   "containerDefinitions": [{
echo     "name": "celery-beat",
echo     "image": "%WORKER_IMAGE%",
echo     "command": ["celery", "-A", "anomaly.celery_app", "beat", "-l", "info"],
echo     "environment": [
echo       {"name": "DATABASE_URL", "value": "%DATABASE_URL%"},
echo       {"name": "REDIS_URL",    "value": "%REDIS_URL%"},
echo       {"name": "GROQ_API_KEY", "value": "%GROQ_API_KEY%"},
echo       {"name": "COMPANY_NAME", "value": "%COMPANY_NAME%"},
echo       {"name": "ENV",          "value": "production"}
echo     ],
echo     "logConfiguration": {
echo       "logDriver": "awslogs",
echo       "options": {
echo         "awslogs-group": "/ecs/%PREFIX%/beat",
echo         "awslogs-region": "%AWS_REGION%",
echo         "awslogs-stream-prefix": "beat"
echo       }
echo     }
echo   }]
echo }
) > %BEAT_TASK%
for /f "tokens=*" %%i in ('aws ecs register-task-definition --cli-input-json file://%BEAT_TASK% --region %AWS_REGION% --query "taskDefinition.taskDefinitionArn" --output text') do set BEAT_TASK_ARN=%%i
echo [OK] Beat task: %BEAT_TASK_ARN%

REM ── Create ECS Services ──────────────────────────────────────
echo.
echo [4/4] Creating ECS worker services...
set CLUSTER=%PREFIX%-cluster
set NET_CONFIG=awsvpcConfiguration={subnets=[%SUBNET_PUB1%,%SUBNET_PUB2%],securityGroups=[%SG_WORKER%],assignPublicIp=ENABLED}

for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %CLUSTER% --services %PREFIX%-worker --region %AWS_REGION% --query "services[0].status" --output text 2^>nul') do set W_STATUS=%%i
if "%W_STATUS%"=="ACTIVE" (
    aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-worker --task-definition %WORKER_TASK_ARN% --region %AWS_REGION% >nul
    echo [OK] Worker service updated
) else (
    aws ecs create-service --cluster %CLUSTER% --service-name %PREFIX%-worker --task-definition %WORKER_TASK_ARN% --desired-count 1 --launch-type FARGATE --network-configuration "%NET_CONFIG%" --region %AWS_REGION% >nul
    echo [OK] Worker service created
)

for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %CLUSTER% --services %PREFIX%-beat --region %AWS_REGION% --query "services[0].status" --output text 2^>nul') do set B_STATUS=%%i
if "%B_STATUS%"=="ACTIVE" (
    aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-beat --task-definition %BEAT_TASK_ARN% --region %AWS_REGION% >nul
    echo [OK] Beat service updated
) else (
    aws ecs create-service --cluster %CLUSTER% --service-name %PREFIX%-beat --task-definition %BEAT_TASK_ARN% --desired-count 1 --launch-type FARGATE --network-configuration "%NET_CONFIG%" --region %AWS_REGION% >nul
    echo [OK] Beat service created
)

echo.
echo ============================================================
echo  Workers deployed to ECS cluster: %CLUSTER%
echo  Check status: AWS Console - ECS - Clusters - %CLUSTER%
echo ============================================================
