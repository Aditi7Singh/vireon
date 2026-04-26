# ============================================================
# 09_deploy_frontend_s3.ps1
# Deploys Next.js static export to S3 + CloudFront
# ============================================================

$ErrorActionPreference = "Stop"

$region      = "ap-south-1"
$bucketName  = "vireon-frontend-732772501496"
$frontendDir = (Resolve-Path "frontend").Path
$outDir      = "$frontendDir\out"

Write-Host "============================================================"
Write-Host " Vireon Frontend - S3 + CloudFront Deployment"
Write-Host "============================================================"
Write-Host ""

# ── Step 1: Build frontend ────────────────────────────────────
Write-Host "[1/6] Building frontend..."
Push-Location $frontendDir
$buildResult = & npm run build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host $buildResult
    Write-Error "Build failed"
    exit 1
}
Pop-Location
Write-Host "[OK] Build complete"
Write-Host ""

# ── Step 2: Create S3 bucket ──────────────────────────────────
Write-Host "[2/6] Setting up S3 bucket..."
$bucketExists = $false
try { aws s3api head-bucket --bucket $bucketName --region $region 2>$null; $bucketExists = ($LASTEXITCODE -eq 0) } catch {}
if (-not $bucketExists) {
    aws s3api create-bucket --bucket $bucketName --region $region --create-bucket-configuration LocationConstraint=$region | Out-Null
    Write-Host "[OK] Bucket created: $bucketName"
} else {
    Write-Host "[SKIP] Bucket exists: $bucketName"
}

# Enable static website hosting
$websiteConfig = '{"IndexDocument":{"Suffix":"index.html"},"ErrorDocument":{"Key":"index.html"}}'
$websiteFile = "$env:TEMP\vireon_website.json"
[System.IO.File]::WriteAllText($websiteFile, $websiteConfig, [System.Text.Encoding]::ASCII)
aws s3api put-bucket-website --bucket $bucketName --website-configuration "file://$websiteFile" --region $region | Out-Null

# Make bucket publicly readable
$policyConfig = "{`"Version`":`"2012-10-17`",`"Statement`":[{`"Sid`":`"PublicRead`",`"Effect`":`"Allow`",`"Principal`":`"*`",`"Action`":`"s3:GetObject`",`"Resource`":`"arn:aws:s3:::$bucketName/*`"}]}"
$policyFile = "$env:TEMP\vireon_s3policy.json"
[System.IO.File]::WriteAllText($policyFile, $policyConfig, [System.Text.Encoding]::ASCII)

# Disable block public access first
aws s3api put-public-access-block --bucket $bucketName --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false" --region $region | Out-Null
Start-Sleep -Seconds 3
aws s3api put-bucket-policy --bucket $bucketName --policy "file://$policyFile" --region $region | Out-Null
Write-Host "[OK] Bucket configured for static hosting"
Write-Host ""

# ── Step 3: Upload files to S3 ────────────────────────────────
Write-Host "[3/6] Uploading files to S3..."
aws s3 sync $outDir "s3://$bucketName" --region $region --delete --exact-timestamps 2>&1 | Out-Null

# Set correct content types for key file types
aws s3 cp "s3://$bucketName" "s3://$bucketName" --recursive --exclude "*" --include "*.html" --content-type "text/html" --metadata-directive REPLACE --region $region 2>&1 | Out-Null
aws s3 cp "s3://$bucketName" "s3://$bucketName" --recursive --exclude "*" --include "*.css" --content-type "text/css" --metadata-directive REPLACE --region $region 2>&1 | Out-Null
aws s3 cp "s3://$bucketName" "s3://$bucketName" --recursive --exclude "*" --include "*.js" --content-type "application/javascript" --metadata-directive REPLACE --region $region 2>&1 | Out-Null

$fileCount = (aws s3 ls "s3://$bucketName" --recursive --region $region | Measure-Object -Line).Lines
Write-Host "[OK] Uploaded $fileCount files to S3"
Write-Host ""

# ── Step 4: Create CloudFront distribution ────────────────────
Write-Host "[4/6] Setting up CloudFront distribution..."
$s3WebsiteEndpoint = "$bucketName.s3-website.$region.amazonaws.com"

# Check if distribution already exists
$existingDist = $null
try {
    $dists = (aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[0].DomainName=='$s3WebsiteEndpoint'].{Id:Id,Domain:DomainName,Status:Status}" --output json 2>$null | ConvertFrom-Json)
    if ($dists -and $dists.Count -gt 0) {
        $existingDist = $dists[0]
    }
} catch {}

if ($existingDist) {
    Write-Host "[SKIP] CloudFront distribution exists: $($existingDist.Id)"
    $cfDomain = $existingDist.Domain
    $cfId = $existingDist.Id
} else {
    $cfConfig = @"
{
  "CallerReference": "vireon-frontend-$(Get-Date -Format 'yyyyMMddHHmmss')",
  "Comment": "Vireon Frontend",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "S3-$bucketName",
      "DomainName": "$s3WebsiteEndpoint",
      "CustomOriginConfig": {
        "HTTPPort": 80,
        "HTTPSPort": 443,
        "OriginProtocolPolicy": "http-only"
      }
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-$bucketName",
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
    "Compress": true,
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    }
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [{
      "ErrorCode": 404,
      "ResponsePagePath": "/index.html",
      "ResponseCode": "200",
      "ErrorCachingMinTTL": 0
    }]
  },
  "Enabled": true,
  "HttpVersion": "http2",
  "PriceClass": "PriceClass_All"
}
"@
    $cfFile = "$env:TEMP\vireon_cf.json"
    [System.IO.File]::WriteAllText($cfFile, $cfConfig, [System.Text.Encoding]::ASCII)
    $cfResult = (aws cloudfront create-distribution --distribution-config "file://$cfFile" --output json | ConvertFrom-Json)
    $cfDomain = $cfResult.Distribution.DomainName
    $cfId = $cfResult.Distribution.Id
    Write-Host "[OK] CloudFront distribution created: $cfId"
    Write-Host "     Note: Takes 10-15 minutes to deploy globally"
}
Write-Host ""

# ── Step 5: Save CloudFront info ──────────────────────────────
Write-Host "[5/6] Saving deployment info..."
$cfInfo = "$env:TEMP\vireon_cf_info.txt"
"CF_DISTRIBUTION_ID=$cfId`nCF_DOMAIN=$cfDomain" | Set-Content $cfInfo
Write-Host "[OK] CloudFront ID: $cfId"
Write-Host ""

# ── Step 6: Done ──────────────────────────────────────────────
Write-Host "[6/6] Deployment complete!"
Write-Host ""
Write-Host "============================================================"
Write-Host " Frontend deployed!"
Write-Host " CloudFront URL : https://$cfDomain"
Write-Host " S3 Website URL : http://$s3WebsiteEndpoint"
Write-Host ""
Write-Host " NOTE: CloudFront takes 10-15 mins to fully propagate."
Write-Host " Use the S3 URL immediately for testing."
Write-Host "============================================================"
Write-Host ""
Write-Host "To redeploy after changes, run this script again."
Write-Host "To invalidate CloudFront cache after redeployment:"
Write-Host "  aws cloudfront create-invalidation --distribution-id $cfId --paths '/*' --region us-east-1"
