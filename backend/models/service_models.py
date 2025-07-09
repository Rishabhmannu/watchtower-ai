from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from enum import Enum
from datetime import datetime


class ServiceCategory(str, Enum):
    """Service categories based on your banking system architecture"""
    CORE_BANKING = "core_banking"
    ML_DETECTION = "ml_detection"
    INFRASTRUCTURE = "infrastructure"
    MESSAGING = "messaging"
    CACHE_PERFORMANCE = "cache_performance"
    DATABASE_STORAGE = "database_storage"
    KUBERNETES = "kubernetes"
    TRACING = "tracing"


class ServiceStatus(str, Enum):
    """Service health status"""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


class ServiceInfo(BaseModel):
    """Individual service information model"""
    name: str = Field(..., description="Service name")
    display_name: str = Field(..., description="Human-readable service name")
    host: str = Field(..., description="Service hostname or container name")
    port: int = Field(..., description="Service port number")
    category: ServiceCategory = Field(..., description="Service category")
    description: str = Field(..., description="Service description")
    prometheus_job: str = Field(...,
                                description="Prometheus job name for this service")
    metrics_path: str = Field(
        default="/metrics", description="Metrics endpoint path")
    scrape_interval: str = Field(
        default="15s", description="Prometheus scrape interval")
    health_endpoint: Optional[str] = Field(
        None, description="Health check endpoint")
    dependencies: List[str] = Field(
        default_factory=list, description="Service dependencies")
    tags: List[str] = Field(default_factory=list,
                            description="Service tags for filtering")


class ServiceHealth(BaseModel):
    """Service health status model"""
    service_name: str
    status: ServiceStatus
    last_seen: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metrics_available: bool = False


class ServiceMetrics(BaseModel):
    """Service metrics summary model"""
    service_name: str
    cpu_usage_percent: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    request_rate_per_min: Optional[float] = None
    error_rate_percent: Optional[float] = None
    response_time_p95_ms: Optional[float] = None
    last_updated: datetime


class CategorySummary(BaseModel):
    """Category-level summary model"""
    category: ServiceCategory
    total_services: int
    healthy_services: int
    degraded_services: int
    down_services: int
    category_health_score: float = Field(
        description="0-100 health score for category")


class ServiceRegistry(BaseModel):
    """Complete service registry model"""
    services: Dict[str, ServiceInfo] = Field(default_factory=dict)
    categories: Dict[ServiceCategory, List[str]] = Field(default_factory=dict)
    total_services: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

    def add_service(self, service: ServiceInfo) -> None:
        """Add a service to the registry"""
        self.services[service.name] = service

        # Update category mapping
        if service.category not in self.categories:
            self.categories[service.category] = []
        if service.name not in self.categories[service.category]:
            self.categories[service.category].append(service.name)

        self.total_services = len(self.services)
        self.last_updated = datetime.now()

    def get_services_by_category(self, category: ServiceCategory) -> List[ServiceInfo]:
        """Get all services in a specific category"""
        service_names = self.categories.get(category, [])
        return [self.services[name] for name in service_names if name in self.services]

    def get_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get a specific service by name"""
        return self.services.get(service_name)

    def get_all_categories(self) -> List[ServiceCategory]:
        """Get all available categories"""
        return list(self.categories.keys())

    def search_services(self, query: str) -> List[ServiceInfo]:
        """Search services by name, description, or tags"""
        query_lower = query.lower()
        results = []

        for service in self.services.values():
            if (query_lower in service.name.lower() or
                query_lower in service.description.lower() or
                    any(query_lower in tag.lower() for tag in service.tags)):
                results.append(service)

        return results
