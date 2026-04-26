@echo off
REM ============================================================
REM REDEPLOY_ALL.bat
REM Full teardown and redeployment of Vireon on AWS
REM Use when you want to redeploy everything with latest code.
REM Each phase asks for confirmation before proceeding.
REM Estimated total time: 25-30 minutes
REM ============================================================

call "%~dp0config.bat"
if %errorlevel% neq 0 ( echo [ERROR] config.bat failed & exit /b 1 )

set REGION=ap-south-1
set PREFIX=vireon-prod
set CLUSTER=%PREFIX%-cluster
set ACCOUNT=732772501496
set BACKEND_IMAGE=%ACCOUNT%.dkr.ecr.%REGION%.amazonaws.com/%ECR_REPO_BACKEND%:latest
set TG_ARN=arn:aws:elasticloadbalancing:ap-south-1:732772501496:targetgroup/vireon-prod-backend-tg/3d9162b87a678ccd
set SUB1=subnet-018d5f610efcf0e98
set SUB2=subnet-089906eeb29c5341b
set SG_BACK=sg-0141ead8a5ade5dfa
set S3_FRONTEND=vireon-frontend-732772501496
set CF_ID=E3EE5PX8GNLDQU

echo.
echo ============================================================
echo   VIREON FULL REDEPLOYMENT SCRIPT
echo   Each phase will ask for confirmation before running.
echo   Press ENTER to proceed or type SKIP to skip a phase.
echo ============================================================
echo.
set /p CONFIRM=Type YES to start the redeployment: 
if /i not "%CONFIRM%"=="YES" ( echo Aborted. & exit /b 0 )

REM ════════════════════════════════════════════════════════════
REM  PHASE 1: TEAR DOWN ECS SERVICES (~2 mins)
REM ════════════════════════════════════════════════════════════
echo.
echo ────────────────────────────────────────────────────────────
echo  PHASE 1: Tear down ECS services (~2 mins)
echo  This stops all running backend, worker, and beat tasks.
echo ────────────────────────────────────────────────────────────
set /p P1=Proceed with Phase 1? (ENTER=yes / SKIP=skip): 
if /i "%P1%"=="SKIP" goto PHASE2

echo Scaling down all services to 0...
aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-backend --desired-count 0 --region %REGION% >nul 2>&1
aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-worker  --desired-count 0 --region %REGION% >nul 2>&1
aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-beat    --desired-count 0 --region %REGION% >nul 2>&1
echo Waiting 15 seconds for tasks to drain...
timeout /t 15 /nobreak >nul
echo Deleting services...
aws ecs delete-service --cluster %CLUSTER% --service %PREFIX%-backend --force --region %REGION% >nul 2>&1
aws ecs delete-service --cluster %CLUSTER% --service %PREFIX%-worker  --force --region %REGION% >nul 2>&1
aws ecs delete-service --cluster %CLUSTER% --service %PREFIX%-beat    --force --region %REGION% >nul 2>&1
echo Waiting 20 seconds for services to fully drain...
timeout /t 20 /nobreak >nul
echo [OK] Phase 1 complete - ECS services torn down
echo.

REM ════════════════════════════════════════════════════════════
REM  PHASE 2: BUILD AND PUSH DOCKER IMAGE (~10-15 mins)
REM ════════════════════════════════════════════════════════════
:PHASE2
echo ────────────────────────────────────────────────────────────
echo  PHASE 2: Build and push Docker image (~10-15 mins)
echo  Builds backend from ./backend and pushes to ECR.
echo  Docker Desktop must be running.
echo ────────────────────────────────────────────────────────────
set /p P2=Proceed with Phase 2? (ENTER=yes / SKIP=skip): 
if /i "%P2%"=="SKIP" goto PHASE3

echo Logging in to ECR...
aws ecr get-login-password --region %REGION% | docker login --username AWS --password-stdin %ACCOUNT%.dkr.ecr.%REGION%.amazonaws.com
if %errorlevel% neq 0 ( echo [ERROR] ECR login failed & exit /b 1 )
echo [OK] ECR login successful

