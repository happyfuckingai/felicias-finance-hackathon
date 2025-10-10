"""
Google Cloud Web3 Integration Configuration
Huvudkonfiguration för Google Cloud Web3 Gateway och relaterade tjänster
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GoogleCloudWeb3Config:
    """Huvudkonfiguration för Google Cloud Web3 integration"""

    # =============================================================================
    # GOOGLE CLOUD PROJECT CONFIGURATION
    # =============================================================================

    # Google Cloud Project ID
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "crypto-trading-system")

    # Region för Google Cloud resurser
    REGION: str = os.getenv("GOOGLE_CLOUD_REGION", "europe-west1")

    # Zone för compute resurser
    ZONE: str = os.getenv("GOOGLE_CLOUD_ZONE", "europe-west1-b")

    # =============================================================================
    # WEB3 GATEWAY CONFIGURATION
    # =============================================================================

    # Google Cloud Web3 Gateway settings
    WEB3_GATEWAY_ENABLED: bool = os.getenv("WEB3_GATEWAY_ENABLED", "true").lower() == "true"

    # Web3 Gateway endpoint
    WEB3_GATEWAY_ENDPOINT: str = os.getenv("WEB3_GATEWAY_ENDPOINT", f"https://{PROJECT_ID}-web3-gateway.web3.gateway.dev")

    # Chain configurations för Web3 Gateway
    SUPPORTED_CHAINS: Dict[str, str] = {
        "ethereum": "mainnet",
        "polygon": "matic-mainnet",
        "arbitrum": "arbitrum-mainnet",
        "optimism": "optimism-mainnet",
        "base": "base-mainnet",
        "bsc": "bsc-mainnet"
    }

    # =============================================================================
    # BIGQUERY CONFIGURATION
    # =============================================================================

    # BigQuery dataset för trading analytics
    BIGQUERY_DATASET_TRADING: str = os.getenv("BIGQUERY_DATASET_TRADING", "trading_analytics")

    # BigQuery dataset för portfolio tracking
    BIGQUERY_DATASET_PORTFOLIO: str = os.getenv("BIGQUERY_DATASET_PORTFOLIO", "portfolio_tracking")

    # BigQuery dataset för risk metrics
    BIGQUERY_DATASET_RISK: str = os.getenv("BIGQUERY_DATASET_RISK", "risk_metrics")

    # BigQuery table för trade history
    BIGQUERY_TABLE_TRADES: str = "trades"

    # BigQuery table för portfolio snapshots
    BIGQUERY_TABLE_PORTFOLIO: str = "portfolio_snapshots"

    # BigQuery table för risk calculations
    BIGQUERY_TABLE_RISK: str = "risk_calculations"

    # =============================================================================
    # PUB/SUB CONFIGURATION
    # =============================================================================

    # Pub/Sub topics för real-tids data
    PUBSUB_TOPIC_TRADES: str = os.getenv("PUBSUB_TOPIC_TRADES", "crypto-trades")

    # Pub/Sub topic för price updates
    PUBSUB_TOPIC_PRICES: str = os.getenv("PUBSUB_TOPIC_PRICES", "price-updates")

    # Pub/Sub topic för alerts
    PUBSUB_TOPIC_ALERTS: str = os.getenv("PUBSUB_TOPIC_ALERTS", "trading-alerts")

    # Pub/Sub subscription för trade processing
    PUBSUB_SUBSCRIPTION_TRADES: str = "crypto-trades-processor"

    # =============================================================================
    # FIRESTORE CONFIGURATION
    # =============================================================================

    # Firestore collection för cache
    FIRESTORE_COLLECTION_CACHE: str = "token_cache"

    # Firestore collection för user preferences
    FIRESTORE_COLLECTION_PREFERENCES: str = "user_preferences"

    # Firestore collection för trading strategies
    FIRESTORE_COLLECTION_STRATEGIES: str = "trading_strategies"

    # =============================================================================
    # CLOUD STORAGE CONFIGURATION
    # =============================================================================

    # Cloud Storage bucket för model artifacts
    GCS_BUCKET_MODELS: str = os.getenv("GCS_BUCKET_MODELS", f"{PROJECT_ID}-ml-models")

    # Cloud Storage bucket för trading data
    GCS_BUCKET_TRADING_DATA: str = os.getenv("GCS_BUCKET_TRADING_DATA", f"{PROJECT_ID}-trading-data")

    # Cloud Storage bucket för backups
    GCS_BUCKET_BACKUPS: str = os.getenv("GCS_BUCKET_BACKUPS", f"{PROJECT_ID}-backups")

    # =============================================================================
    # VERTEX AI CONFIGURATION
    # =============================================================================

    # Vertex AI endpoint för ML predictions
    VERTEX_AI_ENDPOINT: str = os.getenv("VERTEX_AI_ENDPOINT", f"projects/{PROJECT_ID}/locations/{REGION}/endpoints/trading-predictor")

    # Vertex AI model för sentiment analysis
    VERTEX_AI_MODEL_SENTIMENT: str = "text-bison@001"

    # Vertex AI model för price prediction
    VERTEX_AI_MODEL_PREDICTION: str = "gemini-pro"

    # =============================================================================
    # CLOUD FUNCTIONS CONFIGURATION
    # =============================================================================

    # Cloud Function för DEX oracle
    CLOUD_FUNCTION_DEX_ORACLE: str = os.getenv("CLOUD_FUNCTION_DEX_ORACLE", "dex-oracle")

    # Cloud Function för market data processing
    CLOUD_FUNCTION_MARKET_DATA: str = os.getenv("CLOUD_FUNCTION_MARKET_DATA", "market-data-processor")

    # Cloud Function för notifications
    CLOUD_FUNCTION_NOTIFICATIONS: str = os.getenv("CLOUD_FUNCTION_NOTIFICATIONS", "notification-sender")

    # =============================================================================
    # CLOUD RUN CONFIGURATION
    # =============================================================================

    # Cloud Run service för trading bot
    CLOUD_RUN_SERVICE_TRADING_BOT: str = os.getenv("CLOUD_RUN_SERVICE_TRADING_BOT", "crypto-trading-bot")

    # Cloud Run service för analytics
    CLOUD_RUN_SERVICE_ANALYTICS: str = os.getenv("CLOUD_RUN_SERVICE_ANALYTICS", "trading-analytics")

    # Cloud Run service för risk management
    CLOUD_RUN_SERVICE_RISK: str = os.getenv("CLOUD_RUN_SERVICE_RISK", "risk-management")

    # =============================================================================
    # KMS CONFIGURATION
    # =============================================================================

    # KMS key ring för trading
    KMS_KEYRING_TRADING: str = "crypto-trading-keyring"

    # KMS key för private keys encryption
    KMS_KEY_PRIVATE_KEYS: str = "private-keys-key"

    # KMS key för API keys encryption
    KMS_KEY_API_KEYS: str = "api-keys-key"

    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================

    # Monitoring dashboard för trading metrics
    MONITORING_DASHBOARD: str = "projects/{PROJECT_ID}/dashboards/trading-metrics"

    # Alert policies för trading system
    ALERT_POLICY_TRADING_LOSS: str = "trading-loss-alert"
    ALERT_POLICY_API_RATE_LIMIT: str = "api-rate-limit-alert"
    ALERT_POLICY_SYSTEM_HEALTH: str = "system-health-alert"

    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================

    # Log bucket för trading logs
    LOG_BUCKET: str = f"gs://{PROJECT_ID}-logs"

    # Log filter för error tracking
    LOG_FILTER_ERRORS: str = 'severity>=ERROR'

    # =============================================================================
    # SERVICE ACCOUNT CONFIGURATION
    # =============================================================================

    # Service account för trading operations
    SERVICE_ACCOUNT_TRADING: str = f"trading-bot@{PROJECT_ID}.iam.gserviceaccount.com"

    # Service account för analytics
    SERVICE_ACCOUNT_ANALYTICS: str = f"analytics-service@{PROJECT_ID}.iam.gserviceaccount.com"

    # Service account för monitoring
    SERVICE_ACCOUNT_MONITORING: str = f"monitoring-service@{PROJECT_ID}.iam.gserviceaccount.com"

    # =============================================================================
    # RETRY CONFIGURATION
    # =============================================================================

    # Max retry attempts för API calls
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

    # Base delay för exponential backoff (sekunder)
    RETRY_BASE_DELAY: float = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

    # Max delay för exponential backoff (sekunder)
    RETRY_MAX_DELAY: float = float(os.getenv("RETRY_MAX_DELAY", "60.0"))

    # =============================================================================
    # RATE LIMITING
    # =============================================================================

    # Rate limit för BigQuery queries (queries per minute)
    BIGQUERY_RATE_LIMIT: int = int(os.getenv("BIGQUERY_RATE_LIMIT", "100"))

    # Rate limit för Web3 Gateway calls (calls per second)
    WEB3_GATEWAY_RATE_LIMIT: int = int(os.getenv("WEB3_GATEWAY_RATE_LIMIT", "10"))

    # Rate limit för Vertex AI calls (calls per minute)
    VERTEX_AI_RATE_LIMIT: int = int(os.getenv("VERTEX_AI_RATE_LIMIT", "60"))

    # =============================================================================
    # PERFORMANCE CONFIGURATION
    # =============================================================================

    # Batch size för BigQuery operations
    BIGQUERY_BATCH_SIZE: int = int(os.getenv("BIGQUERY_BATCH_SIZE", "1000"))

    # Cache TTL för Firestore (sekunder)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # Connection pool size för databases
    CONNECTION_POOL_SIZE: int = int(os.getenv("CONNECTION_POOL_SIZE", "10"))

# Global configuration instance
config = GoogleCloudWeb3Config()

def get_config() -> GoogleCloudWeb3Config:
    """Returnera den globala konfigurationen"""
    return config

def validate_config() -> List[str]:
    """
    Validera konfiguration och returnera lista med fel

    Returns:
        List[str]: Lista med valideringsfel
    """
    errors = []

    if not config.PROJECT_ID:
        errors.append("GOOGLE_CLOUD_PROJECT_ID är inte satt")

    if config.WEB3_GATEWAY_ENABLED and not config.WEB3_GATEWAY_ENDPOINT:
        errors.append("WEB3_GATEWAY_ENDPOINT är inte satt när Web3 Gateway är aktiverad")

    required_env_vars = [
        "GOOGLE_CLOUD_PROJECT_ID",
        "GOOGLE_CLOUD_REGION"
    ]

    for var in required_env_vars:
        if not os.getenv(var):
            errors.append(f"Environment variable {var} är inte satt")

    return errors

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_service_account_email(service: str) -> str:
    """
    Generera service account email för en given tjänst

    Args:
        service: Tjänstnamn (t.ex. "trading-bot")

    Returns:
        str: Service account email
    """
    return f"{service}@{config.PROJECT_ID}.iam.gserviceaccount.com"

def get_bigquery_table_path(dataset: str, table: str) -> str:
    """
    Generera full BigQuery table path

    Args:
        dataset: Dataset namn
        table: Table namn

    Returns:
        str: Full table path
    """
    return f"{config.PROJECT_ID}.{dataset}.{table}"

def is_production() -> bool:
    """Kontrollera om systemet körs i production mode"""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"

def get_environment() -> str:
    """Returnera nuvarande environment"""
    return os.getenv("ENVIRONMENT", "development")