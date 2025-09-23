output "project_id" {
  description = "Google Cloud project ID"
  value       = var.project_id
}

output "region" {
  description = "Google Cloud region"
  value       = var.region
}

output "zone" {
  description = "Google Cloud zone"
  value       = var.zone
}

# =============================================================================
# SERVICE ACCOUNTS
# =============================================================================

output "web3_provider_service_account_email" {
  description = "Web3 provider service account email"
  value       = google_service_account.web3_provider_sa.email
}

output "bigquery_service_account_email" {
  description = "BigQuery service account email"
  value       = google_service_account.bigquery_service_sa.email
}

output "security_service_account_email" {
  description = "Security service account email"
  value       = google_service_account.security_service_sa.email
}

# =============================================================================
# NETWORKING
# =============================================================================

output "vpc_name" {
  description = "VPC network name"
  value       = google_compute_network.vpc.name
}

output "web3_subnet_name" {
  description = "Web3 subnet name"
  value       = google_compute_subnetwork.web3_subnet.name
}

output "bigquery_subnet_name" {
  description = "BigQuery subnet name"
  value       = google_compute_subnetwork.bigquery_subnet.name
}

output "load_balancer_ip" {
  description = "Load balancer IP address"
  value       = google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address
}

output "load_balancer_url" {
  description = "Load balancer URL"
  value       = "http://${google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address}"
}

# =============================================================================
# CLOUD RUN SERVICES
# =============================================================================

output "web3_provider_url" {
  description = "Web3 provider service URL"
  value       = google_cloud_run_service.web3_provider.status[0].url
}

output "web3_provider_service_name" {
  description = "Web3 provider service name"
  value       = google_cloud_run_service.web3_provider.name
}

output "bigquery_service_url" {
  description = "BigQuery service URL"
  value       = google_cloud_run_service.bigquery_service.status[0].url
}

output "bigquery_service_name" {
  description = "BigQuery service name"
  value       = google_cloud_run_service.bigquery_service.name
}

output "security_service_url" {
  description = "Security service URL"
  value       = google_cloud_run_service.security_service.status[0].url
}

output "security_service_name" {
  description = "Security service name"
  value       = google_cloud_run_service.security_service.name
}

# =============================================================================
# BIGQUERY DATASETS
# =============================================================================

output "trading_analytics_dataset" {
  description = "Trading analytics BigQuery dataset ID"
  value       = google_bigquery_dataset.trading_analytics.dataset_id
}

output "portfolio_tracking_dataset" {
  description = "Portfolio tracking BigQuery dataset ID"
  value       = google_bigquery_dataset.portfolio_tracking.dataset_id
}

output "bigquery_project_dataset" {
  description = "Full BigQuery project.dataset path för trading analytics"
  value       = "${var.project_id}.${google_bigquery_dataset.trading_analytics.dataset_id}"
}

# =============================================================================
# PUB/SUB
# =============================================================================

output "crypto_trades_topic" {
  description = "Crypto trades Pub/Sub topic name"
  value       = google_pubsub_topic.crypto_trades.name
}

output "price_updates_topic" {
  description = "Price updates Pub/Sub topic name"
  value       = google_pubsub_topic.price_updates.name
}

output "trading_alerts_topic" {
  description = "Trading alerts Pub/Sub topic name"
  value       = google_pubsub_topic.trading_alerts.name
}

output "crypto_trades_subscription" {
  description = "Crypto trades processor subscription name"
  value       = google_pubsub_subscription.crypto_trades_processor.name
}

output "price_updates_subscription" {
  description = "Price updates processor subscription name"
  value       = google_pubsub_subscription.price_updates_processor.name
}

# =============================================================================
# KMS
# =============================================================================

output "kms_keyring_name" {
  description = "KMS keyring name"
  value       = google_kms_key_ring.felicia_keyring.name
}

output "kms_keyring_location" {
  description = "KMS keyring location"
  value       = google_kms_key_ring.felicia_keyring.location
}

output "web3_signing_key_id" {
  description = "Web3 signing key ID"
  value       = google_kms_crypto_key.web3_signing_key.id
}

output "api_keys_encryption_key_id" {
  description = "API keys encryption key ID"
  value       = google_kms_crypto_key.api_keys_key.id
}

# =============================================================================
# CLOUD STORAGE
# =============================================================================

output "web3_data_bucket" {
  description = "Web3 data storage bucket name"
  value       = google_storage_bucket.web3_data.name
}

output "ml_models_bucket" {
  description = "ML models storage bucket name"
  value       = google_storage_bucket.ml_models.name
}

output "backups_bucket" {
  description = "Backups storage bucket name"
  value       = google_storage_bucket.backups.name
}

