"""
Updated Dashboard API endpoints for WatchTower AI (CSV-based)
File: backend/api/dashboards.py
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional, Dict, Any
import logging
from core.dashboard_registry import DashboardRegistry, get_legacy_panel_by_id
from integrations.enhanced_prometheus_client import EnhancedPrometheusClient

# Initialize router
router = APIRouter(prefix="/api/dashboards", tags=["dashboards"])

# Initialize dependencies
dashboard_registry = DashboardRegistry()
prometheus_client = EnhancedPrometheusClient()

logger = logging.getLogger(__name__)


def evaluate_panel_health(result: Dict, thresholds: Dict) -> str:
    """Evaluate panel health based on data availability and service status"""
    
    # First check if we have a successful query
    if result.get("status") != "success":
        return "unknown"
    
    try:
        # Get the result data - NOTE: Double nested structure from enhanced client
        data = result.get("data", {})
        inner_data = data.get("data", {})  # ← This is the key fix
        result_data = inner_data.get("result", [])
        
        # If no data returned, check if this might be a service health issue
        if not result_data:
            return "no_data"
        
        # Get the latest value from the first result
        latest_value = None
        for item in result_data:
            value = item.get("value", [])
            if len(value) >= 2:
                latest_value = float(value[1])
                break
        
        # If we couldn't extract a value, return no_data
        if latest_value is None:
            return "no_data"
        
        # For service "up" metrics, use direct mapping
        if latest_value == 1.0:
            return "healthy"
        elif latest_value == 0.0:
            return "unhealthy"
        
        # For other metrics, if we have data, consider it healthy
        # This implements the "data availability = healthy" approach
        if latest_value is not None:
            # If thresholds exist, try to use them
            if thresholds and thresholds.get("steps"):
                return evaluate_threshold_health(latest_value, thresholds)
            else:
                # No thresholds, but we have data = healthy
                return "healthy"
        
        return "unknown"
        
    except Exception as e:
        logger.error(f"Error evaluating panel health: {e}")
        return "unknown"

def evaluate_threshold_health(value: float, thresholds: Dict) -> str:
    """Evaluate health based on threshold configuration"""
    try:
        steps = thresholds.get("steps", [])
        if not steps:
            return "healthy"
        
        # Find the appropriate threshold
        for step in reversed(steps):  # Check from highest to lowest
            threshold_value = step.get("value")
            if threshold_value is not None and value >= threshold_value:
                color = step.get("color", "green")
                if color in ["red", "dark-red"]:
                    return "unhealthy"
                elif color in ["yellow", "orange"]:
                    return "warning"
                else:
                    return "healthy"
        
        return "healthy"
    except Exception as e:
        logger.error(f"Error evaluating threshold health: {e}")
        return "unknown"

# IMPORTANT: Specific routes must come BEFORE generic routes


@router.get("/")
async def get_all_dashboards():
    """Get all available dashboards"""
    try:
        summaries = dashboard_registry.get_dashboard_summaries()
        stats = dashboard_registry.get_registry_stats()

        # Handle case where CSV file doesn't exist or is empty
        if not dashboard_registry.loaded:
            return {
                "dashboards": [],
                "stats": {
                    "total_panels": 0,
                    "total_dashboards": 0,
                    "categories": {},
                    "panel_types": {},
                    "panels_by_category": {},
                    "loaded": False,
                    "error": "No dashboard data loaded. Run extract_dashboards.py first."
                }
            }

        return {
            "dashboards": summaries,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting dashboards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard registry statistics"""
    try:
        stats = dashboard_registry.get_registry_stats()

        # Handle case where CSV file doesn't exist or is empty
        if not stats or not dashboard_registry.loaded:
            return {
                "total_panels": 0,
                "total_dashboards": 0,
                "categories": {},
                "panel_types": {},
                "panels_by_category": {},
                "loaded": False,
                "error": "No dashboard data loaded. Run extract_dashboards.py first."
            }

        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_dashboard_categories():
    """Get all available dashboard categories"""
    try:
        categories = dashboard_registry.get_all_categories()
        stats = dashboard_registry.get_registry_stats()

        return {
            "categories": categories,
            "panels_by_category": stats.get("panels_by_category", {})
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/category/{category}")
async def get_dashboards_by_category(category: str = Path(..., description="Dashboard category")):
    """Get dashboards by category"""
    try:
        dashboards = dashboard_registry.get_dashboards_by_category(category)

        if not dashboards:
            raise HTTPException(
                status_code=404, detail=f"No dashboards found for category: {category}"
            )

        return {
            "category": category,
            "dashboards": dashboards,
            "count": len(dashboards)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboards by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/panels/all")
async def get_all_panels():
    """Get all panels from all dashboards"""
    try:
        panels = dashboard_registry.get_all_panels()
        stats = dashboard_registry.get_registry_stats()

        return {
            "panels": panels,
            "total": len(panels),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting all panels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/panels/search")
async def search_panels(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search panels by query string"""
    try:
        # Get all matching panels
        all_panels = dashboard_registry.search_panels(q)

        # Filter by category if specified
        if category:
            all_panels = [p for p in all_panels if p.get(
                'category') == category]

        return {
            "query": q,
            "category": category,
            "results": all_panels,
            "total": len(all_panels)
        }
    except Exception as e:
        logger.error(f"Error searching panels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/panels/{panel_id}/query")
async def execute_panel_query(
    panel_id: str = Path(..., description="Panel ID"),
    time_range: Optional[str] = Query(
        "5m", description="Time range for query (e.g., 5m, 1h, 1d)")
):
    """Execute the PromQL query for a specific panel"""
    try:
        # Get panel from registry
        panel_data = dashboard_registry.get_panel_by_id(panel_id)

        if not panel_data:
            raise HTTPException(
                status_code=404, detail=f"Panel not found: {panel_id}")

        # Get the query
        query = panel_data.metric_query

        if not query:
            raise HTTPException(
                status_code=400, detail=f"Panel has no query: {panel_id}")

        # Execute the query using enhanced prometheus client
        result = await prometheus_client.query_metric(query)

        # Get panel info
        panel_info = {
            "id": panel_data.panel_id,
            "title": panel_data.panel_title,
            "type": panel_data.panel_type,
            "category": panel_data.dashboard_category,
            "query": query,
            "unit": panel_data.unit,
            "dashboard_title": panel_data.dashboard_title
        }

        # Evaluate health status based on thresholds
        health_status = "unknown"
        thresholds = dashboard_registry.get_panel_thresholds(panel_id)
        if thresholds and result.get("status") == "success":
            health_status = evaluate_panel_health(result, thresholds)

        return {
            "panel": panel_info,
            "query": query,
            "time_range": time_range,
            "result": result,
            "health_status": health_status,
            "timestamp": None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing panel query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/panels/batch-query")
async def batch_query_panels(
    panel_ids: List[str],
    time_range: Optional[str] = Query(
        "5m", description="Time range for queries")
):
    """Execute queries for multiple panels"""
    try:
        results = []

        for panel_id in panel_ids:
            try:
                # Get panel data
                panel_data = dashboard_registry.get_panel_by_id(panel_id)
                if not panel_data:
                    results.append({
                        "panel_id": panel_id,
                        "error": "Panel not found"
                    })
                    continue

                # Execute query
                if panel_data.metric_query:
                    result = await prometheus_client.query_metric(panel_data.metric_query)

                    # Evaluate health
                    health_status = "unknown"
                    thresholds = dashboard_registry.get_panel_thresholds(
                        panel_id)
                    if thresholds and result.get("status") == "success":
                        health_status = evaluate_panel_health(
                            result, thresholds)

                    results.append({
                        "panel_id": panel_id,
                        "title": panel_data.panel_title,
                        "result": result,
                        "health_status": health_status,
                        "query": panel_data.metric_query
                    })
                else:
                    results.append({
                        "panel_id": panel_id,
                        "error": "No query available"
                    })

            except Exception as e:
                results.append({
                    "panel_id": panel_id,
                    "error": str(e)
                })

        return {
            "time_range": time_range,
            "results": results,
            "total": len(panel_ids),
            "successful": len([r for r in results if "error" not in r])
        }
    except Exception as e:
        logger.error(f"Error in batch query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# IMPORTANT: This generic route must come LAST


@router.get("/{dashboard_uid}")
async def get_dashboard_by_uid(dashboard_uid: str = Path(..., description="Dashboard UID")):
    """Get specific dashboard by UID"""
    try:
        # Get all panels for this dashboard
        dashboard_panels = dashboard_registry.get_panels_by_dashboard_uid(
            dashboard_uid)

        if not dashboard_panels:
            raise HTTPException(
                status_code=404, detail=f"Dashboard not found: {dashboard_uid}"
            )

        # Get dashboard info from first panel
        first_panel = dashboard_panels[0]

        return {
            "uid": dashboard_uid,
            "title": first_panel.get("dashboard_title", "Unknown Dashboard"),
            "category": first_panel.get("category", "general"),
            "panels": dashboard_panels,
            "panel_count": len(dashboard_panels)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard by UID: {e}")
        raise HTTPException(status_code=500, detail=str(e))
