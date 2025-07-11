"""
Enhanced Chat API for WatchTower AI with Dashboard Integration
File: backend/api/chat.py
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime

# Import our core components
from core.service_registry import BankingServiceRegistry
from core.dashboard_registry import DashboardRegistry
from integrations.enhanced_prometheus_client import EnhancedPrometheusClient
from llm.openai_client import OpenAIClient
from agents.integration import agent_integration

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize components
service_registry = BankingServiceRegistry()
dashboard_registry = DashboardRegistry()
prometheus_client = EnhancedPrometheusClient()
openai_client = OpenAIClient()


@router.get("/")
async def chat_query(
    query: str = Query(..., description="Natural language query about the banking system")
) -> Dict[str, Any]:
    """
    Process natural language query with advanced AI agent integration
    Returns ChatResponse format expected by frontend
    """
    try:
        logger.info(f"Processing chat query: {query}")
        
        # Step 1: Try to use agent system for intelligent processing
        agent_response = await agent_integration.process_chat_query(query)
        
        if agent_response.get("success"):
            # Agent system provided a response
            return {
                "user_query": query,
                "promql_query": agent_response.get("data", {}).get("promql_query", ""),
                "explanation": agent_response.get("summary", "Agent system processed your query"),
                "raw_data": agent_response.get("data", {}),
                "agent_powered": True,
                "response_type": agent_response.get("response_type", "agent_response"),
                "execution_time": agent_response.get("execution_time", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback to original processing if agent system fails
            logger.warning(f"Agent system failed, falling back to original processing: {agent_response.get('error', 'Unknown error')}")
            
            # Original processing logic (your existing code)
            query_context = await analyze_query_context(query)
            enhanced_query = build_enhanced_query(query, query_context)
            promql_query = await openai_client.natural_language_to_promql(enhanced_query)
            metric_result = await prometheus_client.query_metric(promql_query)
            explanation = await generate_enhanced_explanation(query, promql_query, metric_result, query_context)
            
            return {
                "user_query": query,
                "promql_query": promql_query,
                "explanation": explanation,
                "raw_data": metric_result,
                "context": query_context,
                "agent_powered": False,
                "fallback_reason": agent_response.get("error", "Agent system unavailable"),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error processing chat query '{query}': {e}")
        return {
            "user_query": query,
            "promql_query": "",
            "explanation": f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question.",
            "raw_data": None,
            "error": str(e),
            "agent_powered": False,
            "timestamp": datetime.now().isoformat()
        }


@router.get("/health")
async def chat_health():
    """Chat service health check"""
    try:
        # Test all components
        openai_status = openai_client.test_connection()
        prometheus_status = await prometheus_client.check_prometheus_connection()

        return {
            "status": "healthy",
            "service": "chat",
            "components": {
                "openai": openai_status,
                "prometheus": prometheus_status,
                "service_registry": service_registry.get_services_count(),
                "dashboard_registry": dashboard_registry.loaded
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "chat",
            "error": str(e)
        }


@router.get("/context")
async def get_chat_context():
    """Get available context for chat queries"""
    try:
        return {
            "services": {
                "total": service_registry.get_services_count(),
                "categories": [cat.value for cat in service_registry.get_categories()],
                "sample_services": [
                    {
                        "name": svc.name,
                        "display_name": svc.display_name,
                        "category": svc.category.value
                    }
                    for svc in list(service_registry.get_all_services().values())[:10]
                ]
            },
            "dashboards": {
                "total_panels": dashboard_registry.get_registry_stats().get("total_panels", 0),
                "total_dashboards": dashboard_registry.get_registry_stats().get("total_dashboards", 0),
                "categories": dashboard_registry.get_all_categories(),
                "loaded": dashboard_registry.loaded
            },
            "example_queries": [
                "How are the banking services doing?",
                "What's the cache hit ratio?",
                "Show me transaction service performance",
                "Are there any unhealthy services?",
                "What's the status of Redis cache?",
                "Show me system overview"
            ]
        }
    except Exception as e:
        logger.error(f"Error getting chat context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def analyze_query_context(query: str) -> Dict[str, Any]:
    """Analyze user query to understand context and intent"""
    try:
        query_lower = query.lower()
        context = {
            "query_type": "general",
            "relevant_services": [],
            "relevant_categories": [],
            "relevant_panels": [],
            "intent": "unknown"
        }

        # Detect query intent
        if any(word in query_lower for word in ["health", "healthy", "status", "up", "down"]):
            context["intent"] = "health_check"
        elif any(word in query_lower for word in ["performance", "slow", "fast", "latency", "response"]):
            context["intent"] = "performance"
        elif any(word in query_lower for word in ["cache", "redis", "hit", "miss"]):
            context["intent"] = "cache_analysis"
        elif any(word in query_lower for word in ["transaction", "payment", "transfer"]):
            context["intent"] = "transaction_analysis"
        elif any(word in query_lower for word in ["overview", "summary", "system"]):
            context["intent"] = "system_overview"

        # Find relevant services
        for service_name, service_info in service_registry.get_all_services().items():
            if (service_name.lower() in query_lower or
                service_info.display_name.lower() in query_lower or
                    any(tag.lower() in query_lower for tag in service_info.tags)):
                context["relevant_services"].append({
                    "name": service_name,
                    "display_name": service_info.display_name,
                    "category": service_info.category.value,
                    "port": service_info.port
                })

        # Find relevant categories
        for category in service_registry.get_categories():
            if category.value.lower() in query_lower:
                context["relevant_categories"].append(category.value)

        # Find relevant dashboard panels
        if dashboard_registry.loaded:
            relevant_panels = dashboard_registry.search_panels(query)
            context["relevant_panels"] = relevant_panels[:5]  # Limit to top 5

        # Set query type based on findings
        if context["relevant_services"]:
            context["query_type"] = "service_specific"
        elif context["relevant_categories"]:
            context["query_type"] = "category_specific"
        elif context["relevant_panels"]:
            context["query_type"] = "panel_specific"

        return context

    except Exception as e:
        logger.error(f"Error analyzing query context: {e}")
        return {"query_type": "general", "error": str(e)}


def build_enhanced_query(original_query: str, context: Dict[str, Any]) -> str:
    """Build enhanced query with context for better PromQL generation"""
    enhanced_query = original_query

    # Add service context
    if context.get("relevant_services"):
        services = [svc["display_name"]
                    for svc in context["relevant_services"]]
        enhanced_query += f"\n\nRelevant services: {', '.join(services)}"

    # Add category context
    if context.get("relevant_categories"):
        enhanced_query += f"\n\nRelevant categories: {', '.join(context['relevant_categories'])}"

    # Add intent context
    if context.get("intent") != "unknown":
        enhanced_query += f"\n\nQuery intent: {context['intent']}"

    # Add panel context
    if context.get("relevant_panels"):
        panel_info = []
        for panel in context["relevant_panels"][:3]:  # Top 3
            panel_info.append(
                f"- {panel.get('title', 'Unknown')}: {panel.get('query', 'No query')}")
        if panel_info:
            enhanced_query += f"\n\nRelevant dashboard panels:\n" + \
                "\n".join(panel_info)

    return enhanced_query


async def generate_enhanced_explanation(
    original_query: str,
    promql_query: str,
    metric_result: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """Generate enhanced explanation using OpenAI with context"""
    try:
        # Build enhanced prompt for explanation
        enhanced_prompt = f"""
