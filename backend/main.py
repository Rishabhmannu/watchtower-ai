from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from integrations.prometheus_client import PrometheusClient
from llm.openai_client import OpenAIClient
from core.websocket import ws_manager

# Import the service registry router and enhanced metrics router
from api.services import router as services_router
from api.enhanced_metrics import router as enhanced_metrics_router

# Create FastAPI app
app = FastAPI(
    title="WatchTower AI",
    description="Intelligent AI monitoring agent for banking systems with enhanced Prometheus capabilities",
    version="1.1.0"
)

# Add CORS middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3333"],  # Your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(services_router)
app.include_router(enhanced_metrics_router)

# Initialize clients
prometheus_client = PrometheusClient()
openai_client = OpenAIClient()

# Enhanced root endpoint
@app.get("/")
def read_root():
    return {
        "message": "WatchTower AI Backend is running!",
        "version": "1.1.0",
        "features": [
            "Service Registry (31 services)",
            "Enhanced Prometheus Integration", 
            "Multi-service metric querying",
            "Service-specific metric templates",
            "Intelligent caching and retry logic",
            "Category-based health summaries",
            "OpenAI Chat Interface",
            "Real-time WebSocket monitoring"
        ],
        "api_endpoints": {
            "services": "/api/services/*",
            "enhanced_metrics": "/api/metrics/*",
            "legacy_prometheus": "/api/prometheus/*",
            "chat": "/api/chat",
            "websocket": "/ws"
        }
    }

# Enhanced health check endpoint
@app.get("/api/health")
async def health_check():
    # Test Prometheus connectivity
    prometheus_connected = await prometheus_client.check_connection()
    
    # Test OpenAI connectivity
    openai_connected = openai_client.test_connection()
    
    # Get basic system health
    try:
        health_summary = await prometheus_client.get_system_overview()
        system_health_pct = health_summary.get("system_health_percentage", 0)
        total_services = health_summary.get("total_services", 0)
    except Exception:
        system_health_pct = 0
        total_services = 0
    
    return {
        "status": "healthy" if prometheus_connected and openai_connected else "degraded",
        "service": "watchtower-ai-backend",
        "version": "1.1.0",
        "components": {
            "service_registry": "operational",
            "prometheus_client": "connected" if prometheus_connected else "disconnected",
            "enhanced_prometheus": "operational" if prometheus_connected else "degraded",
            "openai_client": "connected" if openai_connected else "disconnected",
            "websocket_manager": "operational"
        },
        "system_health": {
            "total_services": total_services,
            "health_percentage": system_health_pct,
            "active_websocket_connections": len(ws_manager.active_connections)
        }
    }

