# Google Cloud Web3 Integration - Security Configuration
# This file defines security policies and compliance rules for Web3 services

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

# Organization Policy for Web3 Project
resource "google_org_policy_policy" "require_shielded_vm" {
  name     = "projects/${var.project_id}/policies/compute.requireShieldedVm"
  parent   = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "restrict_vm_external_ip" {
  name     = "projects/${var.project_id}/policies/compute.vmExternalIpAccess"
  parent   = "projects/${var.project_id}"

  spec {
    rules {
      deny_all = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "require_os_login" {
  name     = "projects/${var.project_id}/policies/compute.requireOsLogin"
  parent   = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "restrict_service_account_keys" {
  name     = "projects/${var.project_id}/policies/iam.disableServiceAccountKeyCreation"
  parent   = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Access Context Manager for VPC Service Controls
resource "google_access_context_manager_access_policy" "web3_policy" {
  parent = "projects/${var.project_id}"
  title  = "Web3 Access Policy"
}

resource "google_access_context_manager_access_level" "web3_internal_access" {
  parent = "accessPolicies/${google_access_context_manager_access_policy.web3_policy.name}"
  name   = "accessPolicies/${google_access_context_manager_access_policy.web3_policy.name}/accessLevels/web3_internal"

  title       = "Web3 Internal Access Level"
  description = "Access level for internal Web3 services"

  basic {
    conditions {
      device_policy {
        require_screen_lock = false
        allowed_encryption_statuses = ["ENCRYPTED"]
      }

      allowed_cloud_function_source_ranges = []
    }
  }
}

# VPC Service Controls Service Perimeter
resource "google_access_context_manager_service_perimeter" "web3_perimeter" {
  parent    = "accessPolicies/${google_access_context_manager_access_policy.web3_policy.name}"
  name      = "accessPolicies/${google_access_context_manager_access_policy.web3_policy.name}/servicePerimeters/web3_restricted"
  title     = "Web3 Restricted Services"
  perimeter_type = "REGULAR"

  status {
    restricted_services = [
      "bigquery.googleapis.com",
      "pubsub.googleapis.com",
      "cloudkms.googleapis.com",
      "run.googleapis.com"
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED_SERVICES"]
    }

    access_levels = [
      google_access_context_manager_access_level.web3_internal_access.name
    ]
  }
}

# Cloud Armor Security Policy
resource "google_compute_security_policy" "web3_security_policy" {
  name    = "web3-security-policy-${random_id.web3_suffix.hex}"
  project = var.project_id

  rule {
    action   = "deny(403)"
    priority = 1000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default deny rule for security policy"
  }

  rule {
    action   = "allow"
    priority = 900
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["10.0.0.0/8"] # Internal VPC ranges
      }
    }
    description = "Allow internal VPC traffic"
  }

  rule {
    action   = "allow"
    priority = 800
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = [
          "130.211.0.0/22",  # Google Health Checks
          "35.191.0.0/16",   # Google Health Checks
          "35.235.240.0/20"  # IAP and Health Checks
        ]
      }
    }
    description = "Allow Google Cloud health checks and IAP"
  }
}

# Cloud KMS Crypto Key for Web3 Security
resource "google_kms_crypto_key" "web3_security_key" {
  name            = "web3-security-key"
  key_ring        = google_kms_key_ring.web3_keyring.id
  rotation_period = "7776000s" # 90 days
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm = "GOOGLE_SYMMETRIC_ENCRYPTION"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Service Account for Security Operations
resource "google_service_account" "security_operations_sa" {
  account_id   = "security-operations-${random_id.web3_suffix.hex}"
  display_name = "Security Operations Service Account"
  project      = var.project_id
}

# IAM Bindings for Security Service Account
resource "google_project_iam_binding" "security_operations_logging" {
  project = var.project_id
  role    = "roles/logging.admin"
  members = [
    "serviceAccount:${google_service_account.security_operations_sa.email}"
  ]
}

resource "google_project_iam_binding" "security_operations_monitoring" {
  project = var.project_id
  role    = "roles/monitoring.admin"
  members = [
    "serviceAccount:${google_service_account.security_operations_sa.email}"
  ]
}

resource "google_project_iam_binding" "security_operations_kms" {
  project = var.project_id
  role    = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:${google_service_account.security_operations_sa.email}"
  ]
}

# Cloud Audit Logs Configuration
resource "google_project_iam_audit_config" "web3_audit_logs" {
  project = var.project_id
  service = "allServices"

  audit_log_config {
    log_type = "DATA_READ"
  }

  audit_log_config {
    log_type = "DATA_WRITE"
  }

  audit_log_config {
    log_type = "ADMIN_READ"
  }
}

# Essential Contacts for Security Alerts
resource "google_essential_contacts_contact" "security_contact" {
  parent = "projects/${var.project_id}"
  email  = var.security_contact_email

  language_tag = "en-US"

  notification_category_subscriptions = [
    "SECURITY",
    "TECHNICAL",
    "LEGAL",
    "PRODUCT_UPDATES",
    "SUSPENSION"
  ]
}

# Cloud Monitoring Alert Policy for Security Events
resource "google_monitoring_alert_policy" "security_incident_policy" {
  display_name = "Web3 Security Incident Detection"
  project      = var.project_id

  documentation {
    content   = "Alert triggered when suspicious Web3 security events are detected"
    mime_type = "text/markdown"
  }

  user_labels = {
    alert_type = "security"
    component  = "web3"
  }

  conditions {
    display_name = "Suspicious API Access Pattern"

    condition_threshold {
      filter     = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.web3_suspicious_activity.name}\" resource.type=\"global\""
      duration   = "60s"
      comparison = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.security_email.name]

  alert_strategy {
    auto_close = "1800s"
  }
}

# Cloud Logging Metrics for Security Events
resource "google_logging_metric" "web3_suspicious_activity" {
  name    = "web3-suspicious-activity-${random_id.web3_suffix.hex}"
  project = var.project_id
  filter  = "resource.type=\"global\" AND (protoPayload.methodName=\"SetIamPolicy\" OR protoPayload.methodName=\"CreateServiceAccountKey\") AND resource.labels.project_id=\"${var.project_id}\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"

    labels {
      key        = "user"
      value_type = "STRING"
    }
  }
}

resource "google_logging_metric" "web3_auth_failures" {
  name    = "web3-auth-failures-${random_id.web3_suffix.hex}"
  project = var.project_id
  filter  = "resource.type=\"cloud_run_revision\" AND severity>=ERROR AND \"authentication\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

# Cloud Monitoring Notification Channel
resource "google_monitoring_notification_channel" "security_email" {
  display_name = "Security Email Notifications"
  project      = var.project_id
  type         = "email"

  labels = {
    email_address = var.security_contact_email
  }
}

# Binary Authorization Policy
resource "google_binary_authorization_policy" "web3_policy" {
  project = var.project_id

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"

    require_attestations_by = [
      "projects/${var.project_id}/attestors/web3-attestor"
    ]
  }

  admission_whitelist_patterns {
    name_pattern = "gcr.io/cloudrun/placeholder@sha256:*"
  }
}

# Binary Authorization Attestor
resource "google_binary_authorization_attestor" "web3_attestor" {
  name    = "web3-attestor"
  project = var.project_id

  attestation_authority_note {
    note_reference = "projects/${var.project_id}/notes/web3-security-note"

    public_keys {
      ascii_armored_pgp_public_key = var.pgp_public_key
    }
  }
}

# Container Analysis Note
resource "google_container_analysis_note" "web3_security_note" {
  name = "web3-security-note"
  project = var.project_id
  attestation_authority {
    hint {
      human_readable_name = "Web3 Security Attestor"
    }
  }
}

# Security Health Analytics Custom Module
resource "google_scc_source" "web3_security_source" {
  display_name = "Web3 Security Health Analytics"
  organization = var.organization_id
  description  = "Custom security health analytics for Web3 services"

  security_marks_source = "ENABLED"
}

# Data Loss Prevention Job Trigger
resource "google_data_loss_prevention_job_trigger" "web3_dlp_trigger" {
  parent = "projects/${var.project_id}"

  display_name = "Web3 Data Loss Prevention"
  description  = "Scan BigQuery tables for sensitive Web3 data"

  triggers {
    schedule {
      recurrence_period_duration = "86400s" # Daily
    }
  }

  inspect_job {
    inspect_template_name = "projects/${var.project_id}/inspectTemplates/web3_inspection_template"

    storage_config {
      big_query_options {
        table_reference {
          project_id = var.project_id
          dataset_id = "web3_analytics_${random_id.web3_suffix.hex}"
          table_id   = "*"
        }
      }
    }

    actions {
      save_findings {
        output_config {
          table {
            project_id = var.project_id
            dataset_id = "web3_security"
          }
        }
      }
    }
  }
}

# DLP Inspection Template
resource "google_data_loss_prevention_inspect_template" "web3_inspection_template" {
  parent = "projects/${var.project_id}"

  display_name = "Web3 Inspection Template"
  description  = "Template for inspecting Web3 data for sensitive information"

  inspect_config {
    info_types {
      name = "CRYPTOGRAPHY_KEY"
    }

    info_types {
      name = "ETHEREUM_ADDRESS"
    }

    info_types {
      name = "BITCOIN_ADDRESS"
    }

    min_likelihood = "LIKELY"
    rule_set {
      rules {
        exclusion_rule {
          exclude_info_types {
            info_types {
              name = "CRYPTOGRAPHY_KEY"
            }
          }

          matching_type = "MATCHING_TYPE_PARTIAL_MATCH"
        }
      }
    }
  }
}

# IAM Service Account Keys Rotation Policy
resource "google_service_account_iam_binding" "web3_provider_key_rotation" {
  service_account_id = google_service_account.web3_provider_sa.name
  role               = "roles/iam.serviceAccountKeyAdmin"
  members            = ["serviceAccount:${google_service_account.security_operations_sa.email}"]
}

# Cloud SQL Database Flags for Security
resource "google_sql_database_instance" "web3_db_instance" {
  count        = var.enable_cloud_sql ? 1 : 0
  name         = "web3-db-instance-${random_id.web3_suffix.hex}"
  project      = var.project_id
  region       = var.region
  database_version = "POSTGRES_14"

  settings {
    tier = "db-f1-micro"

    disk_autoresize = true
    disk_size       = 10
    disk_type       = "PD_SSD"

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.web3_vpc.id
      require_ssl     = true
    }

    backup_configuration {
      enabled            = true
      start_time         = "02:00"
      transaction_log_retention_days = 7
    }

    maintenance_window {
      day  = 7
      hour = 2
    }
  }

  encryption_key_name = google_kms_crypto_key.web3_security_key.id

  depends_on = [
    google_kms_crypto_key.web3_security_key
  ]
}

# Output values
output "security_policy" {
  description = "Cloud Armor security policy name"
  value       = google_compute_security_policy.web3_security_policy.name
}

output "kms_security_key" {
  description = "KMS security key ID"
  value       = google_kms_crypto_key.web3_security_key.id
}

output "security_service_account" {
  description = "Security operations service account email"
  value       = google_service_account.security_operations_sa.email
}

output "access_policy" {
  description = "Access Context Manager policy name"
  value       = google_access_context_manager_access_policy.web3_policy.name
}

output "alert_policy" {
  description = "Security alert policy name"
  value       = google_monitoring_alert_policy.security_incident_policy.name
}