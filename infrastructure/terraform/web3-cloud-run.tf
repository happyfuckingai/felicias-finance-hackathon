# Google Cloud Web3 Integration - Cloud Run Services
# This file defines Cloud Run services for all Web3 components

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

# KMS Key Ring for Web3 Services
resource "google_kms_key_ring" "web3_keyring" {
  name     = "web3-keyring-${random_id.web3_suffix.hex}"
  location = var.region
  project  = var.project_id
}

# KMS Key for encryption at rest
resource "google_kms_crypto_key" "web3_encryption_key" {
  name            = "web3-encryption-key"
  key_ring        = google_kms_key_ring.web3_keyring.id
  rotation_period = "7776000s" # 90 days
  purpose         = "ENCRYPT_DECRYPT"

  lifecycle {
    prevent_destroy = true
  }
}

# Service Account for Web3 Provider Service
resource "google_service_account" "web3_provider_sa" {
  account_id   = "web3-provider-sa-${random_id.web3_suffix.hex}"
  display_name = "Web3 Provider Service Account"
  project      = var.project_id
}

# Service Account for BigQuery Service
resource "google_service_account" "bigquery_service_sa" {
  account_id   = "bigquery-service-sa-${random_id.web3_suffix.hex}"
  display_name = "BigQuery Analytics Service Account"
  project      = var.project_id
}

# Service Account for Web3 Security Service
resource "google_service_account" "web3_security_sa" {
  account_id   = "web3-security-sa-${random_id.web3_suffix.hex}"
  display_name = "Web3 Security Service Account"
  project      = var.project_id
}

# IAM Bindings for Service Accounts
resource "google_project_iam_binding" "web3_provider_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  members = [
    "serviceAccount:${google_service_account.web3_provider_sa.email}"
  ]
}

resource "google_project_iam_binding" "bigquery_service_bigquery" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  members = [
    "serviceAccount:${google_service_account.bigquery_service_sa.email}"
  ]
}

resource "google_project_iam_binding" "web3_security_firewall" {
  project = var.project_id
  role    = "roles/compute.securityAdmin"
  members = [
    "serviceAccount:${google_service_account.web3_security_sa.email}"
  ]
}

# BigQuery Dataset for Web3 Analytics
resource "google_bigquery_dataset" "web3_analytics" {
  dataset_id    = "web3_analytics_${random_id.web3_suffix.hex}"
  project       = var.project_id
  location      = var.region
  friendly_name = "Web3 Analytics Dataset"

  default_table_expiration_ms = 63072000000 # 2 years
  default_partition_expiration_ms = 63072000000 # 2 years

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.web3_encryption_key.id
  }

  access {
    role          = "OWNER"
    user_by_email = google_service_account.bigquery_service_sa.email
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.web3_provider_sa.email
  }
}

# BigQuery Tables
resource "google_bigquery_table" "blockchain_transactions" {
  dataset_id = google_bigquery_dataset.web3_analytics.dataset_id
  table_id   = "blockchain_transactions"
  project    = var.project_id

  schema = file("${path.module}/schemas/blockchain_transactions.json")

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["chain_id", "token_address"]

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.web3_encryption_key.id
  }
}

resource "google_bigquery_table" "token_analytics" {
  dataset_id = google_bigquery_dataset.web3_analytics.dataset_id
  table_id   = "token_analytics"
  project    = var.project_id

  schema = file("${path.module}/schemas/token_analytics.json")

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["token_address", "chain_id"]

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.web3_encryption_key.id
  }
}

resource "google_bigquery_table" "portfolio_performance" {
  dataset_id = google_bigquery_dataset.web3_analytics.dataset_id
  table_id   = "portfolio_performance"
  project    = var.project_id

  schema = file("${path.module}/schemas/portfolio_performance.json")

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  clustering = ["portfolio_id", "strategy"]

  encryption_configuration {
    kms_key_name = google_kms_crypto_key.web3_encryption_key.id
  }
}

# Pub/Sub Topics
resource "google_pubsub_topic" "web3_events" {
  name    = "web3-events-${random_id.web3_suffix.hex}"
  project = var.project_id

  kms_key_name = google_kms_crypto_key.web3_encryption_key.id

  message_retention_duration = "604800s" # 7 days
}

resource "google_pubsub_topic" "blockchain_transactions" {
  name    = "blockchain-transactions-${random_id.web3_suffix.hex}"
  project = var.project_id

  kms_key_name = google_kms_crypto_key.web3_encryption_key.id

  message_retention_duration = "604800s"
}

resource "google_pubsub_topic" "security_alerts" {
  name    = "security-alerts-${random_id.web3_suffix.hex}"
  project = var.project_id

  kms_key_name = google_kms_crypto_key.web3_encryption_key.id

  message_retention_duration = "2592000s" # 30 days
}

# Pub/Sub Subscriptions
resource "google_pubsub_subscription" "web3_provider_sub" {
  name  = "web3-provider-sub-${random_id.web3_suffix.hex}"
  topic = google_pubsub_topic.web3_events.name
  project = var.project_id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = google_cloud_run_service.web3_provider.status[0].url

    oidc_token {
      service_account_email = google_service_account.web3_provider_sa.email
    }
  }
}

