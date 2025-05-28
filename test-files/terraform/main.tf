# Terraform main configuration with intentional security vulnerabilities
# This file demonstrates common security misconfigurations for testing

terraform {
  required_version = ">= 0.14"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# Issue: No backend configuration (state stored locally)
# terraform {
#   backend "s3" {
#     bucket = "terraform-state-bucket"
#     key    = "state"
#     region = "us-west-2"
#   }
# }

provider "aws" {
  region = var.aws_region
  # Issue: Hardcoded credentials (should use IAM roles/profiles)
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

provider "azurerm" {
  features {}
  # Issue: Hardcoded credentials
  client_id       = "12345678-1234-1234-1234-123456789012"
  client_secret   = "supersecretclientpassword"
  tenant_id       = "87654321-4321-4321-4321-210987654321"
  subscription_id = "11111111-2222-3333-4444-555555555555"
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  # Issue: Hardcoded service account key
  credentials = file("${path.module}/service-account-key.json")
}

# AWS Resources with security issues

# Issue: S3 bucket with public access
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "my-super-secret-company-data-${random_string.bucket_suffix.result}"
  
  tags = {
    Environment = "production"
    # Issue: Sensitive information in tags
    DatabasePassword = "admin123"
    ApiKey          = var.api_key
  }
}

# Issue: Bucket public access not blocked
resource "aws_s3_bucket_public_access_block" "vulnerable_bucket_pab" {
  bucket = aws_s3_bucket.vulnerable_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Issue: Bucket versioning not enabled
resource "aws_s3_bucket_versioning" "vulnerable_bucket_versioning" {
  bucket = aws_s3_bucket.vulnerable_bucket.id
  versioning_configuration {
    status = "Disabled"
  }
}

# Issue: No server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "vulnerable_bucket_encryption" {
  bucket = aws_s3_bucket.vulnerable_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"  # Issue: Not using KMS
    }
  }
}

# Issue: EC2 instance with security vulnerabilities
resource "aws_instance" "vulnerable_instance" {
  ami           = "ami-0c02fb55956c7d316"  # Issue: Hardcoded AMI ID
  instance_type = "t3.large"               # Issue: Oversized for demo

  # Issue: No key pair specified
  # key_name = aws_key_pair.main.key_name

  # Issue: Security group allows all traffic
  vpc_security_group_ids = [aws_security_group.vulnerable_sg.id]

  # Issue: Root volume not encrypted
  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = false
    delete_on_termination = true
  }

  # Issue: User data with hardcoded secrets
  user_data = base64encode(<<-EOF
              #!/bin/bash
              # Issue: Hardcoded database credentials
              export DB_PASSWORD="admin123"
              export API_KEY="sk-1234567890abcdef"
              export JWT_SECRET="mysupersecretjwtkey"
              
              # Issue: Installing without verification
              curl -fsSL https://get.docker.com -o get-docker.sh
              sh get-docker.sh
              
              # Issue: Storing secrets in files
              echo "admin123" > /etc/mysql_root_password
              chmod 644 /etc/mysql_root_password
              
              # Issue: Running services as root
              docker run -d -p 80:80 nginx
              EOF
  )

  # Issue: No IAM instance profile
  # iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  # Issue: Detailed monitoring disabled
  monitoring = false

  # Issue: Source/destination check disabled
  source_dest_check = false

  tags = {
    Name        = "vulnerable-instance"
    Environment = "production"
    # Issue: Sensitive data in tags
    AdminPassword = "admin123"
  }
}

# Issue: Overly permissive security group
resource "aws_security_group" "vulnerable_sg" {
  name_prefix = "vulnerable-sg"
  description = "Vulnerable security group for testing"

  # Issue: SSH from anywhere
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Issue: HTTP from anywhere
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Issue: All database ports open
  ingress {
    description = "Database ports"
    from_port   = 1433
    to_port     = 1433
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "MySQL"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Issue: All traffic outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "vulnerable-security-group"
  }
}

