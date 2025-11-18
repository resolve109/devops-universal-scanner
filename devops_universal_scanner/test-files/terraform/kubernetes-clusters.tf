# WARNING: This Terraform configuration contains intentional security vulnerabilities
# DO NOT USE IN PRODUCTION!

# Multi-cloud Kubernetes clusters with security issues

# AWS EKS Cluster with vulnerabilities
resource "aws_eks_cluster" "vulnerable_cluster" {
  name     = "vulnerable-eks"
  role_arn = aws_iam_role.eks_cluster_role.arn
  version  = "1.18"  # Outdated version

  vpc_config {
    subnet_ids              = [aws_subnet.public_subnet.id]  # Public subnets only
    endpoint_private_access = false
    endpoint_public_access  = true
    public_access_cidrs     = ["0.0.0.0/0"]  # Open to internet
  }

  # No encryption at rest
  encryption_config {
    provider {
      key_arn = ""  # No encryption key
    }
    resources = []
  }

  # Logging disabled
  enabled_cluster_log_types = []

  tags = {
    Environment = "production"  # No proper tagging
  }
}

# Node group with security issues
resource "aws_eks_node_group" "vulnerable_nodes" {
  cluster_name    = aws_eks_cluster.vulnerable_cluster.name
  node_group_name = "vulnerable-nodes"
  node_role_arn   = aws_iam_role.eks_node_group_role.arn
  subnet_ids      = [aws_subnet.public_subnet.id]  # Public subnet
  instance_types  = ["t3.large"]

  # No encryption for EBS volumes
  disk_size = 50

  # Scaling configuration without limits
  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 1
  }

  # Remote access enabled with wide CIDR
  remote_access {
    ec2_ssh_key               = "my-key"
    source_security_group_ids = []
  }

  # No launch template for security hardening
}

# Azure AKS cluster with vulnerabilities
resource "azurerm_kubernetes_cluster" "vulnerable_aks" {
  name                = "vulnerable-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  dns_prefix          = "vulnerable-aks"
  kubernetes_version  = "1.19.0"  # Outdated version

  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_DS2_v2"
    
    # No network policy
    enable_auto_scaling = false
    
    # OS disk not encrypted
    os_disk_size_gb = 30
  }

  # Service principal with excessive permissions
  service_principal {
    client_id     = var.client_id
    client_secret = var.client_secret  # Secret in variables
  }

  # Network profile without proper security
  network_profile {
    network_plugin     = "azure"
    network_policy     = ""  # No network policy
    service_cidr       = "10.0.0.0/16"
    dns_service_ip     = "10.0.0.10"
    docker_bridge_cidr = "172.17.0.1/16"
  }

  # RBAC disabled
  role_based_access_control {
    enabled = false  # RBAC disabled
  }

  # No Azure AD integration
  addon_profile {
    azure_policy {
      enabled = false
    }
    
    kube_dashboard {
      enabled = true  # Dashboard enabled (deprecated)
    }
  }

  tags = {
    environment = "production"
  }
}

# Google GKE cluster with vulnerabilities
resource "google_container_cluster" "vulnerable_gke" {
  name     = "vulnerable-gke"
  location = "us-central1-a"
  
  # Remove default node pool immediately
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration with issues
  network    = "default"  # Using default network
  subnetwork = "default"  # Using default subnet

  # Master auth with username/password
  master_auth {
    username = "admin"  # Username/password auth
    password = "admin123456789"  # Weak password

    client_certificate_config {
      issue_client_certificate = true  # Client cert enabled
    }
  }

  # Logging and monitoring disabled
  logging_service    = "none"
  monitoring_service = "none"

  # Legacy authorization enabled
  enable_legacy_abac = true

  # Network policy disabled
  network_policy {
    enabled  = false
    provider = ""
  }

  # Private cluster disabled
  private_cluster_config {
    enable_private_nodes    = false
    enable_private_endpoint = false
  }

  # Master authorized networks open
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "All"
    }
  }

  # Workload identity disabled
  workload_identity_config {
    identity_namespace = ""
  }
}

# GKE node pool with vulnerabilities
resource "google_container_node_pool" "vulnerable_nodes" {
  name       = "vulnerable-node-pool"
  location   = "us-central1-a"
  cluster    = google_container_cluster.vulnerable_gke.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-medium"

    # OAuth scopes too broad
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"  # Full access
    ]

    # Service account with excessive permissions
    service_account = "default"  # Default service account

    # No disk encryption
    disk_size_gb = 100
    disk_type    = "pd-standard"

    # Image type not specified (uses default)
    # image_type = ""

    # Metadata with sensitive info
    metadata = {
      disable-legacy-endpoints = "false"  # Legacy endpoints enabled
      ssh-keys                 = "user:ssh-rsa AAAAB3NzaC1yc2E..."  # SSH key in metadata
    }

    # Tags for firewall rules (too permissive)
    tags = ["web-server", "db-server", "ssh-access"]
  }

  # Auto-upgrade disabled
  management {
    auto_repair  = false
    auto_upgrade = false
  }

  # Auto-scaling without limits
  autoscaling {
    min_node_count = 1
    max_node_count = 100  # No reasonable limit
  }
}
