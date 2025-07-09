from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from integrations.prometheus_client import PrometheusClient
from models.service_models import ServiceCategory
import logging

logger = logging.getLogger(__name__)

# Create router for enhanced metrics endpoints
router = APIRouter(prefix="/api/metrics", tags=["enhanced-metrics"])

# Initialize enhanced Prometheus client
prometheus_client = PrometheusClient()


@router.get("/system/overview", response_model=Dict)
async def get_system_overview():
    """
    Get comprehensive system overview across all 31 services
    Provides health status, performance metrics, and category summaries
    """
    try:
        overview = await prometheus_client.get_system_overview()
        return overview

    except Exception as e:
        logger.error(f"Error getting system overview: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving system overview: {str(e)}")


@router.get("/service/{service_name}", response_model=Dict)
async def get_service_comprehensive_metrics(
    service_name: str,
    metric_types: Optional[List[str]] = Query(
        None, description="Filter by metric types: health, performance, resource, error, business")
):
    """
    Get comprehensive metrics for a specific service
    Uses intelligent service-specific metric templates
    """
    try:
        # Convert string metric types to enums if provided
        parsed_metric_types = None
        if metric_types:
            from integrations.enhanced_prometheus_client import MetricType
            try:
                parsed_metric_types = [MetricType(
                    mt.lower()) for mt in metric_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {str(e)}")

        metrics = await prometheus_client.query_service_metrics(service_name, parsed_metric_types)
        return metrics

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting service metrics for {service_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving service metrics: {str(e)}")


@router.get("/category/{category}", response_model=Dict)
async def get_category_health_summary(category: str):
    """
    Get health summary for all services in a category
    Available categories: core_banking, ml_detection, infrastructure, messaging, 
    cache_performance, database_storage, kubernetes, tracing
    """
    try:
        health_summary = await prometheus_client.query_category_health(category)
        return health_summary

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting category health for {category}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving category health: {str(e)}")


@router.post("/services/batch", response_model=Dict)
async def get_multiple_services_metrics(
    request_body: Dict[str, List[str]]
):
    """
    Query metrics for multiple services concurrently
    Request body format: {"service_names": ["api_gateway", "transaction_service", ...], "metric_types": ["health", "performance"]}
    """
    try:
        service_names = request_body.get("service_names", [])
        metric_types_str = request_body.get("metric_types", [])

        if not service_names:
            raise HTTPException(
                status_code=400, detail="service_names list cannot be empty")

        # Convert metric types to enums if provided
        parsed_metric_types = None
        if metric_types_str:
            from integrations.enhanced_prometheus_client import MetricType
            try:
                parsed_metric_types = [MetricType(
                    mt.lower()) for mt in metric_types_str]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid metric type: {str(e)}")

        batch_metrics = await prometheus_client.query_multiple_services(service_names, parsed_metric_types)
        return batch_metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting batch metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving batch metrics: {str(e)}")


@router.get("/banking/core-services", response_model=Dict)
async def get_core_banking_services_health():
    """
    Quick endpoint to get health status of all 6 core banking services
    Optimized for dashboard widgets and alerts
    """
    try:
        core_services = ["api_gateway", "account_service", "transaction_service",
                         "auth_service", "notification_service", "fraud_detection"]

        batch_metrics = await prometheus_client.query_multiple_services(core_services, ["health"])

        # Simplified response for dashboard consumption
        simplified_response = {
            "summary": {
                "total_services": len(core_services),
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "unknown": 0
            },
            "services": {},
            "timestamp": batch_metrics.get("timestamp")
        }

        for service_name, service_data in batch_metrics.get("services", {}).items():
            if "error" in service_data:
                status = "unknown"
            else:
                status = service_data.get("overall_health", "unknown")

            simplified_response["services"][service_name] = {
                "status": status,
                "display_name": service_data.get("display_name", service_name)
            }
            simplified_response["summary"][status] += 1

        # Calculate health percentage
        total = simplified_response["summary"]["total_services"]
        healthy = simplified_response["summary"]["healthy"]
        simplified_response["summary"]["health_percentage"] = (
            healthy / total * 100) if total > 0 else 0

        return simplified_response

    except Exception as e:
        logger.error(f"Error getting core banking services health: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving core services health: {str(e)}")


@router.get("/ml/detection-services", response_model=Dict)
async def get_ml_detection_services_status():
    """
    Get status of all ML detection services with performance metrics
    Includes DDoS detection, auto-baselining, transaction monitoring, etc.
    """
    try:
        ml_services = ["ddos_ml_detection", "auto_baselining", "transaction_monitor",
                       "performance_aggregator", "anomaly_injector"]

        batch_metrics = await prometheus_client.query_multiple_services(ml_services, ["health", "performance"])

        return {
            "category": "ml_detection",
            "services": batch_metrics.get("services", {}),
            "summary": batch_metrics.get("summary", {}),
            "timestamp": batch_metrics.get("timestamp")
        }

    except Exception as e:
        logger.error(f"Error getting ML detection services status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving ML services status: {str(e)}")


@router.get("/infrastructure/critical", response_model=Dict)
async def get_critical_infrastructure_status():
    """
    Get status of critical infrastructure services
    Includes Prometheus, databases, message queues, etc.
    """
    try:
        infrastructure_services = ["prometheus", "node_exporter", "cadvisor",
                                   "redis_exporter", "postgres_exporter", "kafka_exporter"]

        batch_metrics = await prometheus_client.query_multiple_services(infrastructure_services, ["health", "resource"])

        return {
            "category": "infrastructure",
            "services": batch_metrics.get("services", {}),
            "summary": batch_metrics.get("summary", {}),
            "timestamp": batch_metrics.get("timestamp")
        }

    except Exception as e:
        logger.error(f"Error getting infrastructure status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving infrastructure status: {str(e)}")


@router.get("/query/advanced", response_model=Dict)
async def advanced_prometheus_query(
    query: str,
    use_cache: bool = Query(True, description="Whether to use caching"),
    retry_on_failure: bool = Query(
        True, description="Whether to retry on failure")
):
    """
    Advanced Prometheus query with retry logic, caching, and enhanced error handling
    """
    try:
        if retry_on_failure:
            result = await prometheus_client.query_with_retry(query)
        else:
            result = await prometheus_client.query_metric(query)
            # Convert to consistent format
            result = {
                "query": query,
                "success": result is not None,
                "data": result,
                "timestamp": None,
                "execution_time_ms": None,
                "error_message": None if result else "Query failed"
            }

        return result

    except Exception as e:
        logger.error(f"Error executing advanced query '{query}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Error executing query: {str(e)}")


@router.delete("/cache", response_model=Dict)
async def clear_metrics_cache():
    """
    Clear the Prometheus client cache
    Useful for forcing fresh data retrieval
    """
    try:
        await prometheus_client.clear_cache()
        return {"message": "Metrics cache cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/health/summary", response_model=Dict)
async def get_health_summary():
    """
    Get quick health summary across all service categories
    Optimized for real-time monitoring dashboards
    """
    try:
        # Get system overview
        overview = await prometheus_client.get_system_overview()

        # Extract key health metrics
        summary = {
            "total_services": overview.get("total_services", 0),
            "overall_health": overview.get("overall_health", {}),
            "system_health_percentage": overview.get("system_health_percentage", 0),
            "categories_summary": {},
            "timestamp": overview.get("timestamp")
        }

        # Summarize each category
        for category_name, category_data in overview.get("categories", {}).items():
            if "error" not in category_data:
                summary["categories_summary"][category_name] = {
                    "total_services": category_data.get("total_services", 0),
                    "health_percentage": category_data.get("health_percentage", 0),
                    "health_distribution": category_data.get("health_distribution", {})
                }

        return summary

    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving health summary: {str(e)}")


@router.get("/performance/top-issues", response_model=Dict)
async def get_top_performance_issues(limit: int = Query(5, ge=1, le=20)):
    """
    Get top performance issues across all services
    Identifies services with critical or warning health status
    """
    try:
        # Get comprehensive system overview
        overview = await prometheus_client.get_system_overview()

        issues = []

        # Analyze each category for issues
        for category_name, category_data in overview.get("categories", {}).items():
            if "error" in category_data:
                continue

            for service_name, service_info in category_data.get("services", {}).items():
                status = service_info.get("status", "unknown")
                if status in ["critical", "warning"]:
                    issues.append({
                        "service": service_name,
                        "display_name": service_info.get("display_name", service_name),
                        "category": category_name,
                        "status": status,
                        "port": service_info.get("port")
                    })

        # Sort by severity (critical first, then warning)
        issues.sort(key=lambda x: (
            0 if x["status"] == "critical" else 1, x["service"]))

        return {
            "total_issues": len(issues),
            "issues": issues[:limit],
            "summary": {
                "critical": len([i for i in issues if i["status"] == "critical"]),
                "warning": len([i for i in issues if i["status"] == "warning"])
            },
            "timestamp": overview.get("timestamp")
        }

    except Exception as e:
        logger.error(f"Error getting performance issues: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving performance issues: {str(e)}")