# Issue: RDS instance with security vulnerabilities
resource "aws_db_instance" "vulnerable_db" {
  identifier = "vulnerable-database"
  
  engine         = "mysql"
  engine_version = "5.7"  # Issue: Outdated version
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  
  # Issue: Hardcoded database credentials
  db_name  = "testdb"
  username = "admin"
  password = "admin123"  # Issue: Weak password in code
  
  # Issue: Public access enabled
  publicly_accessible = true
  
  # Issue: No encryption at rest
  storage_encrypted = false
  
  # Issue: Backup retention too short
  backup_retention_period = 1
  backup_window          = "03:00-04:00"
  
  # Issue: No maintenance window specified
  # maintenance_window = "sun:04:00-sun:05:00"
  
  # Issue: Deletion protection disabled
  deletion_protection = false
  
  # Issue: Skip final snapshot
  skip_final_snapshot = true
  
  # Issue: No monitoring
  monitoring_interval = 0
  
  # Issue: No enhanced monitoring
  enabled_cloudwatch_logs_exports = []
  
  tags = {
    Name = "vulnerable-database"
    # Issue: Sensitive info in tags
    MasterPassword = "admin123"
  }
}

# Azure Resources with security issues

# Issue: Resource group without proper tagging
resource "azurerm_resource_group" "vulnerable_rg" {
  name     = "vulnerable-resources"
  location = var.azure_location
  
  tags = {
    environment = "production"
    # Issue: Sensitive data in tags
    admin_password = "admin123"
  }
}

# Issue: Storage account with public access
resource "azurerm_storage_account" "vulnerable_storage" {
  name                = "vulnerablestorage${random_string.storage_suffix.result}"
  resource_group_name = azurerm_resource_group.vulnerable_rg.name
  location            = azurerm_resource_group.vulnerable_rg.location
  
  account_tier     = "Standard"
  account_replication_type = "LRS"
  
  # Issue: Public access allowed
  allow_nested_items_to_be_public = true
  
  # Issue: Secure transfer not required
  enable_https_traffic_only = false
  
  # Issue: Minimum TLS version too low
  min_tls_version = "TLS1_0"
  
  # Issue: No network rules
  # network_rules {
  #   default_action = "Deny"
  # }
  
  tags = {
    environment = "production"
    # Issue: Secrets in tags
    connection_string = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key123"
  }
}

# GCP Resources with security issues

# Issue: Compute instance with security vulnerabilities
resource "google_compute_instance" "vulnerable_vm" {
  name         = "vulnerable-vm"
  machine_type = "e2-medium"
  zone         = var.gcp_zone
  
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
      type  = "pd-standard"
      # Issue: No disk encryption with customer-managed keys
    }
  }
  
  network_interface {
    network = "default"
    # Issue: External IP assigned
    access_config {
      // Ephemeral IP
    }
  }
  
  # Issue: Using default service account
  service_account {
    email  = "default"
    scopes = ["cloud-platform"]  # Issue: Overly broad scope
  }
  
  # Issue: Metadata with sensitive information
  metadata = {
    ssh-keys = "testuser:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... testuser@example.com"
    # Issue: Startup script with secrets
    startup-script = <<-EOF
      #!/bin/bash
      export DB_PASSWORD="admin123"
      export API_KEY="sk-1234567890abcdef"
      echo "admin123" > /etc/mysql_root_password
      chmod 644 /etc/mysql_root_password
    EOF
    # Issue: OS Login disabled
    enable-oslogin = "false"
  }
  
  # Issue: No shielded VM configuration
  # shielded_instance_config {
  #   enable_secure_boot          = true
  #   enable_vtpm                 = true
  #   enable_integrity_monitoring = true
  # }
  
  tags = ["webserver", "database", "ssh-allowed"]
}

# Issue: Overly permissive firewall rule
resource "google_compute_firewall" "vulnerable_firewall" {
  name    = "vulnerable-firewall"
  network = "default"
  
  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "3306", "5432", "1433"]
  }
  
  # Issue: Source ranges too broad
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["webserver", "database"]
}

# Random strings for unique naming
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "random_string" "storage_suffix" {
  length  = 8
  special = false
  upper   = false
}
