from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager
import json

# Import existing API routes
from api.chat import router as chat_router
from api.enhanced_metrics import router as enhanced_metrics_router
from api.services import router as services_router

# Add the missing dashboard API router import
from api.dashboards import router as dashboards_router

# Import core components
from core.websocket import WebSocketManager
from core.service_registry import BankingServiceRegistry
from integrations.enhanced_prometheus_client import EnhancedPrometheusClient
from llm.openai_client import OpenAIClient

# Add these imports to the top of main.py
from agents.integration import agent_integration
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global components
ws_manager = WebSocketManager()
service_registry = BankingServiceRegistry()
prometheus_client = EnhancedPrometheusClient()
openai_client = OpenAIClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with full AI agent integration"""
    logger.info("🚀 Starting WatchTower AI Backend...")
    
    # Initialize components
    try:
        # Test connections
        prometheus_status = await prometheus_client.check_prometheus_connection()
        openai_status = openai_client.test_connection()
        
        logger.info(f"Prometheus connection: {'✅' if prometheus_status else '❌'}")
        logger.info(f"OpenAI connection: {'✅' if openai_status else '❌'}")
        logger.info(f"Service registry: ✅ {service_registry.get_services_count()} services loaded")
        logger.info("📊 Dashboard registry initialized")
        logger.info("💬 Enhanced chat API loaded")
        
        # Initialize advanced AI agent system
        logger.info("🤖 Initializing Advanced AI Agent System...")
        await agent_integration.initialize()
        logger.info("✅ Advanced AI Agent System initialized successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Don't fail startup if agent system fails
        logger.warning("⚠️  Continuing without agent system")
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down WatchTower AI Backend...")
    try:
        await agent_integration.shutdown()
        logger.info("✅ Agent system shutdown complete")
    except Exception as e:
        logger.error(f"Error during agent shutdown: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="WatchTower AI Backend",
    description="Intelligent Banking System Monitoring Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3333"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router)
app.include_router(enhanced_metrics_router)
app.include_router(services_router)
app.include_router(dashboards_router)  # New dashboard API

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "WatchTower AI Backend Running",
        "version": "1.0.0",
        "features": {
            "chat": True,
            "enhanced_metrics": True,
            "service_registry": True,
            "dashboard_integration": True  # New feature
        }
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check core components
        prometheus_status = await prometheus_client.check_prometheus_connection()
        openai_status = openai_client.test_connection()
        
        return {
            "status": "healthy",
            "service": "watchtower-ai",
            "components": {
                "prometheus": prometheus_status,
                "openai": openai_status,
                "websocket": len(ws_manager.active_connections),
                "service_registry": service_registry.get_services_count(),
                "dashboard_integration": True
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Enhanced system overview with dashboard integration
@app.get("/api/system/overview")
async def get_system_overview():
    """Get comprehensive system overview including AI agent data"""
    try:
        # Get enhanced system overview using the existing client
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
        prometheus_status = await prometheus_client.check_prometheus_connection()
        
        # Get dashboard stats
        from core.dashboard_registry import DashboardRegistry
        dashboard_registry = DashboardRegistry()
        dashboard_stats = dashboard_registry.get_registry_stats()
        
        # Get AI agent system status
        agent_status = agent_integration.get_system_status()
        
        return {
            "total_services": service_registry.get_services_count(),
            "categories_registry": categories_summary,
            "enhanced_metrics": enhanced_overview,
            "dashboard_integration": {
                "total_dashboards": dashboard_stats["total_dashboards"],
                "total_panels": dashboard_stats["total_panels"],
                "categories": dashboard_stats["categories"],
                "panels_by_category": dashboard_stats["panels_by_category"]
            },
            "monitoring": {
                "prometheus_connected": prometheus_status,
                "websocket_connections": len(ws_manager.active_connections),
                "enhanced_features_available": True
            },
            "ai_features": {
                "openai_available": openai_client.test_connection(),
                "chat_enabled": True,
                "natural_language_queries": True,
                "service_aware_responses": True,
                "dashboard_queries_enabled": True,
                "agent_system_active": agent_status.get("initialized", False),
                "proactive_monitoring": agent_status.get("monitoring_active", False),
                "intelligent_analysis": True,
                "multi_agent_workflows": True
            },
            "agent_system": agent_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to get system overview: {str(e)}",
                "status": "degraded",
                "timestamp": datetime.now().isoformat()
            }
        )

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI-powered communication"""
    try:
        await websocket.accept()
        logger.info("WebSocket connection established")
        
        # Send welcome message with AI system status
        agent_status = agent_integration.get_system_status()
        welcome_message = {
            "type": "connection_established",
            "message": "Connected to WatchTower AI",
            "ai_system_active": agent_status.get("initialized", False),
            "monitoring_active": agent_status.get("monitoring_active", False),
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_text(json.dumps(welcome_message))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                
                try:
                    # Try to parse as JSON
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "unknown")
                    
                    if message_type == "chat_query":
                        # Process chat query using AI agents
                        query = message_data.get("query", "")
                        if query:
                            # Use agent system to process query
                            agent_response = await agent_integration.process_chat_query(query)
                            
                            response = {
                                "type": "chat_response",
                                "query": query,
                                "response": agent_response,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            response = {
                                "type": "error",
                                "message": "No query provided",
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    elif message_type == "agent_status":
                        # Get current agent status
                        response = {
                            "type": "agent_status",
                            "status": agent_integration.get_system_status(),
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    else:
                        # Echo back unknown messages
                        response = {
                            "type": "echo",
                            "message": f"Received: {data}",
                            "timestamp": datetime.now().isoformat()
                        }
                    
                except json.JSONDecodeError:
                    # Handle plain text messages
                    response = {
                        "type": "text_message",
                        "message": f"Received text: {data}",
                        "timestamp": datetime.now().isoformat()
                    }
                
                await websocket.send_text(json.dumps(response))
                
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")
                try:
                    error_response = {
                        "type": "error",
                        "message": f"Message processing failed: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_text(json.dumps(error_response))
                except:
                    break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Test Prometheus connection
@app.get("/api/prometheus/status")
async def prometheus_status():
    """Check if Prometheus is accessible"""
    is_connected = await prometheus_client.check_prometheus_connection()
    
    # Also test enhanced features
    enhanced_available = False
    try:
        # Try to get a quick system overview
        overview = await prometheus_client.get_system_overview()
        enhanced_available = True
    except Exception:
        pass
    
    return {
        "prometheus_connected": is_connected,
        "enhanced_features_available": enhanced_available,
        "url": "http://localhost:9090"
    }

@app.get("/api/openai/status")
async def openai_status():
    """Test OpenAI API connection"""
    is_connected = openai_client.test_connection()
    return {"openai_connected": is_connected}

# Add these new endpoints for complete AI system integration:

@app.get("/api/agents/status")
async def get_agent_status():
    """Get comprehensive status of AI agent system"""
    try:
        agent_status = agent_integration.get_system_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agent_system": agent_status,
            "features": {
                "proactive_monitoring": agent_status.get("monitoring_active", False),
                "intelligent_analysis": agent_status.get("initialized", False),
                "multi_agent_workflows": agent_status.get("initialized", False),
                "background_tasks": agent_status.get("background_tasks", 0),
                "agents_count": len(agent_status.get("agent_statuses", {}))
            },
            "capabilities": [
                "Health monitoring and analysis",
                "Root cause analysis",
                "Cross-system correlation",
                "Predictive insights",
                "Automated recommendations",
                "Real-time alerting"
            ]
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to get agent status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/agents/health-check")
async def trigger_agent_health_check():
    """Trigger comprehensive AI-powered health check"""
    try:
        if not agent_integration.is_initialized:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Agent system not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Trigger health check using agent system
        result = await agent_integration._handle_health_query("system health check", {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_check": result,
            "triggered_by": "api_request"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/agents/analyze")
async def trigger_agent_analysis():
    """Trigger comprehensive AI system analysis"""
    try:
        if not agent_integration.is_initialized:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Agent system not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Trigger system analysis using agent system
        result = await agent_integration._handle_analysis_query("comprehensive system analysis", {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis_result": result,
            "triggered_by": "api_request"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/agents/insights")
async def get_agent_insights():
    """Get AI-generated insights about system performance"""
    try:
        if not agent_integration.is_initialized:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Agent system not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Get comprehensive overview using agent system
        result = await agent_integration._handle_overview_query("system insights", {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "insights": result,
            "generated_by": "ai_agents"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to get insights: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050)