User asked: {original_query}

Query context:
- Intent: {context.get('intent', 'unknown')}
- Query type: {context.get('query_type', 'general')}
- Relevant services: {len(context.get('relevant_services', []))}
- Relevant panels: {len(context.get('relevant_panels', []))}

PromQL executed: {promql_query}

Metric data: {metric_result}

Additional context about the banking system:
- Total services monitored: {service_registry.get_services_count()}
- Dashboard panels available: {dashboard_registry.get_registry_stats().get('total_panels', 0)}
- System categories: {[cat.value for cat in service_registry.get_categories()]}

Please provide a comprehensive explanation that includes:
1. Direct answer to the user's question
2. Current status/health information
3. Any important insights or recommendations
4. Context about the banking system components involved
"""

        explanation = await openai_client.explain_metrics(original_query, enhanced_prompt)

        # Add context-specific insights
        if context.get("relevant_services"):
            explanation += f"\n\n💡 **Related Services**: This query involves {len(context['relevant_services'])} services including: {', '.join([svc['display_name'] for svc in context['relevant_services'][:3]])}"

        if context.get("relevant_panels"):
            explanation += f"\n\n📊 **Dashboard Integration**: Found {len(context['relevant_panels'])} relevant dashboard panels for deeper analysis."

        return explanation

    except Exception as e:
        logger.error(f"Error generating enhanced explanation: {e}")
        return f"I found the data you requested, but had trouble generating a detailed explanation. The query '{promql_query}' returned metric data. Please try asking in a different way."


@router.post("/message")
async def send_message(message: Dict[str, str]):
    """Alternative endpoint for POST requests"""
    try:
        query = message.get("query", message.get("message", ""))
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Use the same logic as GET endpoint
        return await chat_query(query)

    except Exception as e:
        logger.error(f"Error in POST message endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_query_suggestions():
    """Get smart query suggestions based on available data"""
    try:
        suggestions = []

        # Service-based suggestions
        core_services = service_registry.get_services_by_category(
            "core_banking")
        if core_services:
            suggestions.extend([
                f"How is {svc.display_name.lower()} performing?",
                f"Check {svc.display_name.lower()} health status"
            ] for svc in core_services[:3])

        # Category-based suggestions
        categories = service_registry.get_categories()
        suggestions.extend([
            f"Show me {cat.value.replace('_', ' ')} services status",
            f"What's the health of {cat.value.replace('_', ' ')} category?"
        ] for cat in categories[:3])

        # Dashboard-based suggestions
        if dashboard_registry.loaded:
            categories = dashboard_registry.get_all_categories()
            suggestions.extend([
                f"Show me {cat} dashboard metrics",
                f"What's the current {cat} performance?"
            ] for cat in categories[:3])

        # Flatten the list
        flat_suggestions = []
        for item in suggestions:
            if isinstance(item, list):
                flat_suggestions.extend(item)
            else:
                flat_suggestions.append(item)

        return {
            "suggestions": flat_suggestions[:10],  # Limit to 10
            "categories": [cat.value for cat in service_registry.get_categories()],
            "total_services": service_registry.get_services_count()
        }

    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        return {"suggestions": [], "error": str(e)}


@router.get("/agent-status")
async def get_chat_agent_status():
    """Get status of AI agents for chat interface"""
    try:
        return {
            "agent_system": agent_integration.get_system_status(),
            "chat_integration": {
                "enabled": agent_integration.is_initialized,
                "features": [
                    "proactive_monitoring",
                    "intelligent_analysis",
                    "multi_agent_workflows",
                    "correlation_analysis"
                ]
            }
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/analyze")
async def trigger_agent_analysis(request: Dict[str, Any]):
    """Trigger specific agent analysis"""
    try:
        query = request.get("query", "")
        analysis_type = request.get("type", "general")
        
        if analysis_type == "health":
            result = await agent_integration._handle_health_query(query, {})
        elif analysis_type == "analysis":
            result = await agent_integration._handle_analysis_query(query, {})
        elif analysis_type == "overview":
            result = await agent_integration._handle_overview_query(query, {})
        else:
            result = await agent_integration.process_chat_query(query)
        
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering agent analysis: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