resource "google_pubsub_subscription" "bigquery_analytics_sub" {
  name  = "bigquery-analytics-sub-${random_id.web3_suffix.hex}"
  topic = google_pubsub_topic.blockchain_transactions.name
  project = var.project_id

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = google_cloud_run_service.bigquery_service.status[0].url

    oidc_token {
      service_account_email = google_service_account.bigquery_service_sa.email
    }
  }
}

# Cloud Run Service - Web3 Provider
resource "google_cloud_run_service" "web3_provider" {
  name     = "web3-provider-${random_id.web3_suffix.hex}"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/cpu-throttling" = "false"
      "run.googleapis.com/execution-environment" = "gen2"
      "run.googleapis.com/startup-cpu-boost" = "true"
      "run.googleapis.com/cpu-allocation" = "1000m"
      "run.googleapis.com/memory-allocation" = "1Gi"
    }
  }

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }
    }

    spec {
      service_account_name = google_service_account.web3_provider_sa.email

      containers {
        image = var.web3_provider_image

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "1Gi"
          }
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.web3_events.name
        }

        env {
          name  = "KMS_KEY_RING"
          value = google_kms_key_ring.web3_keyring.name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_pubsub_topic.web3_events
  ]
}

# Cloud Run Service - BigQuery Analytics
resource "google_cloud_run_service" "bigquery_service" {
  name     = "bigquery-service-${random_id.web3_suffix.hex}"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/cpu-throttling" = "false"
      "run.googleapis.com/execution-environment" = "gen2"
      "run.googleapis.com/startup-cpu-boost" = "true"
      "run.googleapis.com/cpu-allocation" = "2000m"
      "run.googleapis.com/memory-allocation" = "2Gi"
    }
  }

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "5"
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }
    }

    spec {
      service_account_name = google_service_account.bigquery_service_sa.email

      containers {
        image = var.bigquery_service_image

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "DATASET_ID"
          value = google_bigquery_dataset.web3_analytics.dataset_id
        }

        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.blockchain_transactions.name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_bigquery_dataset.web3_analytics
  ]
}

# Cloud Run Service - Web3 Security
resource "google_cloud_run_service" "web3_security" {
  name     = "web3-security-${random_id.web3_suffix.hex}"
  location = var.region
  project  = var.project_id

  metadata {
    annotations = {
      "run.googleapis.com/cpu-throttling" = "false"
      "run.googleapis.com/execution-environment" = "gen2"
      "run.googleapis.com/startup-cpu-boost" = "true"
      "run.googleapis.com/cpu-allocation" = "500m"
      "run.googleapis.com/memory-allocation" = "512Mi"
    }
  }

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "3"
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/execution-environment" = "gen2"
        "run.googleapis.com/startup-cpu-boost" = "true"
      }
    }

    spec {
      service_account_name = google_service_account.web3_security_sa.email

      containers {
        image = var.web3_security_image

        ports {
          container_port = 8080
        }

        resources {
          limits = {
            cpu    = "500m"
            memory = "512Mi"
          }
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "ALERT_TOPIC"
          value = google_pubsub_topic.security_alerts.name
        }

        env {
          name  = "KMS_KEY_RING"
          value = google_kms_key_ring.web3_keyring.name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    google_pubsub_topic.security_alerts
  ]
}

# IAM policy for public access to Cloud Run services
resource "google_cloud_run_service_iam_policy" "web3_provider_public" {
  location    = google_cloud_run_service.web3_provider.location
  project     = google_cloud_run_service.web3_provider.project
  service     = google_cloud_run_service.web3_provider.name
  policy_data = data.google_iam_policy.public_policy.policy_data
}

resource "google_cloud_run_service_iam_policy" "bigquery_service_public" {
  location    = google_cloud_run_service.bigquery_service.location
  project     = google_cloud_run_service.bigquery_service.project
  service     = google_cloud_run_service.bigquery_service.name
  policy_data = data.google_iam_policy.public_policy.policy_data
}

# Data source for public IAM policy
data "google_iam_policy" "public_policy" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers"
    ]
  }
}

# Firewall rules for internal communication
resource "google_compute_firewall" "allow_internal_web3" {
  name    = "allow-internal-web3-${random_id.web3_suffix.hex}"
  network = var.vpc_network

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["web3-service"]
}

# Output values
output "web3_provider_url" {
  description = "URL of the Web3 Provider Cloud Run service"
  value       = google_cloud_run_service.web3_provider.status[0].url
}

output "bigquery_service_url" {
  description = "URL of the BigQuery Analytics Cloud Run service"
  value       = google_cloud_run_service.bigquery_service.status[0].url
}

output "web3_security_url" {
  description = "URL of the Web3 Security Cloud Run service"
  value       = google_cloud_run_service.web3_security.status[0].url
}

output "kms_key_ring" {
  description = "KMS Key Ring name"
  value       = google_kms_key_ring.web3_keyring.name
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.web3_analytics.dataset_id
}

output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value = {
    web3_events            = google_pubsub_topic.web3_events.name
    blockchain_transactions = google_pubsub_topic.blockchain_transactions.name
    security_alerts        = google_pubsub_topic.security_alerts.name
  }
}