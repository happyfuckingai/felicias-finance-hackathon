"""
Google Cloud IAM Configuration
IAM roles och service accounts för Google Cloud Web3 integration
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GCPServiceAccount:
    """Representerar en Google Cloud Service Account"""

    name: str
    display_name: str
    description: str
    roles: List[str]

@dataclass
class GCPIAMConfig:
    """IAM konfiguration för Google Cloud Web3 integration"""

    # =============================================================================
    # SERVICE ACCOUNTS
    # =============================================================================

    # Huvudservicekonton för olika tjänster
    SERVICE_ACCOUNTS: Dict[str, GCPServiceAccount] = None

    # =============================================================================
    # CUSTOM ROLES
    # =============================================================================

    # Custom role för trading operations
    CUSTOM_ROLE_TRADING: str = "CryptoTradingRole"

    # Custom role för analytics operations
    CUSTOM_ROLE_ANALYTICS: str = "CryptoAnalyticsRole"

    # Custom role för monitoring operations
    CUSTOM_ROLE_MONITORING: str = "CryptoMonitoringRole"

    # =============================================================================
    # STANDARD ROLES
    # =============================================================================

    # Standard Google Cloud roles som används
    STANDARD_ROLES = [
        "roles/web3gateway.user",
        "roles/bigquery.dataEditor",
        "roles/bigquery.dataViewer",
        "roles/pubsub.editor",
        "roles/pubsub.publisher",
        "roles/pubsub.subscriber",
        "roles/firestore.user",
        "roles/storage.objectAdmin",
        "roles/aiplatform.user",
        "roles/cloudfunctions.invoker",
        "roles/run.invoker",
        "roles/monitoring.viewer",
        "roles/logging.viewer",
        "roles/iam.serviceAccountUser",
        "roles/serviceusage.apiKeysAdmin"
    ]

    def __post_init__(self):
        """Initiera service accounts dictionary"""
        if self.SERVICE_ACCOUNTS is None:
            self.SERVICE_ACCOUNTS = {
                "trading-bot": GCPServiceAccount(
                    name="trading-bot",
                    display_name="Crypto Trading Bot Service Account",
                    description="Service account för automatiserad crypto trading med Web3 Gateway",
                    roles=[
                        "roles/web3gateway.user",
                        "roles/bigquery.dataEditor",
                        "roles/bigquery.dataViewer",
                        "roles/pubsub.publisher",
                        "roles/pubsub.subscriber",
                        "roles/firestore.user",
                        "roles/storage.objectAdmin",
                        "roles/aiplatform.user",
                        "roles/cloudfunctions.invoker",
                        "roles/run.invoker",
                        "roles/monitoring.viewer",
                        "roles/logging.viewer"
                    ]
                ),

                "analytics-service": GCPServiceAccount(
                    name="analytics-service",
                    display_name="Trading Analytics Service Account",
                    description="Service account för trading analytics och BigQuery operations",
                    roles=[
                        "roles/bigquery.dataViewer",
                        "roles/bigquery.dataEditor",
                        "roles/storage.objectViewer",
                        "roles/aiplatform.user",
                        "roles/monitoring.viewer"
                    ]
                ),

                "monitoring-service": GCPServiceAccount(
                    name="monitoring-service",
                    display_name="System Monitoring Service Account",
                    description="Service account för system monitoring och alerting",
                    roles=[
                        "roles/monitoring.viewer",
                        "roles/logging.viewer",
                        "roles/pubsub.publisher",
                        "roles/cloudfunctions.invoker"
                    ]
                ),

                "dex-oracle": GCPServiceAccount(
                    name="dex-oracle",
                    display_name="DEX Oracle Service Account",
                    description="Service account för DEX data oracle och price feeds",
                    roles=[
                        "roles/web3gateway.user",
                        "roles/pubsub.publisher",
                        "roles/firestore.user",
                        "roles/monitoring.viewer"
                    ]
                ),

                "market-data-processor": GCPServiceAccount(
                    name="market-data-processor",
                    display_name="Market Data Processor Service Account",
                    description="Service account för real-tids market data processing",
                    roles=[
                        "roles/pubsub.subscriber",
                        "roles/pubsub.publisher",
                        "roles/bigquery.dataEditor",
                        "roles/firestore.user",
                        "roles/aiplatform.user"
                    ]
                ),

                "notification-service": GCPServiceAccount(
                    name="notification-service",
                    display_name="Notification Service Account",
                    description="Service account för trading notifications och alerts",
                    roles=[
                        "roles/pubsub.publisher",
                        "roles/cloudfunctions.invoker",
                        "roles/monitoring.viewer"
                    ]
                )
            }

    # =============================================================================
    # ROLE PERMISSIONS
    # =============================================================================

    CUSTOM_ROLE_PERMISSIONS = {
        "CryptoTradingRole": [
            # Web3 Gateway permissions
            "web3gateway.gateways.get",
            "web3gateway.gateways.list",
            "web3gateway.transactions.send",

            # BigQuery permissions
            "bigquery.tables.get",
            "bigquery.tables.list",
            "bigquery.tables.create",
            "bigquery.tables.update",
            "bigquery.tables.delete",
            "bigquery.jobs.create",
            "bigquery.datasets.get",
            "bigquery.datasets.list",

            # Pub/Sub permissions
            "pubsub.topics.get",
            "pubsub.topics.list",
            "pubsub.topics.create",
            "pubsub.topics.publish",
            "pubsub.subscriptions.get",
            "pubsub.subscriptions.list",
            "pubsub.subscriptions.create",
            "pubsub.subscriptions.consume",

            # Firestore permissions
            "datastore.databases.get",
            "datastore.entities.get",
            "datastore.entities.list",
            "datastore.entities.create",
            "datastore.entities.update",
            "datastore.entities.delete",

            # Storage permissions
            "storage.objects.get",
            "storage.objects.list",
            "storage.objects.create",
            "storage.objects.update",
            "storage.objects.delete",
            "storage.buckets.get",
            "storage.buckets.list",

            # AI Platform permissions
            "aiplatform.endpoints.predict",
            "aiplatform.models.get",
            "aiplatform.models.list",

            # Cloud Functions permissions
            "cloudfunctions.functions.invoke",

            # Cloud Run permissions
            "run.services.invoke",

            # Monitoring permissions
            "monitoring.timeSeries.list",
            "monitoring.dashboards.get",
            "monitoring.dashboards.list",

            # Logging permissions
            "logging.logEntries.list"
        ],

        "CryptoAnalyticsRole": [
            # BigQuery permissions
            "bigquery.tables.get",
            "bigquery.tables.list",
            "bigquery.jobs.create",
            "bigquery.datasets.get",
            "bigquery.datasets.list",

            # Storage permissions
            "storage.objects.get",
            "storage.objects.list",
            "storage.buckets.get",
            "storage.buckets.list",

            # AI Platform permissions
            "aiplatform.endpoints.predict",
            "aiplatform.models.get",
            "aiplatform.models.list",
            "aiplatform.endpoints.deploy",
            "aiplatform.endpoints.undeploy",

            # Monitoring permissions
            "monitoring.timeSeries.list",
            "monitoring.dashboards.get",
            "monitoring.dashboards.list"
        ],

        "CryptoMonitoringRole": [
            # Monitoring permissions
            "monitoring.timeSeries.list",
            "monitoring.timeSeries.create",
            "monitoring.dashboards.get",
            "monitoring.dashboards.list",
            "monitoring.dashboards.create",
            "monitoring.dashboards.update",
            "monitoring.dashboards.delete",
            "monitoring.alertPolicies.get",
            "monitoring.alertPolicies.list",
            "monitoring.alertPolicies.create",
            "monitoring.alertPolicies.update",
            "monitoring.alertPolicies.delete",

            # Logging permissions
            "logging.logEntries.list",
            "logging.logEntries.create",
            "logging.sinks.get",
            "logging.sinks.list",
            "logging.sinks.create",
            "logging.sinks.update",

            # Pub/Sub permissions
            "pubsub.topics.publish",
            "pubsub.topics.get",
            "pubsub.topics.list",

            # Cloud Functions permissions
            "cloudfunctions.functions.invoke"
        ]
    }

    # =============================================================================
    # PROJECT LEVEL PERMISSIONS
    # =============================================================================

    PROJECT_PERMISSIONS = [
        # Service Account management
        "iam.serviceAccounts.get",
        "iam.serviceAccounts.list",
        "iam.serviceAccounts.create",
        "iam.serviceAccounts.delete",
        "iam.serviceAccounts.update",

        # Service Account key management
        "iam.serviceAccountKeys.get",
        "iam.serviceAccountKeys.list",
        "iam.serviceAccountKeys.create",
        "iam.serviceAccountKeys.delete",

        # IAM policy management
        "iam.serviceAccounts.getIamPolicy",
        "iam.serviceAccounts.setIamPolicy",

        # Resource Manager permissions
        "resourcemanager.projects.get",
        "resourcemanager.projects.getIamPolicy",
        "resourcemanager.projects.setIamPolicy",

        # API enablement
        "serviceusage.services.enable",
        "serviceusage.services.disable"
    ]

# Global IAM configuration instance
iam_config = GCPIAMConfig()

def get_iam_config() -> GCPIAMConfig:
    """Returnera den globala IAM konfigurationen"""
    return iam_config

def get_service_account_config(service_name: str) -> Optional[GCPServiceAccount]:
    """
    Hämta konfiguration för en specifik service account

    Args:
        service_name: Namn på tjänsten

    Returns:
        GCPServiceAccount eller None om inte hittad
    """
    return iam_config.SERVICE_ACCOUNTS.get(service_name)

def get_all_service_accounts() -> Dict[str, GCPServiceAccount]:
    """Returnera alla service account konfigurationer"""
    return iam_config.SERVICE_ACCOUNTS

def get_required_roles() -> List[str]:
    """Returnera alla required standard roles"""
    return iam_config.STANDARD_ROLES.copy()

def get_custom_role_permissions(role_name: str) -> List[str]:
    """
    Hämta permissions för en custom role

    Args:
        role_name: Namn på custom role

    Returns:
        List[str]: Lista med permissions
    """
    return iam_config.CUSTOM_ROLE_PERMISSIONS.get(role_name, [])

def get_project_permissions() -> List[str]:
    """Returnera project level permissions"""
    return iam_config.PROJECT_PERMISSIONS.copy()

def validate_service_account_config(service_name: str) -> List[str]:
    """
    Validera konfiguration för en service account

    Args:
        service_name: Namn på tjänsten att validera

    Returns:
        List[str]: Lista med valideringsfel
    """
    errors = []

    service_account = get_service_account_config(service_name)
    if not service_account:
        errors.append(f"Service account '{service_name}' finns inte i konfigurationen")
        return errors

    if not service_account.roles:
        errors.append(f"Service account '{service_name}' har inga roles definierade")

    # Validera att alla roles finns i standard roles eller är custom roles
    for role in service_account.roles:
        if not (role in iam_config.STANDARD_ROLES or
                role in iam_config.CUSTOM_ROLE_PERMISSIONS):
            errors.append(f"Okänd role '{role}' för service account '{service_name}'")

    return errors

def generate_service_account_email(service_name: str, project_id: str) -> str:
    """
    Generera service account email

    Args:
        service_name: Namn på tjänsten
        project_id: Google Cloud project ID

    Returns:
        str: Service account email
    """
    return f"{service_name}@{project_id}.iam.gserviceaccount.com"

def get_setup_instructions() -> str:
    """
    Generera instruktioner för att sätta upp IAM konfiguration

    Returns:
        str: Setup instruktioner
    """
    instructions = """
