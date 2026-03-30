terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Uncomment to use S3 backend for team collaboration
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "vireon/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {}

locals {
  name   = var.project_name
  env    = var.environment
  prefix = "${local.name}-${local.env}"
  azs    = slice(data.aws_availability_zones.available.names, 0, 2)

  tags = {
    Project     = local.name
    Environment = local.env
    ManagedBy   = "terraform"
  }
}
