# Google Cloud Web3 Integration - VPC Network Configuration
# This file defines VPC network infrastructure for Web3 services

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.50"
    }
  }
}

# Random ID for unique resource naming
resource "random_id" "web3_suffix" {
  byte_length = 4
}

# Custom VPC Network for Web3 Services
resource "google_compute_network" "web3_vpc" {
  name                    = "web3-vpc-${random_id.web3_suffix.hex}"
  project                 = var.project_id
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"

  description = "VPC network for Web3 integration services with enhanced security"
}

# Private Subnet for Web3 Services
resource "google_compute_subnetwork" "web3_private_subnet" {
  name          = "web3-private-subnet-${random_id.web3_suffix.hex}"
  project       = var.project_id
  network       = google_compute_network.web3_vpc.id
  region        = var.region
  ip_cidr_range = "10.0.1.0/24"

  description = "Private subnet for Web3 services with restricted internet access"

  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

# Public Subnet for Load Balancers and NAT
resource "google_compute_subnetwork" "web3_public_subnet" {
  name          = "web3-public-subnet-${random_id.web3_suffix.hex}"
  project       = var.project_id
  network       = google_compute_network.web3_vpc.id
  region        = var.region
  ip_cidr_range = "10.0.2.0/24"

  description = "Public subnet for load balancers and NAT gateways"

  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata            = "INCLUDE_ALL_METADATA"
  }
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "web3_router" {
  name    = "web3-router-${random_id.web3_suffix.hex}"
  project = var.project_id
  region  = var.region
  network = google_compute_network.web3_vpc.id

  description = "Cloud Router for NAT gateway configuration"

  bgp {
    asn = 64514
  }
}

# NAT Gateway for Private Subnet Internet Access
resource "google_compute_router_nat" "web3_nat" {
  name                               = "web3-nat-${random_id.web3_suffix.hex}"
  project                            = var.project_id
  region                             = var.region
  router                             = google_compute_router.web3_router.name
  nat_ip_allocate_option            = "AUTO_ONLY"

  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"

  subnetwork {
    name                    = google_compute_subnetwork.web3_private_subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }

  log_config {
    enable = true
    filter = "ALL"
  }

  min_ports_per_vm = 1024
  max_ports_per_vm = 65536

  tcp_established_idle_timeout_sec = 1200
  tcp_transitory_idle_timeout_sec  = 30
  udp_idle_timeout_sec            = 30
}

# Cloud NAT IP Address
resource "google_compute_address" "web3_nat_ip" {
  name         = "web3-nat-ip-${random_id.web3_suffix.hex}"
  project      = var.project_id
  region       = var.region
  address_type = "EXTERNAL"

  description = "External IP address for Web3 NAT gateway"
}

# Global Internal Load Balancer for Web3 Services
resource "google_compute_global_address" "web3_ilb_ip" {
  name         = "web3-ilb-ip-${random_id.web3_suffix.hex}"
  project      = var.project_id
  address_type = "INTERNAL"

  description = "Internal IP for Web3 services load balancer"
}

# Regional Internal Load Balancer for specific region
resource "google_compute_address" "web3_regional_ilb_ip" {
  name         = "web3-regional-ilb-ip-${random_id.web3_suffix.hex}"
  project      = var.project_id
  region       = var.region
  subnetwork   = google_compute_subnetwork.web3_private_subnet.id
  address_type = "INTERNAL"

  description = "Regional internal IP for Web3 services"
}

# Firewall Rules for VPC Network
resource "google_compute_firewall" "allow_internal_vpc" {
  name    = "allow-internal-vpc-${random_id.web3_suffix.hex}"
  network = google_compute_network.web3_vpc.id
  project = var.project_id

  description = "Allow internal communication within VPC"

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [
    google_compute_subnetwork.web3_private_subnet.ip_cidr_range,
    google_compute_subnetwork.web3_public_subnet.ip_cidr_range
  ]
}

resource "google_compute_firewall" "allow_web3_services" {
  name    = "allow-web3-services-${random_id.web3_suffix.hex}"
  network = google_compute_network.web3_vpc.id
  project = var.project_id

  description = "Allow specific ports for Web3 services"

  allow {
    protocol = "tcp"
    ports    = ["8080", "8443", "5432", "6379"]
  }

  source_ranges = [
    google_compute_subnetwork.web3_private_subnet.ip_cidr_range,
    google_compute_subnetwork.web3_public_subnet.ip_cidr_range
  ]

  target_tags = ["web3-service"]
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "allow-health-checks-${random_id.web3_suffix.hex}"
  network = google_compute_network.web3_vpc.id
  project = var.project_id

  description = "Allow Google Cloud health checks"

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8080"]
  }

  source_ranges = [
    "130.211.0.0/22",
    "35.191.0.0/16",
    "35.235.240.0/20"
  ]

  target_tags = ["web3-service", "load-balancer"]
}

