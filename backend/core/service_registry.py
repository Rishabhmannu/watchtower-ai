from models.service_models import ServiceInfo, ServiceCategory, ServiceRegistry
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class BankingServiceRegistry:
    """
    Centralized registry for all 31 banking system services
    Based on prometheus.yml configuration and docker container setup
    """

    def __init__(self):
        self.registry = ServiceRegistry()
        self._initialize_services()
        logger.info(
            f"Initialized service registry with {self.registry.total_services} services")

    def _initialize_services(self):
        """Initialize all 31 services from your banking system"""

        # ========================================
        # CORE BANKING SERVICES (6)
        # ========================================
        core_banking_services = [
            ServiceInfo(
                name="api_gateway",
                display_name="API Gateway",
                host="api-gateway",
                port=8080,
                category=ServiceCategory.CORE_BANKING,
                description="Main entry point for all banking API requests",
                prometheus_job="banking-services",
                health_endpoint="/health",
                tags=["gateway", "entry-point", "routing"]
            ),
            ServiceInfo(
                name="account_service",
                display_name="Account Service",
                host="account-service",
                port=8081,
                category=ServiceCategory.CORE_BANKING,
                description="Manages customer accounts and account operations",
                prometheus_job="banking-services",
                health_endpoint="/health",
                dependencies=["banking_mysql"],
                tags=["accounts", "customer-data", "crud"]
            ),
            ServiceInfo(
                name="transaction_service",
                display_name="Transaction Service",
                host="transaction-service",
                port=8082,
                category=ServiceCategory.CORE_BANKING,
                description="Processes financial transactions and transfers",
                prometheus_job="banking-services",
                health_endpoint="/health",
                dependencies=["banking_mysql", "banking_redis"],
                tags=["transactions", "payments", "transfers"]
            ),
            ServiceInfo(
                name="auth_service",
                display_name="Authentication Service",
                host="auth-service",
                port=8083,
                category=ServiceCategory.CORE_BANKING,
                description="Handles user authentication and authorization",
                prometheus_job="banking-services",
                health_endpoint="/health",
                dependencies=["banking_mysql"],
                tags=["auth", "security", "jwt", "login"]
            ),
            ServiceInfo(
                name="notification_service",
                display_name="Notification Service",
                host="notification-service",
                port=8084,
                category=ServiceCategory.CORE_BANKING,
                description="Sends notifications via email, SMS, and push",
                prometheus_job="banking-services",
                health_endpoint="/health",
                dependencies=["banking_rabbitmq"],
                tags=["notifications", "email", "sms", "alerts"]
            ),
            ServiceInfo(
                name="fraud_detection",
                display_name="Fraud Detection Service",
                host="fraud-detection",
                port=8085,
                category=ServiceCategory.CORE_BANKING,
                description="Real-time fraud detection and prevention",
                prometheus_job="banking-services",
                health_endpoint="/health",
                dependencies=["transaction_service", "banking_redis"],
                tags=["fraud", "security", "ml", "prevention"]
            )
        ]

        # ========================================
        # ML & DETECTION SERVICES (5)
        # ========================================
        ml_services = [
            ServiceInfo(
                name="ddos_ml_detection",
                display_name="DDoS ML Detection",
                host="ddos-ml-detection",
                port=5001,
                category=ServiceCategory.ML_DETECTION,
                description="Machine learning-based DDoS attack detection with 4 algorithms",
                prometheus_job="ddos-ml-detection",
                scrape_interval="15s",
                tags=["ddos", "ml", "security", "ensemble"]
            ),
            ServiceInfo(
                name="auto_baselining",
                display_name="Auto-Baselining Service",
                host="auto-baselining",
                port=5002,
                category=ServiceCategory.ML_DETECTION,
                description="Automatic baseline establishment for performance metrics",
                prometheus_job="auto-baselining",
                scrape_interval="15s",
                tags=["baselining", "metrics", "thresholds", "adaptive"]
            ),
            ServiceInfo(
                name="transaction_monitor",
                display_name="Transaction Performance Monitor",
                host="transaction-performance-monitor",
                port=5003,
                category=ServiceCategory.ML_DETECTION,
                description="Monitors transaction performance and patterns",
                prometheus_job="transaction-monitor",
                scrape_interval="10s",
                dependencies=["transaction_service"],
                tags=["monitoring", "transactions", "performance"]
            ),
            ServiceInfo(
                name="performance_aggregator",
                display_name="Performance Aggregator",
                host="performance-aggregator-service",
                port=5004,
                category=ServiceCategory.ML_DETECTION,
                description="Aggregates performance metrics across all banking services",
                prometheus_job="performance-aggregator",
                scrape_interval="15s",
                tags=["aggregation", "metrics", "performance"]
            ),
            ServiceInfo(
                name="anomaly_injector",
                display_name="Anomaly Injector Service",
                host="anomaly-injector-service",
                port=5005,
                category=ServiceCategory.ML_DETECTION,
                description="Testing service for injecting controlled anomalies",
                prometheus_job="anomaly-injector",
                scrape_interval="10s",
                tags=["testing", "anomalies", "chaos-engineering"]
            )
        ]

        # ========================================
        # INFRASTRUCTURE SERVICES (7)
        # ========================================
        infrastructure_services = [
            ServiceInfo(
                name="prometheus",
                display_name="Prometheus",
                host="localhost",
                port=9090,
                category=ServiceCategory.INFRASTRUCTURE,
                description="Metrics collection and monitoring system",
                prometheus_job="prometheus",
                tags=["monitoring", "metrics", "tsdb"]
            ),
            ServiceInfo(
                name="node_exporter",
                display_name="Node Exporter",
                host="node-exporter",
                port=9100,
                category=ServiceCategory.INFRASTRUCTURE,
                description="System and hardware metrics exporter",
                prometheus_job="node-exporter",
                tags=["system", "hardware", "host-metrics"]
            ),
            ServiceInfo(
                name="cadvisor",
                display_name="cAdvisor",
                host="cadvisor",
                port=8080,
                category=ServiceCategory.INFRASTRUCTURE,
                description="Container metrics and resource usage monitoring",
                prometheus_job="cadvisor",
                tags=["containers", "docker", "resources"]
            ),
            ServiceInfo(
                name="redis_exporter",
                display_name="Redis Exporter",
                host="banking-redis-exporter",
                port=9121,
                category=ServiceCategory.INFRASTRUCTURE,
                description="Redis database metrics exporter",
                prometheus_job="redis-exporter",
                scrape_interval="15s",
                dependencies=["banking_redis"],
                tags=["redis", "cache", "database"]
            ),
            ServiceInfo(
                name="postgres_exporter",
                display_name="PostgreSQL Exporter",
                host="banking-postgres-exporter",
                port=9187,
                category=ServiceCategory.INFRASTRUCTURE,
                description="PostgreSQL database metrics exporter",
                prometheus_job="banking-postgresql",
                scrape_interval="15s",
                dependencies=["banking_postgres"],
                tags=["postgresql", "database", "sql"]
            ),
            ServiceInfo(
                name="kafka_exporter",
                display_name="Kafka Exporter",
                host="banking-kafka-exporter",
                port=9308,
                category=ServiceCategory.INFRASTRUCTURE,
                description="Apache Kafka metrics exporter",
                prometheus_job="banking-kafka",
                scrape_interval="15s",
                dependencies=["banking_kafka"],
                tags=["kafka", "streaming", "events"]
            ),
            ServiceInfo(
                name="windows_exporter",
                display_name="Mock Windows Exporter",
                host="mock-windows-exporter",
                port=9182,
                category=ServiceCategory.INFRASTRUCTURE,
                description="Mock Windows IIS metrics for testing",
                prometheus_job="windows-exporter",
                scrape_interval="15s",
                tags=["windows", "iis", "mock", "testing"]
            )
        ]

        # ========================================
        # MESSAGING SERVICES (4)
        # ========================================
        messaging_services = [
            ServiceInfo(
                name="message_producer",
                display_name="Banking Message Producer",
                host="banking-message-producer",
                port=5007,
                category=ServiceCategory.MESSAGING,
                description="Produces messages for banking event queues",
                prometheus_job="banking-message-producer",
                scrape_interval="15s",
                dependencies=["banking_rabbitmq"],
                tags=["messaging", "producer", "events"]
            ),
            ServiceInfo(
                name="message_consumer",
                display_name="Banking Message Consumer",
                host="banking-message-consumer",
                port=5008,
                category=ServiceCategory.MESSAGING,
                description="Consumes and processes banking event messages",
                prometheus_job="banking-message-consumer",
                scrape_interval="15s",
                dependencies=["banking_rabbitmq"],
                tags=["messaging", "consumer", "processing"]
            ),
            ServiceInfo(
                name="banking_rabbitmq",
                display_name="RabbitMQ",
                host="banking-rabbitmq",
                port=15692,
                category=ServiceCategory.MESSAGING,
                description="Message broker for banking system events",
                prometheus_job="banking-rabbitmq",
                scrape_interval="15s",
                tags=["rabbitmq", "broker", "queues"]
            ),
            ServiceInfo(
                name="rabbitmq_monitor",
                display_name="RabbitMQ Queue Monitor",
                host="banking-rabbitmq-monitor",
                port=9418,
                category=ServiceCategory.MESSAGING,
                description="Monitors RabbitMQ queue depths and performance",
                prometheus_job="rabbitmq-queue-monitor",
                scrape_interval="15s",
                dependencies=["banking_rabbitmq"],
                tags=["monitoring", "queues", "depths"]
            )
        ]

        # ========================================
        # CACHE & PERFORMANCE SERVICES (4)
        # ========================================
        cache_services = [
            ServiceInfo(
                name="cache_analyzer",
                display_name="Cache Pattern Analyzer",
                host="banking-cache-analyzer",
                port=5012,
                category=ServiceCategory.CACHE_PERFORMANCE,
                description="Analyzes Redis cache patterns and performance",
                prometheus_job="cache-pattern-analyzer",
                scrape_interval="15s",
                dependencies=["banking_redis"],
                tags=["cache", "analysis", "patterns"]
            ),
            ServiceInfo(
                name="cache_load_generator",
                display_name="Cache Load Generator",
                host="banking-cache-load-generator",
                port=5013,
                category=ServiceCategory.CACHE_PERFORMANCE,
                description="Generates realistic cache load for testing",
                prometheus_job="cache-load-generator",
                scrape_interval="15s",
                dependencies=["banking_redis"],
                tags=["testing", "load", "cache"]
            ),
            ServiceInfo(
                name="cache_proxy",
                display_name="Cache Proxy Service",
                host="cache-proxy-service",
                port=5020,
                category=ServiceCategory.CACHE_PERFORMANCE,
                description="Intelligent caching proxy for banking services",
                prometheus_job="cache-proxy",
                scrape_interval="30s",
                dependencies=["banking_redis"],
                tags=["proxy", "cache", "optimization"]
            ),
            ServiceInfo(
                name="container_monitor",
                display_name="Container Resource Monitor",
                host="banking-container-monitor",
                port=5010,
                category=ServiceCategory.CACHE_PERFORMANCE,
                description="Monitors container resource usage across 18+ services",
                prometheus_job="container-resource-monitor",
                scrape_interval="30s",
                tags=["containers", "resources", "monitoring"]
            )
        ]

        # ========================================
        # DATABASE & STORAGE SERVICES (2)
        # ========================================
        database_services = [
            ServiceInfo(
                name="db_connection_demo",
                display_name="Database Connection Demo",
                host="banking-db-connection-demo",
                port=5006,
                category=ServiceCategory.DATABASE_STORAGE,
                description="Demonstrates database connection pooling patterns",
                prometheus_job="banking-db-demo",
                scrape_interval="15s",
                dependencies=["banking_mysql"],
                tags=["database", "connections", "pooling"]
            ),
            ServiceInfo(
                name="resource_anomaly_generator",
                display_name="Resource Anomaly Generator",
                host="banking-resource-anomaly",
                port=5011,
                category=ServiceCategory.DATABASE_STORAGE,
                description="Generates resource anomalies for testing resilience",
                prometheus_job="resource-anomaly-generator",
                scrape_interval="15s",
                tags=["testing", "anomalies", "resources"]
            )
        ]

        # ========================================
        # KUBERNETES SERVICES (2)
        # ========================================
        kubernetes_services = [
            ServiceInfo(
                name="k8s_resource_monitor",
                display_name="Kubernetes Resource Monitor",
                host="host.docker.internal",
                port=9419,
                category=ServiceCategory.KUBERNETES,
                description="Monitors Kubernetes pod scaling and resource consumption",
                prometheus_job="k8s-resource-monitor",
                scrape_interval="15s",
                tags=["kubernetes", "pods", "scaling"]
            ),
            ServiceInfo(
                name="kube_state_metrics",
                display_name="Kube State Metrics",
                host="host.docker.internal",
                port=8080,
                category=ServiceCategory.KUBERNETES,
                description="Kubernetes API object metrics",
                prometheus_job="kube-state-metrics",
                scrape_interval="30s",
                tags=["kubernetes", "api", "objects"]
            )
        ]

        # ========================================
        # TRACING SERVICES (1)
        # ========================================
        tracing_services = [
            ServiceInfo(
                name="trace_generator",
                display_name="Trace Generator",
                host="trace-generator",
                port=9414,
                category=ServiceCategory.TRACING,
                description="Generates distributed tracing data for banking transactions",
                prometheus_job="trace-generator",
                scrape_interval="10s",
                tags=["tracing", "distributed", "spans"]
            )
        ]

        # Add all services to registry
        all_services = (
            core_banking_services +
            ml_services +
            infrastructure_services +
            messaging_services +
            cache_services +
            database_services +
            kubernetes_services +
            tracing_services
        )

        for service in all_services:
            self.registry.add_service(service)

    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Get all registered services"""
        return self.registry.services

    def get_services_by_category(self, category: ServiceCategory) -> List[ServiceInfo]:
        """Get services by category"""
        return self.registry.get_services_by_category(category)

    def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get specific service by name"""
        return self.registry.get_service(service_name)

    def get_categories(self) -> List[ServiceCategory]:
        """Get all available categories"""
        return self.registry.get_all_categories()

    def search_services(self, query: str) -> List[ServiceInfo]:
        """Search services"""
        return self.registry.search_services(query)

    def get_services_count(self) -> int:
        """Get total number of services"""
        return self.registry.total_services

    def get_category_summary(self, category: ServiceCategory) -> Dict:
        """Get summary for a specific category"""
        services = self.get_services_by_category(category)
        return {
            "category": category.value,
            "total_services": len(services),
            "services": [
                {
                    "name": svc.name,
                    "display_name": svc.display_name,
                    "port": svc.port,
                    "description": svc.description
                }
                for svc in services
            ]
        }
