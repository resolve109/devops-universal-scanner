# Terraform provider configuration with security issues
# This file demonstrates provider-level security misconfigurations

terraform {
  required_version = ">= 1.0"
  
  # Issue: No required provider versions specified
  required_providers {
    aws = {
      source = "hashicorp/aws"
      # version = "~> 5.0"  # Should specify version constraints
    }
    azurerm = {
      source = "hashicorp/azurerm"
      # version = "~> 3.0"  # Should specify version constraints
    }
    google = {
      source = "hashicorp/google"
      # version = "~> 4.0"  # Should specify version constraints
    }
    random = {
      source = "hashicorp/random"
      # version = "~> 3.0"  # Should specify version constraints
    }
  }
  
  # Issue: No backend configuration - state stored locally
  # backend "s3" {
  #   bucket         = "my-terraform-state-bucket"
  #   key            = "state/terraform.tfstate"
  #   region         = "us-west-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# AWS Provider with security issues
provider "aws" {
  region = var.aws_region
  
  # Issue: Hardcoded credentials (should use IAM roles/profiles)
  # access_key = "AKIAIOSFODNN7EXAMPLE"
  # secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  
  # Issue: No assume role configuration
  # assume_role {
  #   role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
  #   session_name = "terraform-session"
  # }
  
  # Issue: No default tags
  # default_tags {
  #   tags = {
  #     Environment   = var.environment
  #     Project       = "devops-scanner"
  #     ManagedBy     = "terraform"
  #     Owner         = "devops-team"
  #   }
  # }
}

# Azure Provider with security issues
provider "azurerm" {
  features {
    # Issue: Key vault purge protection disabled
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    
    # Issue: Resource group deletion protection disabled
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
    
    # Issue: Storage account blob deletion protection disabled
    storage {
      purge_soft_delete_on_destroy = true
    }
  }
  
  # Issue: Hardcoded credentials
  # client_id       = "12345678-1234-1234-1234-123456789012"
  # client_secret   = "supersecretclientpassword"
  # tenant_id       = "87654321-4321-4321-4321-210987654321"
  # subscription_id = "11111111-2222-3333-4444-555555555555"
  
  # Issue: No partner ID for tracking
  # partner_id = "your-partner-id"
}

# Google Cloud Provider with security issues
provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
  
  # Issue: Hardcoded service account key file
  # credentials = file("${path.module}/service-account-key.json")
  
  # Issue: No billing project specified
  # billing_project = var.gcp_project_id
  
  # Issue: No user project override
  # user_project_override = true
  
  # Issue: No request timeout configured
  # request_timeout = "60s"
}

# Local values with potential security issues
locals {
  # Issue: Sensitive data in locals
  common_tags = {
    Environment   = var.environment
    Project       = "devops-scanner"
    ManagedBy     = "terraform"
    Owner         = "devops-team"
    # Issue: Sensitive information in tags
    AdminContact  = "admin@company.com"
    BudgetCode    = "BUDGET-12345"
    CostCenter    = "CC-9999"
  }
  
  # Issue: Hardcoded sensitive values
  database_config = {
    username = "admin"
    password = "admin123"  # Should use random_password or external source
    port     = 3306
    database = "application_db"
  }
  
  # Issue: Predictable naming patterns
  resource_prefix = "${var.environment}-${var.gcp_project_id}"
  
  # Issue: Common ports exposed
  allowed_ports = [22, 80, 443, 3306, 5432, 1433, 6379, 27017]
  
  # Issue: Overly permissive CIDR blocks
  trusted_networks = [
    "0.0.0.0/0",      # Issue: Allows all traffic
    "10.0.0.0/8",     # Issue: Entire private network
    "172.16.0.0/12",  # Issue: Entire private network
    "192.168.0.0/16"  # Issue: Entire private network
  ]
}
