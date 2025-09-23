terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 4.0"
    }
  }

  backend "gcs" {
    bucket = "felicia-finance-terraform-state"
    prefix = "terraform/state"
  }
}

# Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# =============================================================================
# GOOGLE CLOUD PROJECT SETUP
# =============================================================================

# Enable required APIs
resource "google_project_service" "enabled_apis" {
  for_each = toset(var.enabled_services)

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# =============================================================================
# SERVICE ACCOUNTS
# =============================================================================

# Web3 Provider Service Account
resource "google_service_account" "web3_provider_sa" {
  account_id   = "web3-provider-sa"
  display_name = "Web3 Provider Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "web3_provider_iam" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/pubsub.publisher",
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.web3_provider_sa.email}"
}

# BigQuery Service Account
resource "google_service_account" "bigquery_service_sa" {
  account_id   = "bigquery-service-sa"
  display_name = "BigQuery Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "bigquery_service_iam" {
  for_each = toset([
    "roles/bigquery.admin",
    "roles/pubsub.subscriber",
    "roles/cloudkms.cryptoKeyEncrypterDecrypter",
    "roles/monitoring.metricWriter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.bigquery_service_sa.email}"
}

# Security Service Account
resource "google_service_account" "security_service_sa" {
  account_id   = "security-service-sa"
  display_name = "Security Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "security_service_iam" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.security_service_sa.email}"
}

# =============================================================================
# VPC NETWORK
# =============================================================================

resource "google_compute_network" "vpc" {
  name                    = "felicia-finance-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "web3_subnet" {
  name          = "web3-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  private_ip_google_access = true
}

resource "google_compute_subnetwork" "bigquery_subnet" {
  name          = "bigquery-subnet"
  ip_cidr_range = "10.0.2.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  private_ip_google_access = true
}

# =============================================================================
# FIREWALL RULES
# =============================================================================

resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8080", "8081", "5432", "6379"]
  }

  allow {
    protocol = "udp"
    ports    = ["53"]
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["felicia-finance"]
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "allow-health-checks"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["felicia-finance"]
}

# =============================================================================
# KMS KEY RING AND KEYS
# =============================================================================

resource "google_kms_key_ring" "felicia_keyring" {
  name     = "felicia-keyring"
  location = var.region
  project  = var.project_id
}

resource "google_kms_crypto_key" "web3_signing_key" {
  name     = "web3-signing-key"
  key_ring = google_kms_key_ring.felicia_keyring.id
  purpose  = "ASYMMETRIC_SIGN"

  version_template {
    algorithm = "EC_SIGN_P256_SHA256"
  }
}

resource "google_kms_crypto_key" "api_keys_key" {
  name     = "api-keys-key"
  key_ring = google_kms_key_ring.felicia_keyring.id
  purpose  = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }
}

# Grant KMS permissions to service accounts
resource "google_kms_crypto_key_iam_member" "web3_provider_kms" {
  for_each = toset([
    google_kms_crypto_key.web3_signing_key.id,
    google_kms_crypto_key.api_keys_key.id
  ])

  crypto_key_id = each.value
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.web3_provider_sa.email}"
}

resource "google_kms_crypto_key_iam_member" "bigquery_service_kms" {
  for_each = toset([
    google_kms_crypto_key.web3_signing_key.id,
    google_kms_crypto_key.api_keys_key.id
  ])

  crypto_key_id = each.value
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${google_service_account.bigquery_service_sa.email}"
}

# =============================================================================
# BIGQUERY DATASETS
# =============================================================================

resource "google_bigquery_dataset" "trading_analytics" {
  dataset_id  = "trading_analytics"
  project     = var.project_id
  location    = var.region
  description = "Trading analytics och portfolio data"

  default_table_expiration_ms = 365 * 24 * 60 * 60 * 1000  # 1 år
}