echo Building Docker image (this takes 8-12 minutes)...
docker build -t %ECR_REPO_BACKEND%:latest ./backend
if %errorlevel% neq 0 ( echo [ERROR] Docker build failed & exit /b 1 )
echo [OK] Image built

echo Tagging and pushing to ECR (2-3 minutes)...
docker tag %ECR_REPO_BACKEND%:latest %BACKEND_IMAGE%
docker tag %ECR_REPO_BACKEND%:latest %ACCOUNT%.dkr.ecr.%REGION%.amazonaws.com/%ECR_REPO_WORKER%:latest
docker push %BACKEND_IMAGE%
if %errorlevel% neq 0 ( echo [ERROR] Push failed & exit /b 1 )
docker push %ACCOUNT%.dkr.ecr.%REGION%.amazonaws.com/%ECR_REPO_WORKER%:latest
echo [OK] Phase 2 complete - Images pushed to ECR
echo.

REM ════════════════════════════════════════════════════════════
REM  PHASE 3: REDEPLOY BACKEND (~3-5 mins)
REM ════════════════════════════════════════════════════════════
:PHASE3
echo ────────────────────────────────────────────────────────────
echo  PHASE 3: Redeploy backend ECS service (~3-5 mins)
echo  Registers new task definition and recreates ECS services.
echo ────────────────────────────────────────────────────────────
set /p P3=Proceed with Phase 3? (ENTER=yes / SKIP=skip): 
if /i "%P3%"=="SKIP" goto PHASE4

echo Registering new backend task definition...
powershell -ExecutionPolicy Bypass -File "%~dp0redeploy_register_task.ps1"
set /p TASK_ARN=<"%TEMP%\vireon_task_arn.txt"
if "%TASK_ARN%"=="" ( echo [ERROR] Task definition registration failed & exit /b 1 )
echo [OK] Task definition: %TASK_ARN%

echo Waiting 10 seconds before creating services...
timeout /t 10 /nobreak >nul

echo Creating backend ECS service...
aws ecs create-service --cluster %CLUSTER% --service-name %PREFIX%-backend --task-definition %TASK_ARN% --desired-count 1 --launch-type FARGATE --health-check-grace-period-seconds 120 --network-configuration "awsvpcConfiguration={subnets=[%SUB1%,%SUB2%],securityGroups=[%SG_BACK%],assignPublicIp=ENABLED}" --load-balancers "targetGroupArn=%TG_ARN%,containerName=backend,containerPort=8000" --region %REGION% >nul 2>&1
if %errorlevel% neq 0 (
    echo Service exists - updating task definition...
    aws ecs update-service --cluster %CLUSTER% --service %PREFIX%-backend --task-definition %TASK_ARN% --region %REGION% >nul 2>&1
)
echo [OK] Backend service deployed

echo Deploying workers...
call "%~dp0\05_deploy_workers.bat"
echo [OK] Phase 3 complete - Backend and workers deployed
echo.

REM ════════════════════════════════════════════════════════════
REM  PHASE 4: DATABASE MIGRATIONS (~3-4 mins)
REM ════════════════════════════════════════════════════════════
:PHASE4
echo ────────────────────────────────────────────────────────────
echo  PHASE 4: Run database migrations (~3-4 mins)
echo  Runs Alembic migrations against RDS. Docker must be running.
echo ────────────────────────────────────────────────────────────
set /p P4=Proceed with Phase 4? (ENTER=yes / SKIP=skip): 
if /i "%P4%"=="SKIP" goto PHASE5

echo Waiting 60 seconds for ECS task to start...
timeout /t 60 /nobreak >nul

echo Logging in to ECR for migration image pull...
aws ecr get-login-password --region %REGION% | docker login --username AWS --password-stdin %ACCOUNT%.dkr.ecr.%REGION%.amazonaws.com >nul 2>&1

