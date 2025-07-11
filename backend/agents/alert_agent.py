"""
Health Agent for Proactive Monitoring
File: backend/agents/alert_agent.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .base_agent import BaseAgent, AgentType, AgentMessage, MessageType, create_message
from core.service_registry import BankingServiceRegistry
from core.dashboard_registry import DashboardRegistry
from integrations.enhanced_prometheus_client import EnhancedPrometheusClient

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """Health metric data structure"""
    service_name: str
    metric_name: str
    current_value: float
    threshold_warning: Optional[float]
    threshold_critical: Optional[float]
    status: HealthStatus
    timestamp: datetime
    trend: str  # "improving", "stable", "degrading"


@dataclass
class HealthAlert:
    """Health alert data structure"""
    alert_id: str
    service_name: str
    category: str
    severity: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False


class HealthAgent(BaseAgent):
    """Proactive Health Monitoring Agent"""

    def __init__(self, agent_id: str = "health_agent"):
        super().__init__(agent_id, AgentType.HEALTH)

        # Initialize components
        self.service_registry = BankingServiceRegistry()
        self.dashboard_registry = DashboardRegistry()
        self.prometheus_client = EnhancedPrometheusClient()

        # Health monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.health_history: Dict[str, List[HealthMetric]] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.alert_cooldown = 300  # 5 minutes

        # Health baseline learning
        self.baseline_data: Dict[str, Dict[str, float]] = {}
        self.learning_period = 24 * 60 * 60  # 24 hours

        # Initialize health baselines
        self.initialize_health_baselines()

        self.log_info("Health Agent initialized with proactive monitoring")

    def initialize_health_baselines(self):
        """Initialize health baselines for all services"""
        try:
            for service_name, service_info in self.service_registry.get_all_services().items():
                self.baseline_data[service_name] = {
                    "response_time_avg": 0.0,
                    "response_time_p95": 0.0,
                    "error_rate": 0.0,
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "last_updated": datetime.now().timestamp()
                }
                self.health_history[service_name] = []

            self.log_info(
                f"Initialized health baselines for {len(self.baseline_data)} services")
        except Exception as e:
            self.log_error(f"Error initializing health baselines: {e}")

    async def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming messages"""
        try:
            if message.message_type == MessageType.QUERY:
                return await self._handle_health_query(message)
            elif message.message_type == MessageType.STATUS:
                return await self._handle_status_request(message)
            else:
                self.log_warning(
                    f"Unknown message type: {message.message_type}")
                return None
        except Exception as e:
            self.log_error(f"Error processing message: {e}")
            return None

    async def background_task(self):
        """Continuous health monitoring background task"""
        try:
            # Perform health checks
            await self._monitor_all_services()

            # Check for alerts
            await self._evaluate_alerts()

            # Update baselines
            await self._update_baselines()

            # Wait for next monitoring cycle
            await asyncio.sleep(self.monitoring_interval)

        except Exception as e:
            self.log_error(f"Error in health monitoring background task: {e}")

    async def _monitor_all_services(self):
        """Monitor health of all services"""
        try:
            # Get comprehensive system overview
            system_overview = await self.prometheus_client.get_system_overview()

            # Monitor each service category
            for category_name, category_data in system_overview.get("categories", {}).items():
                await self._monitor_category(category_name, category_data)

            # Monitor critical metrics
            await self._monitor_critical_metrics()

        except Exception as e:
            self.log_error(f"Error monitoring all services: {e}")

    async def _monitor_category(self, category_name: str, category_data: Dict[str, Any]):
        """Monitor services in a specific category"""
        try:
            if "error" in category_data:
                return

            services_data = category_data.get("services", {})

            for service_name, service_info in services_data.items():
                status = service_info.get("status", "unknown")

                # Create health metric
                health_metric = HealthMetric(
                    service_name=service_name,
                    metric_name="service_health",
                    current_value=1.0 if status == "healthy" else 0.0,
                    threshold_warning=1.0,
                    threshold_critical=0.0,
                    status=HealthStatus(status if status in [
                                        "healthy", "warning", "critical"] else "unknown"),
                    timestamp=datetime.now(),
                    trend=self._calculate_trend(
                        service_name, "service_health", 1.0 if status == "healthy" else 0.0)
                )

                # Store in history
                self._store_health_metric(health_metric)

                # Check if alert is needed
                if health_metric.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                    await self._create_alert(health_metric)

        except Exception as e:
            self.log_error(f"Error monitoring category {category_name}: {e}")

    async def _monitor_critical_metrics(self):
        """Monitor critical system-wide metrics"""
        try:
            critical_queries = {
                "cache_hit_ratio": "banking_cache_hits_total / (banking_cache_hits_total + banking_cache_misses_total) * 100",
                "database_connections": "banking_db_pool_connections_active",
                "unprocessed_messages": "banking_unprocessed_messages",
                "pod_count": "k8s_pod_count_total"
            }

            for metric_name, query in critical_queries.items():
                try:
                    result = await self.prometheus_client.query_metric(query)

                    if result.get("status") == "success":
                        value = self._extract_metric_value(result)
                        if value is not None:
                            # Determine health status based on metric
                            status = self._evaluate_metric_health(
                                metric_name, value)

                            health_metric = HealthMetric(
                                service_name="system",
                                metric_name=metric_name,
                                current_value=value,
                                threshold_warning=self._get_threshold(
                                    metric_name, "warning"),
                                threshold_critical=self._get_threshold(
                                    metric_name, "critical"),
                                status=status,
                                timestamp=datetime.now(),
                                trend=self._calculate_trend(
                                    "system", metric_name, value)
                            )

                            self._store_health_metric(health_metric)

                            if status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                                await self._create_alert(health_metric)

                except Exception as e:
                    self.log_error(
                        f"Error monitoring metric {metric_name}: {e}")

        except Exception as e:
            self.log_error(f"Error monitoring critical metrics: {e}")

    def _extract_metric_value(self, result: Dict[str, Any]) -> Optional[float]:
        """Extract numeric value from Prometheus response"""
        try:
            data = result.get("data", {})
            inner_data = data.get("data", {})
            result_data = inner_data.get("result", [])

            if result_data:
                value = result_data[0].get("value", [])
                if len(value) >= 2:
                    return float(value[1])
        except Exception:
            pass
        return None

    def _evaluate_metric_health(self, metric_name: str, value: float) -> HealthStatus:
        """Evaluate health status based on metric value"""
        thresholds = {
            "cache_hit_ratio": {"warning": 80, "critical": 60},
            "database_connections": {"warning": 80, "critical": 95},
            "unprocessed_messages": {"warning": 100, "critical": 500},
            "pod_count": {"warning": 50, "critical": 100}
        }

        if metric_name in thresholds:
            warning_threshold = thresholds[metric_name]["warning"]
            critical_threshold = thresholds[metric_name]["critical"]

            if metric_name == "cache_hit_ratio":
                # Higher is better
                if value < critical_threshold:
                    return HealthStatus.CRITICAL
                elif value < warning_threshold:
                    return HealthStatus.WARNING
            else:
                # Lower is better
                if value > thresholds[metric_name]["critical"]:
                    return HealthStatus.CRITICAL
                elif value > warning_threshold:
                    return HealthStatus.WARNING

        return HealthStatus.HEALTHY

    def _get_threshold(self, metric_name: str, threshold_type: str) -> Optional[float]:
        """Get threshold value for metric"""
        thresholds = {
            "cache_hit_ratio": {"warning": 80, "critical": 60},
            "database_connections": {"warning": 80, "critical": 95},
            "unprocessed_messages": {"warning": 100, "critical": 500},
            "pod_count": {"warning": 50, "critical": 100}
        }

        return thresholds.get(metric_name, {}).get(threshold_type)

    def _calculate_trend(self, service_name: str, metric_name: str, current_value: float) -> str:
        """Calculate trend for a metric"""
        try:
            if service_name not in self.health_history:
                return "stable"

            recent_metrics = [
                m for m in self.health_history[service_name]
                if m.metric_name == metric_name and
                m.timestamp > datetime.now() - timedelta(minutes=15)
            ]

            if len(recent_metrics) < 3:
                return "stable"

            # Calculate trend
            values = [m.current_value for m in recent_metrics]
            avg_first_half = sum(values[:len(values)//2]) / (len(values)//2)
            avg_second_half = sum(
                values[len(values)//2:]) / (len(values) - len(values)//2)

            if avg_second_half > avg_first_half * 1.1:
                return "improving"
            elif avg_second_half < avg_first_half * 0.9:
                return "degrading"
            else:
                return "stable"

        except Exception as e:
            self.log_error(f"Error calculating trend: {e}")
            return "stable"

    def _store_health_metric(self, metric: HealthMetric):
        """Store health metric in history"""
        if metric.service_name not in self.health_history:
            self.health_history[metric.service_name] = []

        self.health_history[metric.service_name].append(metric)

        # Keep only last 100 metrics per service
        if len(self.health_history[metric.service_name]) > 100:
            self.health_history[metric.service_name].pop(0)

    async def _create_alert(self, metric: HealthMetric):
        """Create health alert"""
        try:
            alert_id = f"{metric.service_name}_{metric.metric_name}_{int(metric.timestamp.timestamp())}"

            # Check if similar alert already exists (cooldown)
            existing_alert = self._find_similar_alert(metric)
            if existing_alert:
                return

            # Create alert
            alert = HealthAlert(
                alert_id=alert_id,
                service_name=metric.service_name,
                category=self._get_service_category(metric.service_name),
                severity=metric.status.value,
                message=self._generate_alert_message(metric),
                details={
                    "metric_name": metric.metric_name,
                    "current_value": metric.current_value,
                    "threshold_warning": metric.threshold_warning,
                    "threshold_critical": metric.threshold_critical,
                    "trend": metric.trend
                },
                timestamp=metric.timestamp
            )

            self.active_alerts[alert_id] = alert

            # Send alert message
            alert_message = create_message(
                sender=self.agent_id,
                recipient="analysis_agent",
                message_type=MessageType.ALERT,
                content={
                    "alert": alert.__dict__,
                    "metric": metric.__dict__
                },
                priority=3 if metric.status == HealthStatus.CRITICAL else 2
            )

            await self.send_message(alert_message)

            self.log_info(f"Created alert: {alert.message}")

        except Exception as e:
            self.log_error(f"Error creating alert: {e}")

    def _find_similar_alert(self, metric: HealthMetric) -> Optional[HealthAlert]:
        """Find similar active alert within cooldown period"""
        cooldown_time = datetime.now() - timedelta(seconds=self.alert_cooldown)

        for alert in self.active_alerts.values():
            if (alert.service_name == metric.service_name and
                alert.details.get("metric_name") == metric.metric_name and
                    alert.timestamp > cooldown_time):
                return alert

        return None

    def _get_service_category(self, service_name: str) -> str:
        """Get service category"""
        try:
            service = self.service_registry.get_service(service_name)
            if service:
                return service.category.value
        except Exception:
            pass
        return "unknown"

    def _generate_alert_message(self, metric: HealthMetric) -> str:
        """Generate human-readable alert message"""
        status_emoji = {
            HealthStatus.CRITICAL: "🚨",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.HEALTHY: "✅"
        }

        emoji = status_emoji.get(metric.status, "❓")

        if metric.metric_name == "service_health":
            return f"{emoji} {metric.service_name} service is {metric.status.value}"
        elif metric.metric_name == "cache_hit_ratio":
            return f"{emoji} Cache hit ratio dropped to {metric.current_value:.1f}% (threshold: {metric.threshold_warning}%)"
        elif metric.metric_name == "database_connections":
            return f"{emoji} Database connections at {metric.current_value} (threshold: {metric.threshold_warning})"
        elif metric.metric_name == "unprocessed_messages":
            return f"{emoji} Unprocessed messages: {metric.current_value} (threshold: {metric.threshold_warning})"
        else:
            return f"{emoji} {metric.service_name} {metric.metric_name}: {metric.current_value} (trend: {metric.trend})"

    async def _evaluate_alerts(self):
        """Evaluate and potentially resolve alerts"""
        try:
            current_time = datetime.now()
            resolved_alerts = []

            for alert_id, alert in self.active_alerts.items():
                # Check if alert should be resolved
                if self._should_resolve_alert(alert, current_time):
                    alert.resolved = True
                    resolved_alerts.append(alert_id)

                    # Send resolution message
                    resolution_message = create_message(
                        sender=self.agent_id,
                        recipient="analysis_agent",
                        message_type=MessageType.STATUS,
                        content={
                            "alert_resolved": alert.__dict__,
                            "resolution_time": current_time.isoformat()
                        },
                        priority=1
                    )

                    await self.send_message(resolution_message)
                    self.log_info(f"Resolved alert: {alert.message}")

            # Remove resolved alerts
            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]

        except Exception as e:
            self.log_error(f"Error evaluating alerts: {e}")

    def _should_resolve_alert(self, alert: HealthAlert, current_time: datetime) -> bool:
        """Check if alert should be resolved"""
        # Auto-resolve after 30 minutes
        if current_time - alert.timestamp > timedelta(minutes=30):
            return True

        # Check if the condition has improved
        service_name = alert.service_name
        metric_name = alert.details.get("metric_name")

        if service_name in self.health_history:
            recent_metrics = [
                m for m in self.health_history[service_name]
                if m.metric_name == metric_name and
                m.timestamp > current_time - timedelta(minutes=5)
            ]

            if recent_metrics:
                latest_metric = recent_metrics[-1]
                if latest_metric.status == HealthStatus.HEALTHY:
                    return True

        return False

    async def _update_baselines(self):
        """Update health baselines based on recent data"""
        try:
            current_time = datetime.now()

            for service_name, metrics in self.health_history.items():
                recent_metrics = [
                    m for m in metrics
                    if current_time - m.timestamp < timedelta(hours=1)
                ]

                if recent_metrics:
                    # Update baseline values
                    if service_name not in self.baseline_data:
                        self.baseline_data[service_name] = {}

                    for metric_name in ["service_health", "cache_hit_ratio", "database_connections"]:
                        metric_values = [
                            m.current_value for m in recent_metrics
                            if m.metric_name == metric_name
                        ]

                        if metric_values:
                            avg_value = sum(metric_values) / len(metric_values)
                            self.baseline_data[service_name][metric_name] = avg_value

                    self.baseline_data[service_name]["last_updated"] = current_time.timestamp(
                    )

        except Exception as e:
            self.log_error(f"Error updating baselines: {e}")

    async def _handle_health_query(self, message: AgentMessage) -> AgentMessage:
        """Handle health query from other agents"""
        try:
            query_content = message.content
            query_type = query_content.get("type")

            if query_type == "service_health":
                service_name = query_content.get("service_name")
                health_data = self._get_service_health(service_name)

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={"health_data": health_data}
                )

            elif query_type == "system_overview":
                overview_data = self._get_system_health_overview()

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={"overview": overview_data}
                )

            elif query_type == "active_alerts":
                alerts_data = [
                    alert.__dict__ for alert in self.active_alerts.values()]

                return create_message(
                    sender=self.agent_id,
                    recipient=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={"alerts": alerts_data}
                )

        except Exception as e:
            self.log_error(f"Error handling health query: {e}")

        return create_message(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content={"error": "Unable to process health query"}
        )

    async def _handle_status_request(self, message: AgentMessage) -> AgentMessage:
        """Handle status request"""
        status_data = self.get_status()
        status_data.update({
            "active_alerts": len(self.active_alerts),
            "monitored_services": len(self.health_history),
            "last_monitoring_cycle": self.last_activity.isoformat()
        })

        return create_message(
            sender=self.agent_id,
            recipient=message.sender,
            message_type=MessageType.RESPONSE,
            content={"status": status_data}
        )

    def _get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health data for specific service"""
        if service_name not in self.health_history:
            return {"error": "Service not found"}

        recent_metrics = [
            m for m in self.health_history[service_name]
            if m.timestamp > datetime.now() - timedelta(hours=1)
        ]

        if not recent_metrics:
            return {"error": "No recent health data"}

        latest_metric = recent_metrics[-1]

        return {
            "service_name": service_name,
            "current_status": latest_metric.status.value,
            "last_updated": latest_metric.timestamp.isoformat(),
            "trend": latest_metric.trend,
            "metrics_count": len(recent_metrics)
        }

    def _get_system_health_overview(self) -> Dict[str, Any]:
        """Get system-wide health overview"""
        total_services = len(self.health_history)
        healthy_services = 0
        warning_services = 0
        critical_services = 0

        for service_name, metrics in self.health_history.items():
            if metrics:
                latest_metric = metrics[-1]
                if latest_metric.status == HealthStatus.HEALTHY:
                    healthy_services += 1
                elif latest_metric.status == HealthStatus.WARNING:
                    warning_services += 1
                elif latest_metric.status == HealthStatus.CRITICAL:
                    critical_services += 1

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "warning_services": warning_services,
            "critical_services": critical_services,
            "health_percentage": (healthy_services / total_services * 100) if total_services > 0 else 0,
            "active_alerts": len(self.active_alerts),
            "last_updated": datetime.now().isoformat()
        }
