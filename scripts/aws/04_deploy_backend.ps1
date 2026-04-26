# ============================================================
# 04_deploy_backend.ps1
# Deploys FastAPI backend to ECS Fargate with an ALB
# Run: scripts\aws\04_deploy_backend.bat
# ============================================================

$ErrorActionPreference = "Stop"

# ── Config ────────────────────────────────────────────────────
$region         = "ap-south-1"
$prefix         = "vireon-prod"
$rdsId          = "vireon-postgres"
$redisId        = "vireon-redis"
$ecrBackend     = "vireon-backend"
$dbUser         = "vireon"
$dbPassword     = "vireon_yagna_project"
$dbName         = "vireon"
$secretKey      = "vireon-prod-secret-key-2026-seedlinglabs-ap-south-1"
$mergeKey       = "sNtk4aFWUGxqtiuLivhhP8F59OtpLZT-ZzjSN-IA9lozfcjKD-DYx"
$s3Bucket       = "vireon-documents-732772501496"
$companyName    = "SeedlingLabs"
$allowedOrigins = "https://main.d1tzlh2fec7rai.amplifyapp.com"

# Read GROQ key from config.bat
$groqKey = (Get-Content "$PSScriptRoot\config.bat" | Where-Object { $_ -match "^set GROQ_API_KEY=" } | ForEach-Object { ($_ -split "=", 2)[1].Trim() })

Write-Host "============================================================"
Write-Host " Vireon AWS Deployment - Step 4: Deploy Backend (ECS Fargate)"
Write-Host "============================================================"
Write-Host ""

$account = (aws sts get-caller-identity --query Account --output text)
$image   = "$account.dkr.ecr.$region.amazonaws.com/${ecrBackend}:latest"

Write-Host "Account : $account"
Write-Host "Region  : $region"
Write-Host "Image   : $image"
Write-Host ""

# ── Get endpoints ─────────────────────────────────────────────
Write-Host "Fetching RDS endpoint..."
$rdsHost = (aws rds describe-db-instances --db-instance-identifier $rdsId --query "DBInstances[0].Endpoint.Address" --output text --region $region)
if (-not $rdsHost -or $rdsHost -eq "None") { Write-Error "RDS not found. Run step 3 first."; exit 1 }
Write-Host "[OK] RDS: $rdsHost"

Write-Host "Fetching Redis endpoint..."
$redisHost = (aws elasticache describe-cache-clusters --cache-cluster-id $redisId --show-cache-node-info --query "CacheClusters[0].CacheNodes[0].Endpoint.Address" --output text --region $region)
if (-not $redisHost -or $redisHost -eq "None") { Write-Error "ElastiCache not found. Run step 3 first."; exit 1 }
Write-Host "[OK] Redis: $redisHost"

$dbUrl    = "postgresql+psycopg2://${dbUser}:${dbPassword}@${rdsHost}:5432/${dbName}"
$redisUrl = "redis://${redisHost}:6379/0"
Write-Host ""

# ── 1. VPC ────────────────────────────────────────────────────
Write-Host "[1/9] VPC..."
$vpcId = (aws ec2 describe-vpcs --filters "Name=tag:Name,Values=$prefix-vpc" --query "Vpcs[0].VpcId" --output text --region $region)
if ($vpcId -eq "None" -or -not $vpcId) {
    $vpcId = (aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query "Vpc.VpcId" --output text --region $region)
    aws ec2 modify-vpc-attribute --vpc-id $vpcId --enable-dns-hostnames --region $region | Out-Null
    aws ec2 modify-vpc-attribute --vpc-id $vpcId --enable-dns-support --region $region | Out-Null
    aws ec2 create-tags --resources $vpcId --tags Key=Name,Value="$prefix-vpc" Key=Project,Value=vireon --region $region | Out-Null
    Write-Host "[OK] VPC created: $vpcId"
} else { Write-Host "[SKIP] VPC exists: $vpcId" }

# ── 2. Subnets ────────────────────────────────────────────────
Write-Host "[2/9] Subnets..."
$azs = (aws ec2 describe-availability-zones --region $region --query "AvailabilityZones[*].ZoneName" --output text).Split()
$az1 = $azs[0]; $az2 = $azs[1]

$sub1 = (aws ec2 describe-subnets --filters "Name=tag:Name,Values=$prefix-public-0" --query "Subnets[0].SubnetId" --output text --region $region)
if ($sub1 -eq "None" -or -not $sub1) {
    $sub1 = (aws ec2 create-subnet --vpc-id $vpcId --cidr-block 10.0.0.0/24 --availability-zone $az1 --query "Subnet.SubnetId" --output text --region $region)
    aws ec2 create-tags --resources $sub1 --tags Key=Name,Value="$prefix-public-0" --region $region | Out-Null
    aws ec2 modify-subnet-attribute --subnet-id $sub1 --map-public-ip-on-launch --region $region | Out-Null
}
$sub2 = (aws ec2 describe-subnets --filters "Name=tag:Name,Values=$prefix-public-1" --query "Subnets[0].SubnetId" --output text --region $region)
if ($sub2 -eq "None" -or -not $sub2) {
    $sub2 = (aws ec2 create-subnet --vpc-id $vpcId --cidr-block 10.0.1.0/24 --availability-zone $az2 --query "Subnet.SubnetId" --output text --region $region)
    aws ec2 create-tags --resources $sub2 --tags Key=Name,Value="$prefix-public-1" --region $region | Out-Null
    aws ec2 modify-subnet-attribute --subnet-id $sub2 --map-public-ip-on-launch --region $region | Out-Null
}
Write-Host "[OK] Subnets: $sub1  $sub2"