resource "google_bigquery_dataset" "portfolio_tracking" {
  dataset_id  = "portfolio_tracking"
  project     = var.project_id
  location    = var.region
  description = "Portfolio tracking och performance data"

  default_table_expiration_ms = 365 * 24 * 60 * 60 * 1000  # 1 år
}

# =============================================================================
# PUB/SUB TOPICS
# =============================================================================

resource "google_pubsub_topic" "crypto_trades" {
  name    = "crypto-trades"
  project = var.project_id

  message_retention_duration = "604800s"  # 7 dagar
}

resource "google_pubsub_topic" "price_updates" {
  name    = "price-updates"
  project = var.project_id

  message_retention_duration = "86400s"  # 1 dag
}

resource "google_pubsub_topic" "trading_alerts" {
  name    = "trading-alerts"
  project = var.project_id

  message_retention_duration = "2592000s"  # 30 dagar
}

# =============================================================================
# PUB/SUB SUBSCRIPTIONS
# =============================================================================

resource "google_pubsub_subscription" "crypto_trades_processor" {
  name    = "crypto-trades-processor"
  topic   = google_pubsub_topic.crypto_trades.name
  project = var.project_id

  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
}

resource "google_pubsub_subscription" "price_updates_processor" {
  name    = "price-updates-processor"
  topic   = google_pubsub_topic.price_updates.name
  project = var.project_id

  ack_deadline_seconds       = 30
  message_retention_duration = "86400s"
}

# =============================================================================
# CLOUD STORAGE BUCKETS
# =============================================================================

resource "google_storage_bucket" "web3_data" {
  name          = "${var.project_id}-web3-data"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket" "ml_models" {
  name          = "${var.project_id}-ml-models"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true
}

resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-backups"
  location      = var.region
  project       = var.project_id
  storage_class = "NEARLINE"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# =============================================================================
# CLOUD RUN SERVICES
# =============================================================================

# Web3 Provider Service
resource "google_cloud_run_service" "web3_provider" {
  name     = "web3-provider"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/ingress"       = "all"
      "run.googleapis.com/ingress-status" = "all"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.web3_provider_sa.email

      containers {
        image = "gcr.io/${var.project_id}/web3-provider:latest"

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "2048Mi"
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "WEB3_GATEWAY_ENABLED"
          value = "true"
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.enabled_apis]
}

# BigQuery Service
resource "google_cloud_run_service" "bigquery_service" {
  name     = "bigquery-service"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/ingress"       = "all"
      "run.googleapis.com/ingress-status" = "all"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.bigquery_service_sa.email

      containers {
        image = "gcr.io/${var.project_id}/bigquery-service:latest"

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2000m"
            memory = "4096Mi"
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "BIGQUERY_DATASET_TRADING"
          value = "trading_analytics"
        }

        env {
          name  = "BIGQUERY_DATASET_PORTFOLIO"
          value = "portfolio_tracking"
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "5"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.enabled_apis]
}

# Security Service
resource "google_cloud_run_service" "security_service" {
  name     = "security-service"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/ingress"       = "internal"
      "run.googleapis.com/ingress-status" = "all"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.security_service_sa.email

      containers {
        image = "gcr.io/${var.project_id}/security-service:latest"

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "500m"
            memory = "1024Mi"
          }
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "3"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.enabled_apis]
}

# =============================================================================
# LOAD BALANCER
# =============================================================================

resource "google_compute_region_network_endpoint_group" "web3_provider_neg" {
  name                  = "web3-provider-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = google_cloud_run_service.web3_provider.name
  }
}

resource "google_compute_region_network_endpoint_group" "bigquery_service_neg" {
  name                  = "bigquery-service-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = google_cloud_run_service.bigquery_service.name
  }
}

resource "google_compute_backend_service" "web3_provider_backend" {
  name      = "web3-provider-backend"
  project   = var.project_id
  protocol  = "HTTP"

  timeout_sec = 30

  backend {
    group = google_compute_region_network_endpoint_group.web3_provider_neg.id
  }
}