# Enhanced system overview endpoint
@app.get("/api/system/overview")
async def system_overview():
    """Get comprehensive system overview including all 31 services with enhanced metrics"""
    try:
        # Import here to avoid circular imports
        from core.service_registry import BankingServiceRegistry
        
        service_registry = BankingServiceRegistry()
        
        # Get enhanced system overview using the new client
        enhanced_overview = await prometheus_client.get_system_overview()
        
        # Get basic service counts by category (from registry)
        categories_summary = {}
        for category in service_registry.get_categories():
            services = service_registry.get_services_by_category(category)
            categories_summary[category.value] = {
                "count": len(services),
                "services": [s.display_name for s in services]
            }
        
        # Check Prometheus connectivity
        prometheus_status = await prometheus_client.check_connection()
        
        # Get some key metrics
        targets_result = await prometheus_client.get_targets()
        active_targets = len(targets_result) if targets_result else 0
        
        return {
            "total_services": service_registry.get_services_count(),
            "categories_registry": categories_summary,
            "enhanced_metrics": enhanced_overview,
            "monitoring": {
                "prometheus_connected": prometheus_status,
                "active_targets": active_targets,
                "websocket_connections": len(ws_manager.active_connections),
                "enhanced_features_available": True
            },
            "ai_features": {
                "openai_available": openai_client.test_connection(),
                "chat_enabled": True,
                "natural_language_queries": True,
                "service_aware_responses": True
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to get system overview: {str(e)}",
            "status": "degraded"
        }

# Test Prometheus connection
@app.get("/api/prometheus/status")
async def prometheus_status():
    """Check if Prometheus is accessible"""
    is_connected = await prometheus_client.check_connection()
    
    # Also test enhanced features
    enhanced_available = False
    try:
        # Try to get a quick system overview
        overview = await prometheus_client.get_system_overview()
        enhanced_available = True
    except Exception as e:
        pass
    
    return {
        "prometheus_connected": is_connected,
        "enhanced_features_available": enhanced_available,
        "client_version": "enhanced"
    }

# Get banking system targets
@app.get("/api/prometheus/targets")
async def get_targets():
    """Get list of all monitored banking services"""
    targets = await prometheus_client.get_targets()
    if targets:
        return {"targets": targets, "count": len(targets)}
    else:
        return {"error": "Could not retrieve targets"}

# Query a specific metric
@app.get("/api/prometheus/query")
async def query_metric(query: str, use_enhanced: bool = True):
    """Query Prometheus with a PromQL query (optionally using enhanced client)"""
    if use_enhanced:
        result = await prometheus_client.query_with_retry(query)
        return result
    else:
        result = await prometheus_client.query_metric(query)
        if result:
            return {"query": query, "result": result}
        else:
            return {"error": f"Failed to query metric: {query}"}

# Pre-defined banking system queries
@app.get("/api/banking/health")
async def banking_health():
    """Get health status of core banking services using enhanced client"""
    try:
        # Use the new enhanced endpoint for better results
        core_services_health = await prometheus_client.query_category_health("core_banking")
        return {
            "category": "core_banking",
            "enhanced_results": core_services_health,
            "legacy_compatible": True
        }
    except Exception as e:
        # Fallback to basic query
        query = 'up{job="banking-services"}'
        result = await prometheus_client.query_metric(query)
        if result:
            return {"query": query, "result": result, "fallback_mode": True}
        else:
            return {"error": "Failed to get banking service health"}

@app.get("/api/banking/cache")
async def banking_cache():
    """Get Redis cache metrics using enhanced templates"""
    try:
        # Try to get cache-specific service metrics
        cache_services = ["cache_analyzer", "cache_proxy", "redis_exporter"]
        cache_metrics = await prometheus_client.query_multiple_services(cache_services)
        
        return {
            "cache_services": cache_metrics,
            "enhanced_results": True
        }
    except Exception as e:
        # Fallback to basic query
        query = "redis_connected_clients"
        result = await prometheus_client.query_metric(query)
        if result:
            return {"query": query, "result": result, "fallback_mode": True}
        else:
            return {"error": "Failed to get cache metrics"}

# Test OpenAI connection
@app.get("/api/openai/status")
async def openai_status():
    """Test OpenAI API connection"""
    is_connected = openai_client.test_connection()
    return {"openai_connected": is_connected}

# Enhanced chat endpoint with service context
@app.get("/api/chat")
async def chat_query(query: str):
    """Process natural language query about banking system with enhanced service context"""
    try:
        # Import service registry for context
        from core.service_registry import BankingServiceRegistry
        service_registry = BankingServiceRegistry()
        
        # Check if query is about specific services
        query_lower = query.lower()
        relevant_services = []
        
        # Search for services mentioned in the query
        for service_name, service_info in service_registry.get_all_services().items():
            if (service_name in query_lower or 
                service_info.display_name.lower() in query_lower or
                any(tag in query_lower for tag in service_info.tags)):
                relevant_services.append(service_info)
        
        # Use enhanced metrics if services are mentioned
        enhanced_context = ""
        if relevant_services:
            try:
                # Get real-time metrics for mentioned services
                service_names = [s.name for s in relevant_services]
                enhanced_metrics = await prometheus_client.query_multiple_services(service_names)
                
                enhanced_context = f"\nReal-time service status: {[s.display_name for s in relevant_services]}"
                for service_name, service_data in enhanced_metrics.get("services", {}).items():
                    if "overall_health" in service_data:
                        health = service_data["overall_health"]
                        enhanced_context += f"\n- {service_name}: {health}"
                        
            except Exception as e:
                enhanced_context = f"\nRelevant services: {[s.display_name for s in relevant_services]}"
        
        # Convert natural language to PromQL
        promql_query = await openai_client.natural_language_to_promql(query + enhanced_context)

        # Query Prometheus using enhanced client
        metric_data = await prometheus_client.query_with_retry(promql_query)

        if metric_data and metric_data.get("success"):
            # Get AI explanation with enhanced context
            explanation = await openai_client.explain_metrics(query, metric_data.get("data"))
            return {
                "user_query": query,
                "promql_query": promql_query,
                "explanation": explanation,
                "relevant_services": [s.display_name for s in relevant_services],
                "enhanced_context": enhanced_context,
                "execution_time_ms": metric_data.get("execution_time_ms"),
                "raw_data": metric_data.get("data")
            }
        else:
            error_msg = metric_data.get("error_message") if metric_data else "Unknown error"
            return {"error": f"No data found for query: {query}", "details": error_msg}

    except Exception as e:
        return {"error": f"Chat processing failed: {str(e)}"}

# Simple test endpoint for WebSocket status
@app.get("/api/websocket/test")
async def websocket_test():
    """Test WebSocket manager status"""
    return {
        "active_connections": len(ws_manager.active_connections),
        "is_monitoring": ws_manager.is_monitoring,
        "status": "WebSocket ready"
    }

# WebSocket endpoint for real-time updates (frontend expects /ws)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time system monitoring"""
    try:
        await ws_manager.connect(websocket)
        while True:
            # Keep connection alive and listen for client messages
            try:
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
                await websocket.send_text(f"Echo: {data}")
            except WebSocketDisconnect:
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    await prometheus_client.close()
    # OpenAI client doesn't need explicit cleanup

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
