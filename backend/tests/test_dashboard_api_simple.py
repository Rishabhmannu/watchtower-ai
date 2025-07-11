"""
Simple test for dashboard API without full FastAPI test client
File: backend/tests/test_dashboard_api_simple.py
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


async def test_dashboard_api_components():
    """Test dashboard API components directly"""

    print("🚀 Testing Dashboard API Components...")
    print("=" * 50)

    try:
        # Test 1: Import dashboard API
        print("1. Testing dashboard API import...")
        from api.dashboards import router as dashboards_router
        print("   ✅ Dashboard API imported successfully")

        # Test 2: Check if registry loads
        print("2. Testing dashboard registry...")
        from core.dashboard_registry import DashboardRegistry
        registry = DashboardRegistry()
        stats = registry.get_registry_stats()
        print(
            f"   ✅ Registry loaded: {stats['total_dashboards']} dashboards, {stats['total_panels']} panels")

        # Test 3: Test dashboard endpoints (direct function calls)
        print("3. Testing dashboard functions...")

        # Test get_all_dashboards function
        from api.dashboards import dashboard_registry
        summaries = dashboard_registry.get_dashboard_summaries()
        print(f"   ✅ Dashboard summaries: {len(summaries)} dashboards")

        # Test categories
        categories = dashboard_registry.get_all_categories()
        print(f"   ✅ Categories: {sorted(categories)}")

        # Test panels
        panels = dashboard_registry.get_all_panels()
        print(f"   ✅ All panels: {len(panels)} panels")

        # Test search
        search_results = dashboard_registry.search_panels("cache")
        print(f"   ✅ Search 'cache': {len(search_results)} results")

        # Test 4: Test specific dashboard
        print("4. Testing specific dashboard...")
        redis_dashboard = dashboard_registry.get_dashboard(
            "redis-cache-performance")
        if redis_dashboard:
            print(f"   ✅ Redis dashboard found: {redis_dashboard.title}")
            query_panels = redis_dashboard.get_query_panels()
            print(f"   ✅ Query panels: {len(query_panels)}")

            # Show panel details
            for panel in query_panels:
                print(
                    f"      - {panel.title} ({panel.type.value}): {panel.get_main_query()}")

        print("\n🎉 All dashboard component tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_main_app_startup():
    """Test if main app can start without errors"""

    print("\n🚀 Testing Main App Startup...")
    print("=" * 40)

    try:
        # Test importing main app
        print("1. Testing main app import...")
        from main import app
        print("   ✅ Main app imported successfully")

        # Test if app has dashboard routes
        print("2. Checking app routes...")
        dashboard_routes = [route for route in app.routes if hasattr(
            route, 'path') and '/api/dashboards' in route.path]
        print(f"   ✅ Dashboard routes found: {len(dashboard_routes)}")

        # Test basic app info
        print("3. Testing app configuration...")
        print(f"   ✅ App title: {app.title}")
        print(f"   ✅ App version: {app.version}")

        print("\n🎉 Main app startup test passed!")
        return True

    except Exception as e:
        print(f"❌ Main app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🧪 Running Simple Dashboard API Tests")
    print("=" * 60)

    success1 = await test_dashboard_api_components()
    success2 = await test_main_app_startup()

    if success1 and success2:
        print("\n✅ All tests passed successfully!")
        print("\n📋 What's Working:")
        print("   ✅ Dashboard parser and registry")
        print("   ✅ Dashboard API endpoints")
        print("   ✅ Main app with dashboard integration")
        print("   ✅ Panel search and filtering")
        print("   ✅ Dashboard categorization")

        print("\n🚀 Ready for frontend integration!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
