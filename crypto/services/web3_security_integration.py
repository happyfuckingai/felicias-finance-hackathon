"""
Web3 Security Integration - Integration av alla säkerhetskomponenter.
Unified security dashboard och real-tids security monitoring.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

from ..core.errors.error_handling import handle_errors, CryptoError, SecurityError, ValidationError
from ..security.web3_security_manager import Web3SecurityManager, SecurityContext, SecurityOperation, RiskLevel
from ..security.web3_access_control import Web3AccessControl, Permission, Role, ApprovalStatus
from ..security.web3_firewall import Web3Firewall, ThreatDetection, ThreatLevel, ThreatType

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Typer av säkerhetshändelser."""
    THREAT_DETECTED = "threat_detected"
    ACCESS_DENIED = "access_denied"
    AUTHENTICATION_FAILED = "authentication_failed"
    POLICY_VIOLATION = "policy_violation"
    ANOMALOUS_ACTIVITY = "anomalous_activity"
    SECURITY_INCIDENT = "security_incident"

@dataclass
class SecurityEvent:
    """Säkerhetshändelse."""
    event_id: str
    event_type: SecurityEventType
    timestamp: datetime
    severity: str
    component: str
    details: Dict[str, Any]
    resolved: bool = False
    resolution_notes: str = ""

@dataclass
class SecurityAlert:
    """Säkerhetsalert."""
    alert_id: str
    title: str
    description: str
    severity: ThreatLevel
    affected_components: List[str]
    recommended_actions: List[str]
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: str = ""
    acknowledged_at: Optional[datetime] = None

