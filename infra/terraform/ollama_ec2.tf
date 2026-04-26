# ─── Ollama EC2 Instance ─────────────────────────────────────────────────────
# Uses a g4dn.xlarge (GPU) or t3.large (CPU-only, cheaper) for Ollama
# Default: t3.large (CPU) - change instance_type for GPU support

variable "ollama_instance_type" {
  type    = string
  default = "t3.large"  # swap to g4dn.xlarge for GPU
}

# Latest Amazon Linux 2023 AMI
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security group for Ollama - allow from ECS tasks only
resource "aws_security_group" "ollama" {
  name        = "${local.prefix}-ollama-sg"
  description = "Ollama EC2 - allow port 11434 from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 11434
    to_port         = 11434
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id, aws_security_group.worker.id]
  }

  # SSH from anywhere (restrict to your IP in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { Name = "${local.prefix}-ollama-sg" })
}

# Key pair for SSH access
resource "aws_key_pair" "ollama" {
  key_name   = "${local.prefix}-ollama-key"
  public_key = var.ollama_ssh_public_key
  tags       = local.tags
}

# Ollama EC2 instance in public subnet (needs internet to pull models)
resource "aws_instance" "ollama" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.ollama_instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.ollama.id]
  key_name               = aws_key_pair.ollama.key_name

  root_block_device {
    volume_size = 50  # GB - enough for 2-3 models
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Install Docker
    dnf install -y docker
    systemctl enable docker
    systemctl start docker

    # Install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh

    # Configure Ollama to listen on all interfaces
    mkdir -p /etc/systemd/system/ollama.service.d
    cat > /etc/systemd/system/ollama.service.d/override.conf <<'CONF'
    [Service]
    Environment="OLLAMA_HOST=0.0.0.0:11434"
    CONF

    systemctl daemon-reload
    systemctl enable ollama
    systemctl start ollama

    # Wait for Ollama to start then pull models
    sleep 10
    ollama pull llama3.1:8b
    ollama pull qwen2.5:14b

    echo "Ollama setup complete" >> /var/log/ollama-setup.log
  EOF

  tags = merge(local.tags, { Name = "${local.prefix}-ollama" })
}

output "ollama_private_ip" {
  description = "Ollama EC2 private IP (use this in OLLAMA_BASE_URL)"
  value       = aws_instance.ollama.private_ip
}

output "ollama_public_ip" {
  description = "Ollama EC2 public IP (for SSH access)"
  value       = aws_instance.ollama.public_ip
}