resource "google_compute_firewall" "allow_iap_ssh" {
  name    = "allow-iap-ssh-${random_id.web3_suffix.hex}"
  network = google_compute_network.web3_vpc.id
  project = var.project_id

  description = "Allow SSH access through IAP"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = [
    "35.235.240.0/20" # IAP ranges
  ]

  target_tags = ["web3-service"]
}

resource "google_compute_firewall" "deny_all_egress" {
  name    = "deny-all-egress-${random_id.web3_suffix.hex}"
  network = google_compute_network.web3_vpc.id
  project = var.project_id

  description = "Deny all outbound traffic by default for security"

  deny {
    protocol = "all"
  }

  destination_ranges = ["0.0.0.0/0"]
  priority          = 65535

  target_tags = ["web3-secure"]
}

# Private Service Connect for Google APIs
resource "google_compute_global_address" "private_service_connect_ip" {
  name          = "private-service-connect-${random_id.web3_suffix.hex}"
  project       = var.project_id
  address_type  = "INTERNAL"
  purpose       = "PRIVATE_SERVICE_CONNECT"

  description = "Private Service Connect endpoint IP"
}

# DNS Policy for VPC
resource "google_dns_policy" "web3_dns_policy" {
  name       = "web3-dns-policy-${random_id.web3_suffix.hex}"
  project    = var.project_id
  enable_inbound_forwarding = true

  alternative_name_server_config {
    target_name_servers {
      ipv4_address = "8.8.8.8"
    }
    target_name_servers {
      ipv4_address = "8.8.4.4"
    }
  }

  networks {
    network_url = google_compute_network.web3_vpc.id
  }
}

# Service Account for VPC operations
resource "google_service_account" "vpc_sa" {
  account_id   = "web3-vpc-sa-${random_id.web3_suffix.hex}"
  display_name = "Web3 VPC Service Account"
  project      = var.project_id
}

# IAM Bindings for VPC Service Account
resource "google_project_iam_binding" "vpc_compute_admin" {
  project = var.project_id
  role    = "roles/compute.networkAdmin"
  members = [
    "serviceAccount:${google_service_account.vpc_sa.email}"
  ]
}

resource "google_project_iam_binding" "vpc_security_admin" {
  project = var.project_id
  role    = "roles/compute.securityAdmin"
  members = [
    "serviceAccount:${google_service_account.vpc_sa.email}"
  ]
}

# Static Routes for Custom Routing
resource "google_compute_route" "web3_internal_route" {
  name        = "web3-internal-route-${random_id.web3_suffix.hex}"
  project     = var.project_id
  network     = google_compute_network.web3_vpc.id
  dest_range  = "10.0.0.0/8"
  priority    = 100

  description = "Internal route for VPC traffic"

  next_hop_vpc_network {
    network = "default"
  }
}