class Web3SecurityIntegration:
    """
    Integration av alla säkerhetskomponenter.

    Funktioner:
    - Unified security dashboard
    - Real-tids security monitoring
    - Automated threat response
    - Security event correlation
    - Incident management
    - Security reporting
    """

    def __init__(self, project_id: str, key_ring_id: str, location_id: str = "global"):
        """
        Initiera Web3 Security Integration.

        Args:
            project_id: Google Cloud project ID
            key_ring_id: KMS key ring ID
            location_id: KMS location
        """
        # Initiera säkerhetskomponenter
        self.security_manager = Web3SecurityManager(project_id, key_ring_id, location_id)
        self.access_control = Web3AccessControl()
        self.firewall = Web3Firewall()

        # Security events och alerts
        self.security_events = []
        self.active_alerts = []

        # Event correlation
        self.event_correlation_window = 300  # 5 minuter
        self.correlation_rules = {}
        self._initialize_correlation_rules()

        # Automated response rules
        self.response_rules = {}
        self._initialize_response_rules()

        # Monitoring och metrics
        self.security_metrics = {
            'total_events': 0,
            'threats_blocked': 0,
            'access_denied': 0,
            'incidents_resolved': 0,
            'average_response_time': 0.0,
            'false_positives': 0
        }

        # Background monitoring
        self.monitoring_active = False
        self.monitoring_task = None

        logger.info("Web3 Security Integration initierad")

    def _initialize_correlation_rules(self):
        """Initiera event correlation rules."""
        self.correlation_rules = {
            'multiple_failed_access': {
                'event_types': [SecurityEventType.ACCESS_DENIED, SecurityEventType.AUTHENTICATION_FAILED],
                'threshold': 5,
                'time_window': 60,  # 1 minut
                'correlated_event': SecurityEventType.ANOMALOUS_ACTIVITY
            },
            'suspicious_pattern': {
                'event_types': [SecurityEventType.THREAT_DETECTED, SecurityEventType.POLICY_VIOLATION],
                'threshold': 3,
                'time_window': 300,  # 5 minuter
                'correlated_event': SecurityEventType.SECURITY_INCIDENT
            }
        }

    def _initialize_response_rules(self):
        """Initiera automated response rules."""
        self.response_rules = {
            ThreatLevel.CRITICAL: {
                'actions': ['block_address', 'alert_admin', 'log_incident', 'trigger_backup_security']
            },
            ThreatLevel.HIGH: {
                'actions': ['block_transaction', 'alert_security_officer', 'log_threat']
            },
            ThreatLevel.MEDIUM: {
                'actions': ['monitor_activity', 'log_warning']
            },
            ThreatLevel.LOW: {
                'actions': ['log_info']
            }
        }

    async def start_monitoring(self):
        """Starta background monitoring."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Security monitoring startad")

    async def stop_monitoring(self):
        """Stoppa background monitoring."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Security monitoring stoppad")

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        try:
            while self.monitoring_active:
                # Kör security checks
                await self._perform_security_checks()

                # Korrellera events
                await self._correlate_events()

                # Uppdatera alerts
                await self._update_alerts()

                # Rensa gamla events
                await self._cleanup_old_events()

                # Vänta 30 sekunder
                await asyncio.sleep(30)

        except asyncio.CancelledError:
            logger.info("Security monitoring loop avbruten")
        except Exception as e:
            logger.error(f"Security monitoring loop misslyckades: {e}")

    async def _perform_security_checks(self):
        """Utför säkerhetskontroller."""
        try:
            # Kontrollera aktiva hot
            firewall_health = await self.firewall.health_check()

            # Kontrollera åtkomstkontroll
            access_health = await self.access_control.health_check()

            # Kontrollera security manager
            manager_health = await self.security_manager.health_check()

            # Logga hälsostatus
            if firewall_health['status'] != 'healthy':
                await self._log_security_event(
                    SecurityEventType.ANOMALOUS_ACTIVITY,
                    'warning',
                    'firewall',
                    {'health_check_failed': firewall_health.get('error', 'unknown')}
                )

            logger.debug("Security checks genomförda")

        except Exception as e:
            logger.error(f"Security checks misslyckades: {e}")

    async def _correlate_events(self):
        """Korrellera säkerhetshändelser."""
        try:
            current_time = datetime.now()

            for rule_name, rule_config in self.correlation_rules.items():
                # Hitta events inom tidsfönster
                relevant_events = [
                    event for event in self.security_events
                    if (event.event_type in rule_config['event_types'] and
                        current_time - event.timestamp < timedelta(seconds=rule_config['time_window']))
                ]

                # Kontrollera threshold
                if len(relevant_events) >= rule_config['threshold']:
                    # Skapa korrellerad händelse
                    correlated_event = SecurityEvent(
                        event_id=f"corr_{rule_name}_{current_time.timestamp()}",
                        event_type=rule_config['correlated_event'],
                        timestamp=current_time,
                        severity='high',
                        component='security_integration',
                        details={
                            'rule_name': rule_name,
                            'triggered_events': len(relevant_events),
                            'event_types': [e.event_type.value for e in relevant_events],
                            'correlation_rule': rule_config
                        }
                    )

                    self.security_events.append(correlated_event)

                    # Skapa alert
                    await self._create_correlation_alert(correlated_event)

                    logger.warning(f"Event correlation triggered: {rule_name} - {len(relevant_events)} events")

        except Exception as e:
            logger.error(f"Event correlation misslyckades: {e}")

    async def _create_correlation_alert(self, event: SecurityEvent):
        """Skapa alert för korrellerad händelse."""
        alert = SecurityAlert(
            alert_id=f"alert_{event.event_id}",
            title=f"Security Correlation Alert: {event.event_type.value}",
            description=f"Correlated security event detected: {event.details['rule_name']}",
            severity=ThreatLevel.HIGH,
            affected_components=[event.component],
            recommended_actions=[
                "Review correlated events",
                "Check for false positives",
                "Consider escalating to incident"
            ],
            created_at=event.timestamp
        )

        self.active_alerts.append(alert)

    async def _update_alerts(self):
        """Uppdatera aktiva alerts."""
        try:
            # Kontrollera om alerts behöver eskaleras
            for alert in self.active_alerts:
                if not alert.acknowledged:
                    # Eskalera efter viss tid
                    age_hours = (datetime.now() - alert.created_at).total_seconds() / 3600

                    if age_hours > 2:  # Eskalera efter 2 timmar
                        alert.recommended_actions.append("ESCALATE: Alert not acknowledged")

            # Rensa gamla icke-erkända alerts
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.active_alerts = [
                alert for alert in self.active_alerts
                if alert.created_at > cutoff_time or alert.acknowledged
            ]

        except Exception as e:
            logger.error(f"Alert update misslyckades: {e}")

    async def _cleanup_old_events(self):
        """Rensa gamla säkerhetshändelser."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            original_count = len(self.security_events)

            self.security_events = [
                event for event in self.security_events
                if event.timestamp > cutoff_time
            ]

            cleaned_count = original_count - len(self.security_events)
            if cleaned_count > 0:
                logger.debug(f"Rensade {cleaned_count} gamla security events")

        except Exception as e:
            logger.error(f"Event cleanup misslyckades: {e}")

    @handle_errors(service_name="web3_security_integration")
    async def analyze_security_request(self, user_id: str, operation: str,
                                     resource: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analysera säkerhetsbegäran och ge rekommendationer.

        Args:
            user_id: Användar-ID
            operation: Operation att utföra
            resource: Resurs att komma åt
            context: Ytterligare kontext

        Returns:
            Security analysis resultat
        """
        try:
            context = context or {}
            analysis_id = f"analysis_{user_id}_{datetime.now().timestamp()}"

            # Skapa security context
            security_context = SecurityContext(
                user_id=user_id,
                operation=SecurityOperation(operation),
                resource=resource,
                risk_level=RiskLevel.MEDIUM,  # Default
                metadata=context
            )

            # Kontrollera åtkomst
            access_allowed = await self.access_control.check_access(
                user_id, resource, Permission.ADMIN_ACCESS, context
            )

            # Analysera hot
            threat_analysis = await self.firewall.analyze_transaction(
                {"operation": operation, "resource": resource, **context},
                user_id
            )

            # Bedöm risk
            risk_assessment = await self.security_manager._assess_risk(security_context)

            # Generera rekommendationer
            recommendations = await self._generate_security_recommendations(
                access_allowed, threat_analysis, risk_assessment, context
            )

            # Logga analys
            await self._log_security_event(
                SecurityEventType.POLICY_VIOLATION if not access_allowed else SecurityEventType.ANOMALOUS_ACTIVITY,
                'info' if access_allowed else 'warning',
                'security_integration',
                {
                    'analysis_id': analysis_id,
                    'user_id': user_id,
                    'operation': operation,
                    'resource': resource,
                    'access_allowed': access_allowed,
                    'threat_level': threat_analysis.threat_level.value,
                    'risk_assessment': risk_assessment
                }
            )

            result = {
                'analysis_id': analysis_id,
                'access_allowed': access_allowed,
                'threat_analysis': {
                    'threat_level': threat_analysis.threat_level.value,
                    'threat_type': threat_analysis.threat_type.value,
                    'confidence_score': threat_analysis.confidence_score,
                    'blocked': threat_analysis.blocked
                },
                'risk_assessment': risk_assessment,
                'recommendations': recommendations,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"Security analysis genomförd för {user_id}: access={access_allowed}")
            return result

        except Exception as e:
            logger.error(f"Security analysis misslyckades för {user_id}: {e}")
            raise SecurityError(f"Security analysis misslyckades: {str(e)}", "SECURITY_ANALYSIS_FAILED")

    async def _generate_security_recommendations(self, access_allowed: bool, threat_analysis: ThreatDetection,
                                              risk_assessment: float, context: Dict[str, Any]) -> List[str]:
        """Generera säkerhetsrekommendationer."""
        recommendations = []

        if not access_allowed:
            recommendations.append("Access denied - review user permissions")
            recommendations.append("Check access control policies for this resource")
            recommendations.append("Verify user role assignments")

        if threat_analysis.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            recommendations.append(f"High threat detected: {threat_analysis.threat_type.value}")
            recommendations.append("Review transaction details for suspicious activity")
            recommendations.append("Consider blocking address if threat confirmed")

        if risk_assessment > 0.7:
            recommendations.append("High risk operation - consider additional approval")
            recommendations.append("Review operation context and justification")
            recommendations.append("Monitor for similar patterns")

        # Lägg till kontextsberoende rekommendationer
        if context.get('amount', 0) > 10000:
            recommendations.append("Large transaction amount - verify approval workflow")

        if context.get('cross_chain'):
            recommendations.append("Cross-chain operation - verify chain compatibility")

        return recommendations

    async def _log_security_event(self, event_type: SecurityEventType, severity: str,
                                component: str, details: Dict[str, Any]):
        """Logga säkerhetshändelse."""
        event = SecurityEvent(
            event_id=f"event_{event_type.value}_{datetime.now().timestamp()}",
            event_type=event_type,
            timestamp=datetime.now(),
            severity=severity,
            component=component,
            details=details
        )

        self.security_events.append(event)
        self.security_metrics['total_events'] += 1

        if severity == 'warning':
            logger.warning(f"Security Event: {event_type.value} - {details}")
        elif severity == 'critical':
            logger.error(f"Security Event: {event_type.value} - {details}")
        else:
            logger.info(f"Security Event: {event_type.value} - {details}")

    @handle_errors(service_name="web3_security_integration")
    async def get_unified_security_dashboard(self) -> Dict[str, Any]:
        """Hämta unified security dashboard."""
        try:
            # Hämta data från alla komponenter
            security_manager_dashboard = await self.security_manager.get_security_dashboard()
            access_control_dashboard = await self.access_control.get_access_control_dashboard()
            firewall_dashboard = await self.firewall.get_firewall_dashboard()

            # Beräkna unified metrics
            total_threats = len(self.security_events)
            active_threats = len([e for e in self.security_events
                                if not e.resolved and e.severity in ['high', 'critical']])

            # Säkerhetsscore
            security_score = await self._calculate_security_score()

            # Aktiva alerts
            critical_alerts = [a for a in self.active_alerts if a.severity == ThreatLevel.CRITICAL]
            high_alerts = [a for a in self.active_alerts if a.severity == ThreatLevel.HIGH]

            dashboard = {
                'unified_security_score': security_score,
                'overall_status': 'healthy' if security_score > 0.8 else 'warning' if security_score > 0.6 else 'critical',
                'total_threats': total_threats,
                'active_threats': active_threats,
                'total_alerts': len(self.active_alerts),
                'critical_alerts': len(critical_alerts),
                'high_alerts': len(high_alerts),
                'security_metrics': self.security_metrics,
                'component_status': {
                    'security_manager': security_manager_dashboard.get('status', 'unknown'),
                    'access_control': access_control_dashboard.get('status', 'unknown'),
                    'firewall': firewall_dashboard.get('status', 'unknown')
                },
                'recent_events': [
                    {
                        'event_id': event.event_id,
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'severity': event.severity,
                        'component': event.component
                    }
                    for event in self.security_events[-10:]  # Senaste 10 events
                ],
                'active_alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'title': alert.title,
                        'severity': alert.severity.value,
                        'created_at': alert.created_at.isoformat(),
                        'acknowledged': alert.acknowledged
                    }
                    for alert in self.active_alerts[:10]  # Senaste 10 alerts
                ],
                'supported_operations': [op.value for op in SecurityOperation],
                'supported_permissions': [perm.value for perm in Permission],
                'supported_roles': [role.value for role in Role],
                'supported_threat_types': [tt.value for tt in ThreatType],
                'timestamp': datetime.now().isoformat()
            }

            return dashboard

        except Exception as e:
            logger.error(f"Unified security dashboard misslyckades: {e}")
            return {'error': str(e)}

    async def _calculate_security_score(self) -> float:
        """Beräkna unified security score."""
        try:
            # Faktorera in olika komponenter
            component_scores = {
                'threat_level': 1.0 - (len([e for e in self.security_events
                                          if e.severity == 'critical']) * 0.3),
                'alert_backlog': 1.0 - (len([a for a in self.active_alerts
                                           if not a.acknowledged]) * 0.1),
                'incident_response': 1.0 - (self.security_metrics['total_events'] -
                                          self.security_metrics['incidents_resolved']) * 0.05,
                'false_positive_ratio': 1.0 - (self.security_metrics['false_positives'] /
                                             max(self.security_metrics['total_events'], 1)) * 0.2
            }

            # Beräkna genomsnitt
            security_score = sum(component_scores.values()) / len(component_scores)

            # Begränsa till 0.0-1.0
            security_score = max(0.0, min(1.0, security_score))

            return round(security_score, 2)

        except Exception as e:
            logger.error(f"Security score calculation misslyckades: {e}")
            return 0.5

    async def acknowledge_alert(self, alert_id: str, user_id: str, notes: str = "") -> bool:
        """Erkänn alert."""
        try:
            for alert in self.active_alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_by = user_id
                    alert.acknowledged_at = datetime.now()
                    alert.resolution_notes = notes

                    logger.info(f"Alert {alert_id} erkänd av {user_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Alert acknowledgment misslyckades för {alert_id}: {e}")
            return False

    async def create_security_incident(self, title: str, description: str,
                                     severity: ThreatLevel, affected_components: List[str],
                                     reported_by: str) -> str:
        """Skapa säkerhetsincident."""
        try:
            incident_id = f"incident_{datetime.now().timestamp()}"

            # Skapa security event
            event = SecurityEvent(
                event_id=incident_id,
                event_type=SecurityEventType.SECURITY_INCIDENT,
                timestamp=datetime.now(),
                severity=severity.value,
                component='security_integration',
                details={
                    'title': title,
                    'description': description,
                    'affected_components': affected_components,
                    'reported_by': reported_by
                }
            )

            self.security_events.append(event)

            # Skapa alert
            alert = SecurityAlert(
                alert_id=f"alert_{incident_id}",
                title=f"Security Incident: {title}",
                description=description,
                severity=severity,
                affected_components=affected_components,
                recommended_actions=[
                    "Investigate incident details",
                    "Assess impact on systems",
                    "Implement remediation measures",
                    "Update security policies if needed"
                ],
                created_at=datetime.now()
            )

            self.active_alerts.append(alert)

            logger.warning(f"Security incident skapad: {title} av {reported_by}")
            return incident_id

        except Exception as e:
            logger.error(f"Security incident creation misslyckades: {e}")
            return ""

    async def health_check(self) -> Dict[str, Any]:
        """Utför health check på security integration."""
        try:
            security_manager_health = await self.security_manager.health_check()
            access_control_health = await self.access_control.health_check()
            firewall_health = await self.firewall.health_check()

            overall_status = 'healthy'
            if any(h.get('status') != 'healthy' for h in [security_manager_health, access_control_health, firewall_health]):
                overall_status = 'degraded'

            return {
                'service': 'web3_security_integration',
                'status': overall_status,
                'security_manager': security_manager_health.get('status', 'unknown'),
                'access_control': access_control_health.get('status', 'unknown'),
                'firewall': firewall_health.get('status', 'unknown'),
                'monitoring_active': self.monitoring_active,
                'total_events': len(self.security_events),
                'active_alerts': len(self.active_alerts),
                'security_score': await self._calculate_security_score(),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'service': 'web3_security_integration',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }