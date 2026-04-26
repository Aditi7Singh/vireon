# ─── Application Load Balancer ───────────────────────────────────────────────
resource "aws_lb" "main" {
  name               = "${local.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = merge(local.tags, { Name = "${local.prefix}-alb" })
}

# ─── Target Groups ───────────────────────────────────────────────────────────
resource "aws_lb_target_group" "backend" {
  name        = "${local.prefix}-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health/ready"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  tags = local.tags
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.prefix}-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    interval            = 30
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  tags = local.tags
}

# ─── HTTP Listener ────────────────────────────────────────────────────────────
# Without a cert: forward directly to frontend
# With a cert: redirect to HTTPS (handled by https listener below)
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # When no cert, forward to frontend. When cert exists, redirect to HTTPS.
  default_action {
    type = "forward"
    forward {
      target_group {
        arn = aws_lb_target_group.frontend.arn
      }
    }
  }

  tags = local.tags
}

# Override HTTP listener to redirect when HTTPS cert is provided
resource "aws_lb_listener_rule" "http_to_https_redirect" {
  count        = var.acm_certificate_arn != "" ? 1 : 0
  listener_arn = aws_lb_listener.http.arn
  priority     = 1

  action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# ─── HTTPS Listener (only when cert is provided) ──────────────────────────────
resource "aws_lb_listener" "https" {
  count             = var.acm_certificate_arn != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  tags = local.tags
}

# ─── Route /api/* and /health/* to backend ───────────────────────────────────
# On HTTP (no cert) or HTTPS (with cert)
resource "aws_lb_listener_rule" "backend_api_http" {
  count        = var.acm_certificate_arn == "" ? 1 : 0
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health/*"]
    }
  }
}

resource "aws_lb_listener_rule" "backend_api_https" {
  count        = var.acm_certificate_arn != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/health/*"]
    }
  }
}