# Instance Template for Web3 Compute Instances (if needed)
resource "google_compute_instance_template" "web3_template" {
  name         = "web3-instance-template-${random_id.web3_suffix.hex}"
  project      = var.project_id
  machine_type = "e2-medium"

  disk {
    source_image = "cos-cloud/cos-stable"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network    = google_compute_network.web3_vpc.id
    subnetwork = google_compute_subnetwork.web3_private_subnet.id

    access_config {
      // Ephemeral external IP for initial setup
    }
  }

  service_account {
    email  = google_service_account.vpc_sa.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    block-project-ssh-keys = "true"
    enable-oslogin         = "TRUE"
  }

  tags = ["web3-service", "web3-secure"]

  depends_on = [
    google_compute_firewall.allow_health_checks,
    google_compute_firewall.allow_web3_services
  ]
}

# Managed Instance Group (for scaling if needed)
resource "google_compute_instance_group_manager" "web3_mig" {
  name               = "web3-mig-${random_id.web3_suffix.hex}"
  project            = var.project_id
  zone               = "${var.region}-a"
  base_instance_name = "web3-instance"
  target_size        = 1

  version {
    instance_template = google_compute_instance_template.web3_template.id
  }

  named_port {
    name = "http"
    port = 8080
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.web3_health_check.id
    initial_delay_sec = 300
  }
}

# Health Check for Instance Group
resource "google_compute_health_check" "web3_health_check" {
  name                = "web3-health-check-${random_id.web3_suffix.hex}"
  project             = var.project_id
  check_interval_sec  = 5
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 2

  http_health_check {
    request_path = "/health"
    port         = 8080
  }
}

# Backend Service for Load Balancing
resource "google_compute_backend_service" "web3_backend" {
  name                    = "web3-backend-${random_id.web3_suffix.hex}"
  project                 = var.project_id
  protocol                = "HTTP"
  port_name               = "http"
  load_balancing_scheme   = "INTERNAL_MANAGED"
  timeout_sec             = 30
  enable_cdn             = false

  backend {
    group = google_compute_instance_group_manager.web3_mig.instance_group
  }

  health_checks = [google_compute_health_check.web3_health_check.id]
}

# URL Map for Load Balancer
resource "google_compute_url_map" "web3_url_map" {
  name            = "web3-url-map-${random_id.web3_suffix.hex}"
  project         = var.project_id
  default_service = google_compute_backend_service.web3_backend.id
}

# Target HTTP Proxy
resource "google_compute_target_http_proxy" "web3_http_proxy" {
  name    = "web3-http-proxy-${random_id.web3_suffix.hex}"
  project = var.project_id
  url_map = google_compute_url_map.web3_url_map.id
}

# Forwarding Rule for Load Balancer
resource "google_compute_forwarding_rule" "web3_forwarding_rule" {
  name                  = "web3-forwarding-rule-${random_id.web3_suffix.hex}"
  project               = var.project_id
  region                = var.region
  ip_address            = google_compute_address.web3_regional_ilb_ip.address
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.web3_http_proxy.id
  load_balancing_scheme = "INTERNAL_MANAGED"
  network               = google_compute_network.web3_vpc.id
  subnetwork            = google_compute_subnetwork.web3_private_subnet.id
}

# Output values
output "vpc_network" {
  description = "VPC network name"
  value       = google_compute_network.web3_vpc.name
}

output "private_subnet" {
  description = "Private subnet name"
  value       = google_compute_subnetwork.web3_private_subnet.name
}

output "public_subnet" {
  description = "Public subnet name"
  value       = google_compute_subnetwork.web3_public_subnet.name
}

output "nat_ip" {
  description = "NAT gateway external IP"
  value       = google_compute_address.web3_nat_ip.address
}

output "load_balancer_ip" {
  description = "Internal load balancer IP"
  value       = google_compute_address.web3_regional_ilb_ip.address
}

output "router_name" {
  description = "Cloud Router name"
  value       = google_compute_router.web3_router.name
}

output "instance_template" {
  description = "Instance template name"
  value       = google_compute_instance_template.web3_template.name
}