output "web3_data_bucket_url" {
  description = "Web3 data bucket URL"
  value       = google_storage_bucket.web3_data.url
}

# =============================================================================
# MONITORING
# =============================================================================

output "monitoring_dashboard_url" {
  description = "Cloud Monitoring dashboard URL"
  value       = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
}

output "logging_url" {
  description = "Cloud Logging URL"
  value       = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
}

# =============================================================================
# SERVICE ENDPOINTS
# =============================================================================

output "api_base_url" {
  description = "Base URL för API endpoints"
  value       = "http://${google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address}"
}

output "web3_provider_endpoint" {
  description = "Web3 provider API endpoint"
  value       = "${google_cloud_run_service.web3_provider.status[0].url}/api/v1/web3"
}

output "portfolio_analytics_endpoint" {
  description = "Portfolio analytics API endpoint"
  value       = "${google_cloud_run_service.bigquery_service.status[0].url}/api/v1/portfolio"
}

output "security_service_endpoint" {
  description = "Security service API endpoint"
  value       = "${google_cloud_run_service.security_service.status[0].url}/api/v1/security"
}

# =============================================================================
# DEPLOYMENT INFORMATION
# =============================================================================

output "deployment_timestamp" {
  description = "Deployment timestamp"
  value       = timestamp()
}

output "terraform_version" {
  description = "Terraform version used"
  value       = "1.5.7"
}

output "google_provider_version" {
  description = "Google provider version"
  value       = "~> 4.0"
}

# =============================================================================
# CONNECTION STRINGS
# =============================================================================

output "web3_provider_connection_string" {
  description = "Web3 provider connection string för clients"
  value       = "${google_cloud_run_service.web3_provider.status[0].url}"
}

output "bigquery_service_connection_string" {
  description = "BigQuery service connection string för clients"
  value       = "${google_cloud_run_service.bigquery_service.status[0].url}"
}

output "load_balancer_connection_string" {
  description = "Load balancer connection string för clients"
  value       = "http://${google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address}"
}

# =============================================================================
# SERVICE STATUS
# =============================================================================

output "services_status" {
  description = "Status för alla deployade services"
  value = {
    web3_provider = {
      name = google_cloud_run_service.web3_provider.name
      url  = google_cloud_run_service.web3_provider.status[0].url
      status = "deployed"
    }
    bigquery_service = {
      name = google_cloud_run_service.bigquery_service.name
      url  = google_cloud_run_service.bigquery_service.status[0].url
      status = "deployed"
    }
    security_service = {
      name = google_cloud_run_service.security_service.name
      url  = google_cloud_run_service.security_service.status[0].url
      status = "deployed"
    }
  }
}

# =============================================================================
# SECURITY INFORMATION
# =============================================================================

output "service_accounts_created" {
  description = "List of created service accounts"
  value = [
    google_service_account.web3_provider_sa.email,
    google_service_account.bigquery_service_sa.email,
    google_service_account.security_service_sa.email
  ]
}

output "kms_keys_created" {
  description = "List of created KMS keys"
  value = [
    google_kms_crypto_key.web3_signing_key.name,
    google_kms_crypto_key.api_keys_key.name
  ]
}

# =============================================================================
# NETWORK INFORMATION
# =============================================================================

output "network_information" {
  description = "Network configuration information"
  value = {
    vpc_name         = google_compute_network.vpc.name
    web3_subnet      = google_compute_subnetwork.web3_subnet.name
    bigquery_subnet  = google_compute_subnetwork.bigquery_subnet.name
    load_balancer_ip = google_compute_global_forwarding_rule.felicia_finance_forwarding_rule.ip_address
    firewall_rules   = [
      google_compute_firewall.allow_internal.name,
      google_compute_firewall.allow_health_checks.name
    ]
  }
}

# =============================================================================
# MONITORING LINKS
# =============================================================================

output "monitoring_links" {
  description = "Useful monitoring and management links"
  value = {
    cloud_console           = "https://console.cloud.google.com/home/dashboard?project=${var.project_id}"
    cloud_run_dashboard     = "https://console.cloud.google.com/run?project=${var.project_id}"
    bigquery_console        = "https://console.cloud.google.com/bigquery?project=${var.project_id}"
    monitoring_dashboard    = "https://console.cloud.google.com/monitoring/dashboards?project=${var.project_id}"
    logging_console         = "https://console.cloud.google.com/logs/query?project=${var.project_id}"
    pubsub_console          = "https://console.cloud.google.com/cloudpubsub?project=${var.project_id}"
    kms_console             = "https://console.cloud.google.com/security/kms?project=${var.project_id}"
    load_balancer_console   = "https://console.cloud.google.com/net-services/loadbalancing/loadBalancers/details?project=${var.project_id}"
  }
}