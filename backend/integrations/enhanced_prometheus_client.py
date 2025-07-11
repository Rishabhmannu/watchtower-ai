import asyncio
import aiohttp
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass
from enum import Enum
import time

# Import our service registry for service-aware querying
from core.service_registry import BankingServiceRegistry
from models.service_models import ServiceCategory, ServiceInfo

# Set up logging
logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics for different analysis"""
    HEALTH = "health"
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    ERROR = "error"
    BUSINESS = "business"


@dataclass
class MetricTemplate:
    """Template for service-specific metrics"""
    name: str
    promql_query: str
    description: str
    unit: str
    metric_type: MetricType
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    higher_is_better: bool = True


@dataclass
class QueryResult:
    """Structured result from Prometheus query"""
    query: str
    success: bool
    data: Any
    timestamp: datetime
    execution_time_ms: float
    error_message: Optional[str] = None


class EnhancedPrometheusClient:
    """
    Enhanced Prometheus client with advanced capabilities for banking system monitoring
    Builds upon the existing PrometheusClient with:
    - Multi-service querying
    - Service-specific metric templates  
    - Intelligent caching
    - Error handling and retries
    - Metric correlation
    """

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.service_registry = BankingServiceRegistry()

        # Caching for frequently accessed metrics
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(seconds=30)  # 30-second cache TTL

        # Connection settings
        self._timeout = aiohttp.ClientTimeout(total=30)
        self._retry_attempts = 3
        self._retry_delay = 1.0

        # Initialize service-specific metric templates
        self._metric_templates = self._initialize_metric_templates()

        logger.info("Enhanced Prometheus client initialized")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper configuration"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool limit
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self._timeout,
                headers={"User-Agent": "WatchTower-AI/1.0"}
            )
        return self.session

    def _initialize_metric_templates(self) -> Dict[str, List[MetricTemplate]]:
        """Initialize service-specific metric templates for banking system - FINAL CORRECTED VERSION"""
        templates = {
            # Core Banking Services Templates (UNCHANGED - these work correctly)
            "core_banking": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="banking-services", instance="{host}:{port}"}}',
                    description="Service availability status",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="request_rate",
                    promql_query='rate(http_requests_total{{job="banking-services", instance="{host}:{port}"}}[5m])',
                    description="HTTP requests per second",
                    unit="req/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="response_time_p95",
                    promql_query='histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="banking-services", instance="{host}:{port}"}}[5m]))',
                    description="95th percentile response time",
                    unit="seconds",
                    metric_type=MetricType.PERFORMANCE,
                    threshold_warning=0.5,
                    threshold_critical=1.0,
                    higher_is_better=False
                ),
                MetricTemplate(
                    name="error_rate",
                    promql_query='rate(http_requests_total{{job="banking-services", instance="{host}:{port}", status=~"5.."}}[5m])',
                    description="HTTP 5xx error rate",
                    unit="errors/s",
                    metric_type=MetricType.ERROR,
                    threshold_warning=0.01,
                    threshold_critical=0.05,
                    higher_is_better=False
                )
            ],
            
            # ML Detection Services Templates - Just health check for now
            "ml_detection": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="ML service availability",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                )
            ],
            
            # Infrastructure Services Templates - Just health check
            "infrastructure": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Infrastructure service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                )
            ],
            
            # Messaging Templates - Use global banking metrics
            "messaging": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Messaging service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="messages_published_rate",
                    promql_query='rate(banking_messages_published_total[5m])',
                    description="Messages published per second (global)",
                    unit="msg/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="messages_consumed_rate",
                    promql_query='rate(banking_messages_consumed_total[5m])',
                    description="Messages consumed per second (global)",
                    unit="msg/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="unprocessed_messages",
                    promql_query='banking_unprocessed_messages',
                    description="Unprocessed messages count (global)",
                    unit="messages",
                    metric_type=MetricType.PERFORMANCE,
                    threshold_warning=500,
                    threshold_critical=2000,
                    higher_is_better=False
                )
            ],
            
            # Cache & Performance Templates - Use global cache metrics (WORKING)
            "cache_performance": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Cache service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="cache_hit_ratio",
                    promql_query='banking_cache_hits_total / (banking_cache_hits_total + banking_cache_misses_total) * 100',
                    description="Cache hit ratio (global)",
                    unit="percentage",
                    metric_type=MetricType.PERFORMANCE,
                    threshold_warning=80,
                    threshold_critical=60
                ),
                MetricTemplate(
                    name="cache_operations_rate",
                    promql_query='rate(cache_load_operations_total[5m])',
                    description="Cache operations per second (global)",
                    unit="ops/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="cache_active_entries",
                    promql_query='banking_cache_active_entries',
                    description="Active cache entries",
                    unit="entries",
                    metric_type=MetricType.RESOURCE
                )
            ],
            
            # Database Storage Templates - Use global DB metrics
            "database_storage": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Database service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="db_pool_utilization",
                    promql_query='banking_db_pool_utilization_percent',
                    description="Database connection pool utilization (global)",
                    unit="percentage",
                    metric_type=MetricType.RESOURCE,
                    threshold_warning=80,
                    threshold_critical=95,
                    higher_is_better=False
                ),
                MetricTemplate(
                    name="db_active_connections",
                    promql_query='banking_db_pool_connections_active',
                    description="Active database connections (global)",
                    unit="connections",
                    metric_type=MetricType.RESOURCE
                ),
                MetricTemplate(
                    name="anomaly_cpu_percent",
                    promql_query='anomaly_generator_cpu_percent',
                    description="Anomaly generator CPU usage (global)",
                    unit="percentage",
                    metric_type=MetricType.RESOURCE,
                    threshold_warning=70,
                    threshold_critical=90,
                    higher_is_better=False
                )
            ],
            
            # Kubernetes Templates - Use global K8s metrics
            "kubernetes": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Kubernetes service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="pod_count",
                    promql_query='k8s_pod_count_total',
                    description="Total pod count (global)",
                    unit="pods",
                    metric_type=MetricType.RESOURCE
                ),
                MetricTemplate(
                    name="scaling_events_rate",
                    promql_query='rate(k8s_scaling_events_total[5m])',
                    description="Pod scaling events per second (global)",
                    unit="events/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="deployment_replicas",
                    promql_query='k8s_deployment_replicas',
                    description="Deployment replica count (global)",
                    unit="replicas",
                    metric_type=MetricType.RESOURCE
                )
            ],
            
            # Tracing Templates - Use global tracing metrics
            "tracing": [
                MetricTemplate(
                    name="service_health",
                    promql_query='up{{job="{prometheus_job}"}}',
                    description="Tracing service health",
                    unit="boolean",
                    metric_type=MetricType.HEALTH,
                    threshold_critical=0.5
                ),
                MetricTemplate(
                    name="traces_generated_rate",
                    promql_query='rate(traces_generated_total[5m])',
                    description="Traces generated per second (global)",
                    unit="traces/s",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="active_trace_generation",
                    promql_query='active_trace_generation',
                    description="Active trace generation sessions (global)",
                    unit="sessions",
                    metric_type=MetricType.PERFORMANCE
                ),
                MetricTemplate(
                    name="trace_patterns_rate",
                    promql_query='trace_patterns_per_minute / 60',
                    description="Trace patterns per second",
                    unit="patterns/s",
                    metric_type=MetricType.PERFORMANCE
                )
            ]
        }
        
        return templates

    async def query_metric(self, query: str) -> Dict[str, Any]:
        """Simple query method that returns a dictionary for API compatibility"""
        result = await self.query_metric_with_retry(query)
        
        if result.success:
            return {
                "status": "success",
                "data": result.data,
                "timestamp": result.timestamp.isoformat(),
                "execution_time_ms": result.execution_time_ms
            }
        else:
            return {
                "status": "error",
                "error": result.error_message,
                "timestamp": result.timestamp.isoformat(),
                "execution_time_ms": result.execution_time_ms
            }

    async def query_metric_with_retry(self, query: str) -> QueryResult:
        """Query Prometheus with retry logic and enhanced error handling"""
        start_time = time.time()

        # Check cache first
        cache_key = f"query:{query}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_ttl:
                execution_time = (time.time() - start_time) * 1000
                logger.debug(f"Cache hit for query: {query}")
                return QueryResult(
                    query=query,
                    success=True,
                    data=cached_data,
                    timestamp=cached_time,
                    execution_time_ms=execution_time
                )

        # Attempt query with retries
        last_error = None
        for attempt in range(self._retry_attempts):
            try:
                session = await self._get_session()
                url = f"{self.base_url}/api/v1/query"
                params = {"query": query}

                async with session.get(url, params=params) as response:
                    execution_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        timestamp = datetime.now()

                        # Cache successful results
                        self._cache[cache_key] = (data, timestamp)

                        logger.debug(f"Prometheus query successful: {query}")
                        return QueryResult(
                            query=query,
                            success=True,
                            data=data,
                            timestamp=timestamp,
                            execution_time_ms=execution_time
                        )
                    else:
                        error_text = await response.text()
                        last_error = f"HTTP {response.status}: {error_text}"

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Query attempt {attempt + 1} failed: {e}")

                if attempt < self._retry_attempts - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        # All attempts failed
        execution_time = (time.time() - start_time) * 1000
        logger.error(
            f"Query failed after {self._retry_attempts} attempts: {query}")

        return QueryResult(
            query=query,
            success=False,
            data=None,
            timestamp=datetime.now(),
            execution_time_ms=execution_time,
            error_message=last_error
        )

    async def query_service_metrics(self, service_name: str, metric_types: Optional[List[MetricType]] = None) -> Dict[str, Any]:
        """Query comprehensive metrics for a specific service"""
        service = self.service_registry.get_service(service_name)
        if not service:
            raise ValueError(f"Service '{service_name}' not found in registry")

        # Get appropriate metric templates for service category
        category_key = service.category.value
        templates = self._metric_templates.get(category_key, [])

        # Filter by metric types if specified
        if metric_types:
            templates = [t for t in templates if t.metric_type in metric_types]

        # Execute all metric queries concurrently
        tasks = []
        for template in templates:
            # Format the query with service-specific values
            formatted_query = template.promql_query.format(
                host=service.host,
                port=service.port,
                service_name=service.name,
                prometheus_job=service.prometheus_job
            )
            tasks.append(self.query_metric_with_retry(formatted_query))

        # Wait for all queries to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        service_metrics = {
            "service": service.name,
            "display_name": service.display_name,
            "category": service.category.value,
            "metrics": {},
            "overall_health": "unknown",
            "query_timestamp": datetime.now().isoformat()
        }

        health_scores = []
        for i, (template, result) in enumerate(zip(templates, results)):
            if isinstance(result, Exception):
                service_metrics["metrics"][template.name] = {
                    "error": str(result),
                    "template": template.description
                }
                continue

            if not result.success:
                service_metrics["metrics"][template.name] = {
                    "error": result.error_message,
                    "template": template.description
                }
                continue

            # Extract metric value
            metric_value = self._extract_metric_value(result.data)
            health_status = self._evaluate_metric_health(
                metric_value, template)

            service_metrics["metrics"][template.name] = {
                "value": metric_value,
                "unit": template.unit,
                "description": template.description,
                "health_status": health_status,
                "execution_time_ms": result.execution_time_ms,
                "thresholds": {
                    "warning": template.threshold_warning,
                    "critical": template.threshold_critical
                }
            }

            # Calculate health score for overall health
            if health_status == "healthy":
                health_scores.append(1.0)
            elif health_status == "warning":
                health_scores.append(0.7)
            elif health_status == "critical":
                health_scores.append(0.3)
            else:
                health_scores.append(0.5)  # unknown

        # Calculate overall health
        if health_scores:
            avg_health = sum(health_scores) / len(health_scores)
            if avg_health >= 0.8:
                service_metrics["overall_health"] = "healthy"
            elif avg_health >= 0.6:
                service_metrics["overall_health"] = "warning"
            else:
                service_metrics["overall_health"] = "critical"

        return service_metrics

    async def query_category_health(self, category: ServiceCategory) -> Dict[str, Any]:
        """Get health summary for all services in a category"""
        services = self.service_registry.get_services_by_category(category)

        # Query health metrics for all services concurrently
        tasks = [
            self.query_service_metrics(service.name, [MetricType.HEALTH])
            for service in services
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        category_summary = {
            "category": category.value,
            "total_services": len(services),
            "services": {},
            "health_distribution": {"healthy": 0, "warning": 0, "critical": 0, "unknown": 0},
            "timestamp": datetime.now().isoformat()
        }

        for service, result in zip(services, results):
            if isinstance(result, Exception):
                category_summary["services"][service.name] = {
                    "status": "error",
                    "error": str(result)
                }
                category_summary["health_distribution"]["unknown"] += 1
            else:
                overall_health = result.get("overall_health", "unknown")
                category_summary["services"][service.name] = {
                    "status": overall_health,
                    "display_name": service.display_name,
                    "port": service.port
                }
                category_summary["health_distribution"][overall_health] += 1

        # Calculate category health percentage
        total = category_summary["total_services"]
        healthy_count = category_summary["health_distribution"]["healthy"]
        category_summary["health_percentage"] = (
            healthy_count / total * 100) if total > 0 else 0

        return category_summary

    async def query_multiple_services(self, service_names: List[str], metric_types: Optional[List[MetricType]] = None) -> Dict[str, Any]:
        """Query metrics for multiple services concurrently"""
        tasks = [
            self.query_service_metrics(service_name, metric_types)
            for service_name in service_names
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        multi_service_data = {
            "services": {},
            "summary": {
                "total_queried": len(service_names),
                "successful": 0,
                "failed": 0
            },
            "timestamp": datetime.now().isoformat()
        }

        for service_name, result in zip(service_names, results):
            if isinstance(result, Exception):
                multi_service_data["services"][service_name] = {
                    "error": str(result)
                }
                multi_service_data["summary"]["failed"] += 1
            else:
                multi_service_data["services"][service_name] = result
                multi_service_data["summary"]["successful"] += 1

        return multi_service_data

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview across all categories"""
        categories = self.service_registry.get_categories()

        # Query all categories concurrently
        tasks = [self.query_category_health(
            category) for category in categories]
        category_results = await asyncio.gather(*tasks, return_exceptions=True)

        system_overview = {
            "total_services": self.service_registry.get_services_count(),
            "categories": {},
            "overall_health": {
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0
            },
            "timestamp": datetime.now().isoformat()
        }

        for category, result in zip(categories, category_results):
            if isinstance(result, Exception):
                system_overview["categories"][category.value] = {
                    "error": str(result)
                }
            else:
                system_overview["categories"][category.value] = result

                # Aggregate health counts
                health_dist = result.get("health_distribution", {})
                for status, count in health_dist.items():
                    system_overview["overall_health"][status] += count

        # Calculate overall system health percentage
        total_services = sum(system_overview["overall_health"].values())
        healthy_services = system_overview["overall_health"]["healthy"]
        system_overview["system_health_percentage"] = (
            healthy_services / total_services * 100 if total_services > 0 else 0
        )

        return system_overview

    def _extract_metric_value(self, prometheus_data: Dict) -> Optional[float]:
        """Extract numeric value from Prometheus response"""
        try:
            if prometheus_data.get("status") != "success":
                return None

            result = prometheus_data.get("data", {}).get("result", [])
            if not result:
                return None

            # Get the first result's value
            value_pair = result[0].get("value", [])
            if len(value_pair) < 2:
                return None

            return float(value_pair[1])

        except (ValueError, TypeError, KeyError, IndexError):
            return None

    def _evaluate_metric_health(self, value: Optional[float], template: MetricTemplate) -> str:
        """Evaluate metric health based on thresholds"""
        if value is None:
            return "unknown"

        # For metrics where higher is better (e.g., cache hit ratio)
        if template.higher_is_better:
            if template.threshold_critical and value < template.threshold_critical:
                return "critical"
            elif template.threshold_warning and value < template.threshold_warning:
                return "warning"
            else:
                return "healthy"

        # For metrics where lower is better (e.g., response time, error rate)
        else:
            if template.threshold_critical and value > template.threshold_critical:
                return "critical"
            elif template.threshold_warning and value > template.threshold_warning:
                return "warning"
            else:
                return "healthy"

    async def check_prometheus_connection(self) -> bool:
        """Check if Prometheus is accessible"""
        try:
            session = await self._get_session()
            url = f"{self.base_url}/api/v1/query"
            params = {"query": "up"}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "success"
                return False
        except Exception as e:
            logger.error(f"Prometheus connection check failed: {e}")
            return False

    async def clear_cache(self):
        """Clear the metric cache"""
        self._cache.clear()
        logger.info("Prometheus client cache cleared")

    async def close(self):
        """Close the HTTP session and cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        self._cache.clear()
        logger.info("Enhanced Prometheus client closed")
