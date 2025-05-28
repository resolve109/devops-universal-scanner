# Terraform variables with security issues
# This file contains variable definitions with intentional vulnerabilities

variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  # Issue: Default value hardcoded, no validation
  default     = "us-west-2"
}

variable "azure_location" {
  description = "The Azure location to deploy resources in"
  type        = string
  default     = "East US"
  # Issue: No validation on allowed values
}

variable "gcp_project_id" {
  description = "The GCP project ID"
  type        = string
  # Issue: No default value but also no validation
}

variable "gcp_region" {
  description = "The GCP region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "gcp_zone" {
  description = "The GCP zone to deploy resources in"
  type        = string
  default     = "us-central1-a"
}

# Issue: Sensitive variable not marked as sensitive
variable "database_password" {
  description = "The password for the database"
  type        = string
  # Issue: Default password is weak and hardcoded
  default     = "admin123"
  # sensitive   = true  # This should be uncommented
}

# Issue: API key stored in variable without proper protection
variable "api_key" {
  description = "API key for external services"
  type        = string
  # Issue: Default API key is fake but demonstrates the issue
  default     = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
  # sensitive   = true  # This should be uncommented
}

# Issue: JWT secret not protected
variable "jwt_secret" {
  description = "Secret key for JWT token signing"
  type        = string
  default     = "mysupersecretjwtkey123"
  # sensitive   = true  # This should be uncommented
}

# Issue: Encryption key stored in plain text
variable "encryption_key" {
  description = "Encryption key for application data"
  type        = string
  default     = "hardcodedencryptionkey32chars!"
  # sensitive   = true  # This should be uncommented
}

# Issue: Database connection string contains credentials
variable "database_connection_string" {
  description = "Database connection string"
  type        = string
  default     = "Server=tcp:server.database.windows.net,1433;Database=mydb;User ID=admin;Password=Password123!;"
  # sensitive   = true  # This should be uncommented
}

# Issue: SSH private key stored as variable
variable "ssh_private_key" {
  description = "SSH private key for instance access"
  type        = string
  default     = <<-EOF
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA7Z3QQ9Z9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9
... (fake key for demonstration)
-----END RSA PRIVATE KEY-----
EOF
  # sensitive   = true  # This should be uncommented
}

# Issue: Certificate stored in variable
variable "ssl_certificate" {
  description = "SSL certificate for HTTPS"
  type        = string
  default     = <<-EOF
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKZ9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9X9
... (fake certificate for demonstration)
-----END CERTIFICATE-----
EOF
  # sensitive   = true  # This should be uncommented
}

# Issue: Service account key stored as variable
variable "service_account_key" {
  description = "GCP service account key"
  type        = string
  default     = <<-EOF
{
  "type": "service_account",
  "project_id": "my-project",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@my-project.iam.gserviceaccount.com",
  "client_id": "1234567890",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
EOF
  # sensitive   = true  # This should be uncommented
}

# Issue: Environment variable but no validation
variable "environment" {
  description = "The deployment environment"
  type        = string
  default     = "development"
  # validation {
  #   condition     = contains(["development", "staging", "production"], var.environment)
  #   error_message = "Environment must be development, staging, or production."
  # }
}

# Issue: Instance size without validation
variable "instance_size" {
  description = "The size of the EC2 instance"
  type        = string
  default     = "t3.large"  # Issue: Default might be oversized
  # validation {
  #   condition     = contains(["t3.micro", "t3.small", "t3.medium", "t3.large"], var.instance_size)
  #   error_message = "Instance size must be a valid t3 instance type."
  # }
}

# Issue: CIDR blocks without validation
variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access resources"
  type        = list(string)
  # Issue: Default allows all traffic
  default     = ["0.0.0.0/0"]
  # validation {
  #   condition = alltrue([
  #     for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
  #   ])
  #   error_message = "All values must be valid CIDR blocks."
  # }
}

# Issue: Storage account name without validation
variable "storage_account_name" {
  description = "Name for the Azure storage account"
  type        = string
  default     = "mystorageaccount123"
  # validation {
  #   condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
  #   error_message = "Storage account name must be 3-24 characters long and contain only lowercase letters and numbers."
  # }
}

# Issue: Port numbers without validation
variable "application_port" {
  description = "Port for the application"
  type        = number
  default     = 8080
  # validation {
  #   condition     = var.application_port > 0 && var.application_port <= 65535
  #   error_message = "Port must be between 1 and 65535."
  # }
}

# Issue: Boolean variable for security feature defaulting to false
variable "enable_encryption" {
  description = "Whether to enable encryption at rest"
  type        = bool
  # Issue: Security feature disabled by default
  default     = false
}

variable "enable_monitoring" {
  description = "Whether to enable detailed monitoring"
  type        = bool
  # Issue: Monitoring disabled by default
  default     = false
}

variable "enable_backup" {
  description = "Whether to enable automated backups"
  type        = bool
  # Issue: Backups disabled by default
  default     = false
}

# Issue: Map with sensitive data
variable "application_secrets" {
  description = "Application secrets and configuration"
  type        = map(string)
  default = {
    # Issue: Secrets in default values
    "database_password" = "admin123"
    "api_key"          = "sk-1234567890abcdef"
    "jwt_secret"       = "mysupersecretkey"
    "encryption_key"   = "hardcodedkey123"
    "oauth_secret"     = "oauth-secret-123"
  }
  # sensitive = true  # This should be uncommented
}
