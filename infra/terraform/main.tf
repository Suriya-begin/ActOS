# ActOS — AWS Infrastructure (Phase 5)
# Blueprint: EC2 + S3 + RDS + CloudFront + Lambda

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── VPC ──────────────────────────────────────────────────────
resource "aws_vpc" "actos_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "actos-vpc" }
}

# ── EC2 (FastAPI Backend) ────────────────────────────────────
resource "aws_instance" "actos_backend" {
  ami           = "ami-0f5ee92e2d63afc18"   # Ubuntu 22.04 ap-south-1
  instance_type = "t3.medium"
  tags = { Name = "actos-backend" }

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io docker-compose
    systemctl start docker
    cd /home/ubuntu
    git clone https://github.com/your-username/actos.git
    cd actos && docker-compose up -d
  EOF
}

# ── S3 (Audio files, assets) ─────────────────────────────────
resource "aws_s3_bucket" "actos_assets" {
  bucket = "actos-assets-${var.environment}"
  tags   = { Name = "actos-assets" }
}

resource "aws_s3_bucket_versioning" "assets_versioning" {
  bucket = aws_s3_bucket.actos_assets.id
  versioning_configuration { status = "Enabled" }
}

# ── RDS PostgreSQL ───────────────────────────────────────────
resource "aws_db_instance" "actos_postgres" {
  identifier        = "actos-postgres"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  db_name           = "actos_db"
  username          = "actos_user"
  password          = var.db_password
  skip_final_snapshot = true
  tags = { Name = "actos-rds" }
}

# ── CLOUDFRONT (Frontend CDN) ────────────────────────────────
resource "aws_cloudfront_distribution" "actos_cdn" {
  enabled = true
  origin {
    domain_name = aws_s3_bucket.actos_assets.bucket_regional_domain_name
    origin_id   = "actos-s3"
  }
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "actos-s3"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }
  restrictions {
    geo_restriction { restriction_type = "none" }
  }
  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