# IAM Setup Instructions för Google Cloud Web3 Integration

## 1. Enable Required APIs
gcloud services enable web3gateway.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudkms.googleapis.com

## 2. Create Custom Roles
"""

    for role_name, permissions in iam_config.CUSTOM_ROLE_PERMISSIONS.items():
        instructions += f"""
### {role_name}
gcloud iam roles create {role_name.lower().replace('crypto', 'crypto').replace('role', '')} \\
    --project={os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'PROJECT_ID')} \\
    --title="{role_name}" \\
    --description="Custom role för crypto trading system" \\
    --permissions={','.join(permissions)} \\
    --stage=GA
"""

    instructions += """
## 3. Create Service Accounts
"""

    for sa_name, sa_config in iam_config.SERVICE_ACCOUNTS.items():
        instructions += f"""
### {sa_config.display_name}
gcloud iam service-accounts create {sa_name} \\
    --display-name="{sa_config.display_name}" \\
    --description="{sa_config.description}" \\
    --project={os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'PROJECT_ID')}

# Add roles to service account
"""

        for role in sa_config.roles:
            instructions += f"gcloud projects add-iam-policy-binding {os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'PROJECT_ID')} \\\n"
            instructions += f"    --member=serviceAccount:{generate_service_account_email(sa_name, os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'PROJECT_ID'))} \\\n"
            instructions += f"    --role={role}\n"

    instructions += """
## 4. Create Service Account Keys (för development/testning)
VARNING: Använd endast för development! I production, använd Workload Identity.

"""

    for sa_name in iam_config.SERVICE_ACCOUNTS.keys():
        instructions += f"gcloud iam service-accounts keys create {sa_name}-key.json \\\n"
        instructions += f"    --iam-account={generate_service_account_email(sa_name, os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'PROJECT_ID'))}\n"

    return instructions