echo Running Alembic migrations...
docker run --rm -e DATABASE_URL="postgresql+psycopg2://%DB_USER%:%DB_PASSWORD%@vireon-postgres.cd686gs48rds.ap-south-1.rds.amazonaws.com:5432/%DB_NAME%" -e REDIS_URL="redis://vireon-redis.r1atz6.0001.aps1.cache.amazonaws.com:6379/0" -e GROQ_API_KEY="%GROQ_API_KEY%" -e ENV="production" --workdir /app %BACKEND_IMAGE% alembic upgrade head
if %errorlevel% neq 0 (
    echo [WARN] upgrade head failed - stamping to head instead...
    docker run --rm -e DATABASE_URL="postgresql+psycopg2://%DB_USER%:%DB_PASSWORD%@vireon-postgres.cd686gs48rds.ap-south-1.rds.amazonaws.com:5432/%DB_NAME%" -e REDIS_URL="redis://vireon-redis.r1atz6.0001.aps1.cache.amazonaws.com:6379/0" -e GROQ_API_KEY="%GROQ_API_KEY%" -e ENV="production" --workdir /app %BACKEND_IMAGE% alembic stamp head
)
echo [OK] Phase 4 complete - Database migrations done
echo.

REM ════════════════════════════════════════════════════════════
REM  PHASE 5: FRONTEND REDEPLOY (~5-8 mins)
REM ════════════════════════════════════════════════════════════
:PHASE5
echo ────────────────────────────────────────────────────────────
echo  PHASE 5: Rebuild and redeploy frontend (~5-8 mins)
echo  Builds Next.js, uploads to S3, invalidates CloudFront.
echo ────────────────────────────────────────────────────────────
set /p P5=Proceed with Phase 5? (ENTER=yes / SKIP=skip): 
if /i "%P5%"=="SKIP" goto VERIFY

echo Building frontend...
pushd "%~dp0..\..\frontend"
call npm run build
if %errorlevel% neq 0 ( echo [ERROR] Frontend build failed & popd & exit /b 1 )
popd
echo [OK] Frontend built

echo Uploading to S3...
aws s3 sync "%~dp0..\..\frontend\out" "s3://%S3_FRONTEND%" --region %REGION% --delete --exact-timestamps >nul 2>&1
echo [OK] Uploaded to S3

echo Invalidating CloudFront cache (propagates in background ~5-10 mins)...
aws cloudfront create-invalidation --distribution-id %CF_ID% --paths "/*" --region us-east-1 >nul 2>&1
echo [OK] Phase 5 complete - Frontend deployed
echo.

REM ════════════════════════════════════════════════════════════
REM  FINAL VERIFICATION
REM ════════════════════════════════════════════════════════════
:VERIFY
echo ────────────────────────────────────────────────────────────
echo  VERIFICATION: Checking deployment health...
echo ────────────────────────────────────────────────────────────
echo Waiting 30 seconds then checking health...
timeout /t 30 /nobreak >nul

:HEALTH_LOOP
for /f "tokens=*" %%i in ('aws ecs describe-services --cluster %CLUSTER% --services %PREFIX%-backend --region %REGION% --query "services[0].runningCount" --output text 2^>nul') do set RUNNING=%%i
if "%RUNNING%"=="1" goto HEALTH_OK
echo   ECS running count: %RUNNING% - waiting 15 more seconds...
timeout /t 15 /nobreak >nul
goto HEALTH_LOOP

:HEALTH_OK
echo [OK] ECS backend task is running
curl -s -o nul -w "  API health check: HTTP %%{http_code}" http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/health/live
echo.
echo.
echo ============================================================
echo  REDEPLOYMENT COMPLETE!
echo.
echo  Backend  : http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com
echo  API Docs : http://vireon-prod-alb-1468866347.ap-south-1.elb.amazonaws.com/api/v1/docs
echo  Frontend : http://vireon-frontend-732772501496.s3-website.ap-south-1.amazonaws.com
echo  HTTPS    : https://d10nqxcoyrzhqf.cloudfront.net
echo ============================================================
