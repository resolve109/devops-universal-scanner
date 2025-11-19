# Terraform outputs with security issues
# This file contains output definitions with intentional vulnerabilities

# Issue: Outputting sensitive data without marking as sensitive
output "database_password" {
  description = "The password for the database"
  value       = var.database_password
  # sensitive   = true  # This should be uncommented
}

output "api_key" {
  description = "API key for external services"
  value       = var.api_key
  # sensitive   = true  # This should be uncommented
}

output "jwt_secret" {
  description = "JWT secret for token signing"
  value       = var.jwt_secret
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting connection strings with embedded credentials
output "database_connection_string" {
  description = "Complete database connection string"
  value       = "Server=${aws_db_instance.vulnerable_db.endpoint};Database=${aws_db_instance.vulnerable_db.db_name};User Id=${aws_db_instance.vulnerable_db.username};Password=${aws_db_instance.vulnerable_db.password};"
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting SSH private key
output "ssh_private_key" {
  description = "SSH private key for instance access"
  value       = var.ssh_private_key
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting service account credentials
output "service_account_key" {
  description = "GCP service account key JSON"
  value       = var.service_account_key
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting SSL certificate private key
output "ssl_private_key" {
  description = "SSL certificate private key"
  value       = var.ssl_certificate
  # sensitive   = true  # This should be uncommented
}

# Infrastructure details (these might be acceptable but could be used for reconnaissance)
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.vulnerable_instance.public_ip
}

output "instance_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = aws_instance.vulnerable_instance.private_ip
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.vulnerable_db.endpoint
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.vulnerable_db.port
}

# Issue: Outputting S3 bucket name (could enable bucket enumeration)
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.vulnerable_bucket.id
}

# Issue: Outputting storage account access keys
output "storage_account_primary_key" {
  description = "Primary access key for Azure storage account"
  value       = azurerm_storage_account.vulnerable_storage.primary_access_key
  # sensitive   = true  # This should be uncommented
}

output "storage_account_secondary_key" {
  description = "Secondary access key for Azure storage account"
  value       = azurerm_storage_account.vulnerable_storage.secondary_access_key
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting complete connection string for Azure storage
output "storage_connection_string" {
  description = "Connection string for Azure storage account"
  value       = azurerm_storage_account.vulnerable_storage.primary_connection_string
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting GCP VM external IP
output "gcp_vm_external_ip" {
  description = "External IP of the GCP VM instance"
  value       = google_compute_instance.vulnerable_vm.network_interface[0].access_config[0].nat_ip
}

# Issue: Outputting SSH command with embedded key
output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i private_key.pem ubuntu@${aws_instance.vulnerable_instance.public_ip}"
}

# Issue: Outputting all application secrets
output "application_secrets" {
  description = "All application secrets and configuration"
  value       = var.application_secrets
  # sensitive   = true  # This should be uncommented
}

# Issue: Outputting admin URLs that might be sensitive
output "admin_urls" {
  description = "Administrative URLs for various services"
  value = {
    "database_admin" = "https://${aws_db_instance.vulnerable_db.endpoint}:3306/admin"
    "monitoring"     = "https://${aws_instance.vulnerable_instance.public_ip}:8080/admin"
    "api_docs"      = "https://${aws_instance.vulnerable_instance.public_ip}/api/docs"
  }
}

# Issue: Outputting security group IDs (might help in reconnaissance)
output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.vulnerable_sg.id
}

# Issue: Outputting subnet IDs and VPC information
output "vpc_info" {
  description = "VPC and networking information"
  value = {
    "vpc_id"           = aws_instance.vulnerable_instance.vpc_security_group_ids
    "availability_zone" = aws_instance.vulnerable_instance.availability_zone
    "subnet_id"        = aws_instance.vulnerable_instance.subnet_id
  }
}

# Issue: Outputting IAM role ARNs (if they existed)
# output "iam_role_arn" {
#   description = "ARN of the IAM role"
#   value       = aws_iam_role.instance_role.arn
# }

# Issue: Outputting resource IDs that could be used for attacks
output "resource_identifiers" {
  description = "Various resource identifiers"
  value = {
    "instance_id"       = aws_instance.vulnerable_instance.id
    "bucket_arn"        = aws_s3_bucket.vulnerable_bucket.arn
    "database_id"       = aws_db_instance.vulnerable_db.id
    "storage_account"   = azurerm_storage_account.vulnerable_storage.name
    "gcp_instance"      = google_compute_instance.vulnerable_vm.self_link
  }
}

# Issue: Outputting backup and snapshot information
output "backup_info" {
  description = "Backup and snapshot information"
  value = {
    "rds_backup_window"     = aws_db_instance.vulnerable_db.backup_window
    "rds_backup_retention"  = aws_db_instance.vulnerable_db.backup_retention_period
    "final_snapshot_id"     = "${aws_db_instance.vulnerable_db.identifier}-final-snapshot"
  }
}
