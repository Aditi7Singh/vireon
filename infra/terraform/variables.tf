variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "vireon"
}

variable "environment" {
  description = "Deployment environment (prod, staging)"
  type        = string
  default     = "prod"
}

# --- Networking ---
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

# --- ECR image tags (set by CI/CD) ---
variable "backend_image_tag" {
  description = "Docker image tag for the backend"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for the frontend"
  type        = string
  default     = "latest"
}

# --- RDS ---
variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "vireon"
}

variable "db_username" {
  type    = string
  default = "vireon"
}

# --- ElastiCache ---
variable "redis_node_type" {
  type    = string
  default = "cache.t3.micro"
}

# --- ECS ---
variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "worker_cpu" {
  type    = number
  default = 256
}

variable "worker_memory" {
  type    = number
  default = 512
}

# --- Domain (optional) ---
variable "domain_name" {
  description = "Your domain name (e.g. vireon.example.com). Leave empty to use ALB DNS."
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS. Required if domain_name is set."
  type        = string
  default     = ""
}

# --- Secrets (passed in via tfvars or env, never hardcoded) ---
variable "groq_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "merge_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "merge_secret_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "ollama_ssh_public_key" {
  description = "SSH public key for Ollama EC2 instance (run: ssh-keygen -t ed25519 -f ollama_key)"
  type        = string
  default     = ""
}