resource "google_compute_backend_service" "bigquery_service_backend" {
  name      = "bigquery-service-backend"
  project   = var.project_id
  protocol  = "HTTP"

  timeout_sec = 60

  backend {
    group = google_compute_region_network_endpoint_group.bigquery_service_neg.id
  }
}

resource "google_compute_url_map" "felicia_finance_lb" {
  name            = "felicia-finance-lb"
  project         = var.project_id
  default_service = google_compute_backend_service.web3_provider_backend.id

  host_rule {
    hosts        = ["api.felicia-finance.com"]
    path_matcher = "felicia-finance-paths"
  }

  path_matcher {
    name            = "felicia-finance-paths"
    default_service = google_compute_backend_service.web3_provider_backend.id

    path_rule {
      paths   = ["/api/v1/portfolio/*", "/api/v1/analysis/*"]
      service = google_compute_backend_service.bigquery_service_backend.id
    }

    path_rule {
      paths   = ["/api/v1/web3/*", "/api/v1/tokens/*"]
      service = google_compute_backend_service.web3_provider_backend.id
    }
  }
}

resource "google_compute_target_http_proxy" "felicia_finance_http_proxy" {
  name    = "felicia-finance-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.felicia_finance_lb.id
}

resource "google_compute_global_forwarding_rule" "felicia_finance_forwarding_rule" {
  name       = "felicia-finance-forwarding-rule"
  project    = var.project_id
  target     = google_compute_target_http_proxy.felicia_finance_http_proxy.id
  port_range = "80"
  ip_protocol = "TCP"
}

# =============================================================================
# MONITORING & ALERTING
# =============================================================================

resource "google_monitoring_dashboard" "felicia_finance_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Felicia Finance Main Dashboard"
    gridLayout = {
      columns = 2
      widgets = [
        {
          title = "Web3 Provider CPU Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"web3-provider\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    crossSeriesReducer = "REDUCE_MEAN"
                  }
                }
              }
            }]
            chartType = "LINE"
          }
        },
        {
          title = "BigQuery Service Memory Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/container/memory/utilizations\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"bigquery-service\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_MEAN"
                    crossSeriesReducer = "REDUCE_MEAN"
                  }
                }
              }
            }]
            chartType = "LINE"
          }
        },
        {
          title = "Error Rate by Service"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request_count\" resource.type=\"cloud_run_revision\" metric.label.state=\"error\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_SUM"
                  }
                }
              }
            }]
            chartType = "LINE"
          }
        },
        {
          title = "Request Latency"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request_latencies\" resource.type=\"cloud_run_revision\""
                  aggregation = {
                    perSeriesAligner = "ALIGN_PERCENTILE_99"
                    crossSeriesReducer = "REDUCE_PERCENTILE_99"
                  }
                }
              }
            }]
            chartType = "LINE"
          }
        }
      ]
    }
  })

  project = var.project_id
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "web3_provider_url" {
  description = "Web3 Provider service URL"
  value       = google_cloud_run_service.web3_provider.status[0].url
}

output "bigquery_service_url" {
  description = "BigQuery service URL"
  value       = google_cloud_run_service.bigquery_service.status[0].url
}

output "security_service_url" {
  description = "Security service URL"
  value       = google_cloud_run_service.security_service.status[0].url
}

output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address
}

output "project_id" {
  description = "Google Cloud project ID"
  value       = var.project_id
}

output "kms_keyring_name" {
  description = "KMS keyring name"
  value       = google_kms_key_ring.felicia_keyring.name
}

output "bigquery_dataset_trading" {
  description = "Trading analytics BigQuery dataset"
  value       = google_bigquery_dataset.trading_analytics.dataset_id
}

output "bigquery_dataset_portfolio" {
  description = "Portfolio tracking BigQuery dataset"
  value       = google_bigquery_dataset.portfolio_tracking.dataset_id
}