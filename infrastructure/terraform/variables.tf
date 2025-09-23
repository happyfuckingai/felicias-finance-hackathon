variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
  default     = "felicia-finance-prod"
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Google Cloud zone"
  type        = string
  default     = "europe-west1-b"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "enabled_services" {
  description = "List of Google Cloud services to enable"
  type        = list(string)
  default = [
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "container.googleapis.com",
    "bigquery.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "aiplatform.googleapis.com",
    "kms.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com"
  ]
}

variable "web3_provider_image" {
  description = "Docker image för Web3 provider service"
  type        = string
  default     = "gcr.io/felicia-finance-prod/web3-provider:latest"
}

variable "bigquery_service_image" {
  description = "Docker image för BigQuery service"
  type        = string
  default     = "gcr.io/felicia-finance-prod/bigquery-service:latest"
}

variable "security_service_image" {
  description = "Docker image för security service"
  type        = string
  default     = "gcr.io/felicia-finance-prod/security-service:latest"
}

variable "web3_provider_min_instances" {
  description = "Minimum instances för Web3 provider"
  type        = number
  default     = 1
}

variable "web3_provider_max_instances" {
  description = "Maximum instances för Web3 provider"
  type        = number
  default     = 10
}

variable "bigquery_service_min_instances" {
  description = "Minimum instances för BigQuery service"
  type        = number
  default     = 1
}

variable "bigquery_service_max_instances" {
  description = "Maximum instances för BigQuery service"
  type        = number
  default     = 5
}

variable "security_service_min_instances" {
  description = "Minimum instances för security service"
  type        = number
  default     = 1
}

variable "security_service_max_instances" {
  description = "Maximum instances för security service"
  type        = number
  default     = 3
}

variable "web3_provider_cpu" {
  description = "CPU allocation för Web3 provider (m)"
  type        = string
  default     = "1000m"
}

variable "web3_provider_memory" {
  description = "Memory allocation för Web3 provider (Mi)"
  type        = string
  default     = "2048Mi"
}

variable "bigquery_service_cpu" {
  description = "CPU allocation för BigQuery service (m)"
  type        = string
  default     = "2000m"
}

variable "bigquery_service_memory" {
  description = "Memory allocation för BigQuery service (Mi)"
  type        = string
  default     = "4096Mi"
}

variable "security_service_cpu" {
  description = "CPU allocation för security service (m)"
  type        = string
  default     = "500m"
}

variable "security_service_memory" {
  description = "Memory allocation för security service (Mi)"
  type        = string
  default     = "1024Mi"
}

variable "bigquery_dataset_trading" {
  description = "BigQuery dataset för trading analytics"
  type        = string
  default     = "trading_analytics"
}

variable "bigquery_dataset_portfolio" {
  description = "BigQuery dataset för portfolio tracking"
  type        = string
  default     = "portfolio_tracking"
}

variable "vpc_cidr_block" {
  description = "CIDR block för VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "web3_subnet_cidr" {
  description = "CIDR block för Web3 subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "bigquery_subnet_cidr" {
  description = "CIDR block för BigQuery subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "kms_key_rotation_period" {
  description = "KMS key rotation period"
  type        = string
  default     = "7776000s"  # 90 dagar
}

variable "monitoring_notification_channels" {
  description = "List of notification channels för monitoring alerts"
  type        = list(string)
  default     = []
}

variable "domain_name" {
  description = "Domain name för load balancer"
  type        = string
  default     = "api.felicia-finance.com"
}

variable "ssl_certificate_name" {
  description = "SSL certificate name"
  type        = string
  default     = "felicia-finance-ssl-cert"
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 30
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "enable_cloud_nat" {
  description = "Enable Cloud NAT för private subnets"
  type        = bool
  default     = true
}

variable "enable_cloud_cdn" {
  description = "Enable Cloud CDN för static assets"
  type        = bool
  default     = true
}

variable "enable_stackdriver_trace" {
  description = "Enable Stackdriver Trace"
  type        = bool
  default     = true
}

variable "alert_thresholds" {
  description = "Alert thresholds för monitoring"
  type = object({
    cpu_utilization_percent    = number
    memory_utilization_percent = number
    error_rate_percent         = number
    latency_ms                 = number
  })
  default = {
    cpu_utilization_percent    = 80
    memory_utilization_percent = 85
    error_rate_percent         = 5
    latency_ms                 = 1000
  }
}

variable "auto_backup_schedule" {
  description = "Schedule för automated backups"
  type        = string
  default     = "0 2 * * *"  # Daily at 2 AM
}

variable "maintenance_window" {
  description = "Maintenance window för updates"
  type        = string
  default     = "SUN 02:00-04:00"
}