# ── 3. Internet Gateway ───────────────────────────────────────
Write-Host "[3/9] Internet Gateway..."
$igwId = (aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$vpcId" --query "InternetGateways[0].InternetGatewayId" --output text --region $region)
if ($igwId -eq "None" -or -not $igwId) {
    $igwId = (aws ec2 create-internet-gateway --query "InternetGateway.InternetGatewayId" --output text --region $region)
    aws ec2 attach-internet-gateway --internet-gateway-id $igwId --vpc-id $vpcId --region $region | Out-Null
    Write-Host "[OK] IGW created: $igwId"
} else { Write-Host "[SKIP] IGW exists: $igwId" }

$rtId = (aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$vpcId" "Name=tag:Name,Values=$prefix-public-rt" --query "RouteTables[0].RouteTableId" --output text --region $region)
if ($rtId -eq "None" -or -not $rtId) {
    $rtId = (aws ec2 create-route-table --vpc-id $vpcId --query "RouteTable.RouteTableId" --output text --region $region)
    aws ec2 create-tags --resources $rtId --tags Key=Name,Value="$prefix-public-rt" --region $region | Out-Null
    aws ec2 create-route --route-table-id $rtId --destination-cidr-block 0.0.0.0/0 --gateway-id $igwId --region $region | Out-Null
    aws ec2 associate-route-table --route-table-id $rtId --subnet-id $sub1 --region $region | Out-Null
    aws ec2 associate-route-table --route-table-id $rtId --subnet-id $sub2 --region $region | Out-Null
}

# ── 4. Security Groups ────────────────────────────────────────
Write-Host "[4/9] Security Groups..."
$sgAlb = (aws ec2 describe-security-groups --filters "Name=group-name,Values=$prefix-alb-sg" "Name=vpc-id,Values=$vpcId" --query "SecurityGroups[0].GroupId" --output text --region $region)
if ($sgAlb -eq "None" -or -not $sgAlb) {
    $sgAlb = (aws ec2 create-security-group --group-name "$prefix-alb-sg" --description "ALB SG" --vpc-id $vpcId --query "GroupId" --output text --region $region)
    aws ec2 authorize-security-group-ingress --group-id $sgAlb --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $region | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $sgAlb --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $region | Out-Null
}
$sgBack = (aws ec2 describe-security-groups --filters "Name=group-name,Values=$prefix-backend-sg" "Name=vpc-id,Values=$vpcId" --query "SecurityGroups[0].GroupId" --output text --region $region)
if ($sgBack -eq "None" -or -not $sgBack) {
    $sgBack = (aws ec2 create-security-group --group-name "$prefix-backend-sg" --description "Backend ECS SG" --vpc-id $vpcId --query "GroupId" --output text --region $region)
    aws ec2 authorize-security-group-ingress --group-id $sgBack --protocol tcp --port 8000 --source-group $sgAlb --region $region | Out-Null
}
Write-Host "[OK] SG ALB=$sgAlb  Backend=$sgBack"

# ── 5. IAM Role ───────────────────────────────────────────────
Write-Host "[5/9] IAM Role..."
$roleCheck = $null
try { $roleCheck = (aws iam get-role --role-name ecsTaskExecutionRole --query "Role.RoleName" --output text 2>$null) } catch {}
if ($roleCheck -ne "ecsTaskExecutionRole") {
    $trustFile = "$env:TEMP/vireon_trust.json"
    [System.IO.File]::WriteAllText($trustFile, '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}', [System.Text.Encoding]::ASCII)
    aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document "file://$trustFile" | Out-Null
    aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy | Out-Null
    aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly | Out-Null
    Write-Host "[OK] IAM role created"
} else { Write-Host "[SKIP] IAM role exists" }

# ── 6. ECS Cluster ────────────────────────────────────────────
Write-Host "[6/9] ECS Cluster..."
aws ecs create-cluster --cluster-name "$prefix-cluster" --region $region 2>$null | Out-Null
try { aws logs create-log-group --log-group-name "/ecs/$prefix/backend" --region $region 2>$null | Out-Null } catch {}
Write-Host "[OK] ECS cluster ready"

# ── 7. ALB + Target Group ─────────────────────────────────────
Write-Host "[7/9] ALB + Target Group..."
$albArn = $null
try { $albArn = (aws elbv2 describe-load-balancers --names "$prefix-alb" --query "LoadBalancers[0].LoadBalancerArn" --output text --region $region 2>$null) } catch {}
if ($albArn -eq "None" -or -not $albArn) {
    $albArn = (aws elbv2 create-load-balancer --name "$prefix-alb" --subnets $sub1 $sub2 --security-groups $sgAlb --scheme internet-facing --type application --region $region --query "LoadBalancers[0].LoadBalancerArn" --output text)
    Write-Host "[OK] ALB created"
} else { Write-Host "[SKIP] ALB exists" }
$albDns = (aws elbv2 describe-load-balancers --load-balancer-arns $albArn --query "LoadBalancers[0].DNSName" --output text --region $region)

$tgArn = $null
try { $tgArn = (aws elbv2 describe-target-groups --names "$prefix-backend-tg" --query "TargetGroups[0].TargetGroupArn" --output text --region $region 2>$null) } catch {}
if ($tgArn -eq "None" -or -not $tgArn) {
    $tgArn = (aws elbv2 create-target-group --name "$prefix-backend-tg" --protocol HTTP --port 8000 --vpc-id $vpcId --target-type ip --health-check-path /health/ready --health-check-interval-seconds 30 --healthy-threshold-count 2 --unhealthy-threshold-count 3 --query "TargetGroups[0].TargetGroupArn" --output text --region $region)
    Write-Host "[OK] Target group created"
} else { Write-Host "[SKIP] Target group exists" }

$listenerArn = $null
try { $listenerArn = (aws elbv2 describe-listeners --load-balancer-arn $albArn --query "Listeners[0].ListenerArn" --output text --region $region 2>$null) } catch {}
if ($listenerArn -eq "None" -or -not $listenerArn) {
    aws elbv2 create-listener --load-balancer-arn $albArn --protocol HTTP --port 80 --default-actions "Type=forward,TargetGroupArn=$tgArn" --region $region | Out-Null
    Write-Host "[OK] Listener created"
}
Write-Host "[OK] ALB DNS: $albDns"

# ── 8. ECS Task Definition ────────────────────────────────────
Write-Host "[8/9] ECS Task Definition..."
$taskFile = "$env:TEMP/vireon_task.json"
$taskJson = @"
{
  "family": "$prefix-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${account}:role/ecsTaskExecutionRole",
  "containerDefinitions": [{
    "name": "backend",
    "image": "$image",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "command": ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"],
    "environment": [
      {"name": "DATABASE_URL",    "value": "$dbUrl"},
      {"name": "REDIS_URL",       "value": "$redisUrl"},
      {"name": "GROQ_API_KEY",    "value": "$groqKey"},
      {"name": "SECRET_KEY",      "value": "$secretKey"},
      {"name": "COMPANY_NAME",    "value": "$companyName"},
      {"name": "S3_BUCKET",       "value": "$s3Bucket"},
      {"name": "AWS_REGION",      "value": "$region"},
      {"name": "ALLOWED_ORIGINS", "value": "$allowedOrigins"},
      {"name": "MERGE_API_KEY",   "value": "$mergeKey"},
      {"name": "ENV",             "value": "production"},
      {"name": "SANDBOX_MODE",    "value": "false"},
      {"name": "STRICT_STARTUP_CHECKS",       "value": "false"},
      {"name": "REQUIRE_REDIS_FOR_READINESS", "value": "false"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group":         "/ecs/$prefix/backend",
        "awslogs-region":        "$region",
        "awslogs-stream-prefix": "backend"
      }
    }
  }]
}
"@
[System.IO.File]::WriteAllText($taskFile, $taskJson, [System.Text.Encoding]::ASCII)
$taskArn = (aws ecs register-task-definition --cli-input-json "file://$taskFile" --region $region --query "taskDefinition.taskDefinitionArn" --output text)
if (-not $taskArn -or $taskArn -eq "None") { Write-Error "Task definition registration failed"; exit 1 }
Write-Host "[OK] Task: $taskArn"

# ── 9. ECS Service ────────────────────────────────────────────
Write-Host "[9/9] ECS Service..."
$svcStatus = $null
try { $svcStatus = (aws ecs describe-services --cluster "$prefix-cluster" --services "$prefix-backend" --region $region --query "services[0].status" --output text 2>$null) } catch {}
if ($svcStatus -eq "ACTIVE") {
    aws ecs update-service --cluster "$prefix-cluster" --service "$prefix-backend" --task-definition $taskArn --region $region | Out-Null
    Write-Host "[OK] Service updated"
} else {
    aws ecs create-service --cluster "$prefix-cluster" --service-name "$prefix-backend" --task-definition $taskArn --desired-count 1 --launch-type FARGATE --network-configuration "awsvpcConfiguration={subnets=[$sub1,$sub2],securityGroups=[$sgBack],assignPublicIp=ENABLED}" --load-balancers "targetGroupArn=$tgArn,containerName=backend,containerPort=8000" --region $region | Out-Null
    Write-Host "[OK] Service created"
}

Write-Host ""
Write-Host "============================================================"
Write-Host " Backend deployment complete!"
Write-Host " API URL : http://$albDns"
Write-Host " Health  : http://$albDns/health/live"
Write-Host " API Docs: http://$albDns/api/v1/docs"
Write-Host " Note: Takes ~3 minutes for the task to start"
Write-Host "============================================================"
