from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from models.service_models import ServiceInfo, ServiceCategory, ServiceHealth
from core.service_registry import BankingServiceRegistry
from integrations.prometheus_client import PrometheusClient
import logging

logger = logging.getLogger(__name__)

# Create router for service-related endpoints
router = APIRouter(prefix="/api/services", tags=["services"])

# Initialize service registry and Prometheus client
service_registry = BankingServiceRegistry()
prometheus_client = PrometheusClient()


@router.get("/", response_model=Dict)
async def list_all_services():
    """
    Get list of all 31 registered banking services
    Returns service count, categories, and basic service info
    """
    try:
        all_services = service_registry.get_all_services()
        categories = service_registry.get_categories()

        # Create simplified response
        services_summary = []
        for service_name, service_info in all_services.items():
            services_summary.append({
                "name": service_info.name,
                "display_name": service_info.display_name,
                "port": service_info.port,
                "category": service_info.category.value,
                "description": service_info.description,
                "prometheus_job": service_info.prometheus_job
            })

        return {
            "total_services": service_registry.get_services_count(),
            "categories": [cat.value for cat in categories],
            "services": services_summary
        }

    except Exception as e:
        logger.error(f"Error listing services: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving services: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get all available service categories"""
    try:
        categories = service_registry.get_categories()
        return [cat.value for cat in categories]
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving categories: {str(e)}")


@router.get("/category/{category}", response_model=Dict)
async def get_services_by_category(category: str):
    """
    Get all services in a specific category
    Available categories: core_banking, ml_detection, infrastructure, messaging, 
    cache_performance, database_storage, kubernetes, tracing
    """
    try:
        # Validate category
        try:
            service_category = ServiceCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Available: {[cat.value for cat in ServiceCategory]}"
            )

        # Get services in category
        services = service_registry.get_services_by_category(service_category)

        if not services:
            return {
                "category": category,
                "services": [],
                "count": 0,
                "message": f"No services found in category: {category}"
            }

        services_data = []
        for service in services:
            services_data.append({
                "name": service.name,
                "display_name": service.display_name,
                "host": service.host,
                "port": service.port,
                "description": service.description,
                "prometheus_job": service.prometheus_job,
                "health_endpoint": service.health_endpoint,
                "dependencies": service.dependencies,
                "tags": service.tags
            })

        return {
            "category": category,
            "services": services_data,
            "count": len(services)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting services for category {category}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving services: {str(e)}")


@router.get("/{service_name}", response_model=Dict)
async def get_service_details(service_name: str):
    """Get detailed information about a specific service"""
    try:
        service = service_registry.get_service(service_name)

        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found"
            )

        return {
            "name": service.name,
            "display_name": service.display_name,
            "host": service.host,
            "port": service.port,
            "category": service.category.value,
            "description": service.description,
            "prometheus_job": service.prometheus_job,
            "metrics_path": service.metrics_path,
            "scrape_interval": service.scrape_interval,
            "health_endpoint": service.health_endpoint,
            "dependencies": service.dependencies,
            "tags": service.tags
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service details for {service_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving service: {str(e)}")


@router.get("/{service_name}/health", response_model=Dict)
async def get_service_health(service_name: str):
    """
    Get health status for a specific service using Prometheus
    Queries the 'up' metric for the service
    """
    try:
        service = service_registry.get_service(service_name)

        if not service:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found"
            )

        # Query Prometheus for service health
        # Build PromQL query based on service configuration
        if service.prometheus_job == "banking-services":
            # For banking services, include instance filter
            query = f'up{{job="{service.prometheus_job}", instance="{service.host}:{service.port}"}}'
        else:
            # For other services, use job filter
            query = f'up{{job="{service.prometheus_job}"}}'

        result = await prometheus_client.query_metric(query)

        if result and result.get("status") == "success":
            data = result.get("data", {}).get("result", [])

            if data:
                # Get the latest value
                metric_data = data[0]
                value = metric_data.get("value", [None, "0"])
                status = "up" if float(value[1]) == 1.0 else "down"

                return {
                    "service_name": service_name,
                    "status": status,
                    "prometheus_job": service.prometheus_job,
                    "query_used": query,
                    "raw_value": float(value[1]),
                    "timestamp": value[0] if len(value) > 1 else None
                }
            else:
                return {
                    "service_name": service_name,
                    "status": "unknown",
                    "message": "No metrics data available",
                    "query_used": query
                }
        else:
            return {
                "service_name": service_name,
                "status": "unknown",
                "message": "Failed to query Prometheus",
                "query_used": query
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health for service {service_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving health: {str(e)}")


@router.get("/search/{query}", response_model=Dict)
async def search_services(query: str, limit: Optional[int] = Query(10, ge=1, le=50)):
    """
    Search services by name, description, or tags
    Returns matching services up to the specified limit
    """
    try:
        if len(query.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters long"
            )

        results = service_registry.search_services(query)

        # Limit results
        limited_results = results[:limit] if limit else results

        services_data = []
        for service in limited_results:
            services_data.append({
                "name": service.name,
                "display_name": service.display_name,
                "port": service.port,
                "category": service.category.value,
                "description": service.description,
                "tags": service.tags,
                "relevance_score": _calculate_relevance_score(query, service)
            })

        # Sort by relevance score
        services_data.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "query": query,
            "total_found": len(results),
            "returned_count": len(services_data),
            "results": services_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching services with query '{query}': {e}")
        raise HTTPException(
            status_code=500, detail=f"Error searching services: {str(e)}")


@router.get("/category/{category}/summary", response_model=Dict)
async def get_category_summary(category: str):
    """
    Get summary statistics for a service category
    Includes service count and basic health information
    """
    try:
        # Validate category
        try:
            service_category = ServiceCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Available: {[cat.value for cat in ServiceCategory]}"
            )

        summary = service_registry.get_category_summary(service_category)

        # Add health information by querying Prometheus
        health_summary = await _get_category_health_summary(service_category)
        summary.update(health_summary)

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting category summary for {category}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving summary: {str(e)}")

# Helper functions


def _calculate_relevance_score(query: str, service: ServiceInfo) -> float:
    """Calculate relevance score for search results"""
    score = 0.0
    query_lower = query.lower()

    # Exact name match gets highest score
    if query_lower == service.name.lower():
        score += 100
    elif query_lower in service.name.lower():
        score += 50

    # Display name match
    if query_lower in service.display_name.lower():
        score += 30

    # Description match
    if query_lower in service.description.lower():
        score += 20

    # Tag matches
    for tag in service.tags:
        if query_lower in tag.lower():
            score += 15

    # Category match
    if query_lower in service.category.value:
        score += 10

    return score


async def _get_category_health_summary(category: ServiceCategory) -> Dict:
    """Get health summary for all services in a category"""
    try:
        services = service_registry.get_services_by_category(category)

        health_counts = {"up": 0, "down": 0, "unknown": 0}

        for service in services:
            # Query health for each service
            try:
                if service.prometheus_job == "banking-services":
                    query = f'up{{job="{service.prometheus_job}", instance="{service.host}:{service.port}"}}'
                else:
                    query = f'up{{job="{service.prometheus_job}"}}'

                result = await prometheus_client.query_metric(query)

                if result and result.get("status") == "success":
                    data = result.get("data", {}).get("result", [])
                    if data:
                        value = data[0].get("value", [None, "0"])
                        status = "up" if float(value[1]) == 1.0 else "down"
                        health_counts[status] += 1
                    else:
                        health_counts["unknown"] += 1
                else:
                    health_counts["unknown"] += 1

            except Exception as e:
                logger.warning(f"Failed to get health for {service.name}: {e}")
                health_counts["unknown"] += 1

        total_services = len(services)
        health_percentage = (
            health_counts["up"] / total_services * 100) if total_services > 0 else 0

        return {
            "health_summary": health_counts,
            "health_percentage": round(health_percentage, 1),
            "total_services": total_services
        }

    except Exception as e:
        logger.error(
            f"Error getting health summary for category {category}: {e}")
        return {
            "health_summary": {"up": 0, "down": 0, "unknown": 0},
            "health_percentage": 0,
            "total_services": 0,
            "error": str(e)
        }
