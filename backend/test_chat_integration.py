"""
Test script to verify chat integration works
File: backend/test_chat_integration.py
"""

from integrations.enhanced_prometheus_client import EnhancedPrometheusClient
from llm.openai_client import OpenAIClient
from core.dashboard_registry import DashboardRegistry
from core.service_registry import BankingServiceRegistry
from api.chat import chat_query
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))


async def test_chat_integration():
    """Test the chat integration functionality"""

    print("🧪 Testing WatchTower AI Chat Integration...")
    print("="*50)

    # Test 1: Component initialization
    print("\n1. Testing Component Initialization:")
    try:
        service_registry = BankingServiceRegistry()
        dashboard_registry = DashboardRegistry()
        openai_client = OpenAIClient()
        prometheus_client = EnhancedPrometheusClient()

        print(
            f"   ✅ Service Registry: {service_registry.get_services_count()} services")
        print(
            f"   ✅ Dashboard Registry: {dashboard_registry.get_registry_stats().get('total_panels', 0)} panels")
        print(
            f"   ✅ OpenAI Client: {'Connected' if openai_client.test_connection() else 'Failed'}")
        print(f"   ✅ Prometheus Client: {'Connected' if await prometheus_client.check_prometheus_connection() else 'Failed'}")

    except Exception as e:
        print(f"   ❌ Component initialization failed: {e}")
        return False

    # Test 2: Chat endpoint functionality
    print("\n2. Testing Chat Endpoint:")
    test_queries = [
        "How are banking services?",
        "What's the cache status?",
        "Show me system overview"
    ]

    for query in test_queries:
        try:
            print(f"   Testing: '{query}'")
            result = await chat_query(query)

            if result.get("error"):
                print(f"      ❌ Error: {result['error']}")
            else:
                print(f"      ✅ Response received")
                print(f"         PromQL: {result.get('promql_query', 'None')}")
                print(
                    f"         Explanation: {result.get('explanation', 'None')[:100]}...")

        except Exception as e:
            print(f"      ❌ Query failed: {e}")

    # Test 3: Context endpoints
    print("\n3. Testing Context Endpoints:")
    try:
        from api.chat import get_chat_context, get_query_suggestions

        # Test context
        context = await get_chat_context()
        print(
            f"   ✅ Context: {context['services']['total']} services, {context['dashboards']['total_panels']} panels")

        # Test suggestions
        suggestions = await get_query_suggestions()
        print(
            f"   ✅ Suggestions: {len(suggestions.get('suggestions', []))} available")

    except Exception as e:
        print(f"   ❌ Context endpoints failed: {e}")

    # Test 4: Health check
    print("\n4. Testing Health Check:")
    try:
        from api.chat import chat_health
        health = await chat_health()
        print(f"   ✅ Health Status: {health['status']}")
        print(f"   ✅ Components: {health['components']}")

    except Exception as e:
        print(f"   ❌ Health check failed: {e}")

    print("\n" + "="*50)
    print("✅ Chat Integration Test Complete!")
    print("\nNext steps:")
    print("1. Start backend: cd backend && python main.py")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Test chat at: http://localhost:3333")

    return True

if __name__ == "__main__":
    asyncio.run(test_chat_integration())
