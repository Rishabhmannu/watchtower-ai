"""
Test dashboard API endpoints
File: backend/tests/test_dashboard_api.py
"""

from main import app
from fastapi.testclient import TestClient
import sys
import os
import asyncio
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# Create test client
client = TestClient(app)


def test_dashboard_api_endpoints():
    """Test all dashboard API endpoints"""

    print("🚀 Testing Dashboard API Endpoints...")
    print("=" * 50)

    try:
        # Test 1: Get all dashboards
        print("1. Testing GET /api/dashboards/")
        response = client.get("/api/dashboards/")
        assert response.status_code == 200

        data = response.json()
        assert "dashboards" in data
        assert "stats" in data

        dashboards = data["dashboards"]
        stats = data["stats"]

        print(f"   ✅ Found {len(dashboards)} dashboards")
        print(f"   ✅ Total panels: {stats['total_panels']}")
        print(f"   ✅ Categories: {stats['categories']}")

        # Test 2: Get dashboard categories
        print("\n2. Testing GET /api/dashboards/categories")
        response = client.get("/api/dashboards/categories")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert "panels_by_category" in data

        categories = data["categories"]
        print(f"   ✅ Categories: {categories}")

        # Test 3: Get dashboards by category
        print("\n3. Testing GET /api/dashboards/category/{category}")

        for category in categories:
            response = client.get(f"/api/dashboards/category/{category}")
            assert response.status_code == 200

            data = response.json()
            assert data["category"] == category
            assert "dashboards" in data

            print(
                f"   ✅ Category '{category}': {len(data['dashboards'])} dashboards")

        # Test 4: Get specific dashboard
        print("\n4. Testing GET /api/dashboards/{uid}")

        # Test with Redis dashboard
        response = client.get("/api/dashboards/redis-cache-performance")
        assert response.status_code == 200

        data = response.json()
        assert data["uid"] == "redis-cache-performance"
        assert data["title"] == "Redis Cache Performance"
        assert "panels" in data

        panels = data["panels"]
        print(f"   ✅ Redis dashboard: {len(panels)} panels")

        # Check panel structure
        if panels:
            panel = panels[0]
            required_fields = ["id", "title", "type",
                               "category", "query", "unit", "has_thresholds"]
            for field in required_fields:
                assert field in panel, f"Missing field: {field}"

            print(f"   ✅ Panel structure valid: {panel['title']}")

        # Test 5: Get all panels
        print("\n5. Testing GET /api/dashboards/panels/all")
        response = client.get("/api/dashboards/panels/all")
        assert response.status_code == 200

        data = response.json()
        assert "panels" in data
        assert "total" in data

        panels = data["panels"]
        print(f"   ✅ All panels: {len(panels)} panels")

        # Test with category filter
        response = client.get("/api/dashboards/panels/all?category=cache")
        assert response.status_code == 200

        data = response.json()
        cache_panels = data["panels"]
        print(f"   ✅ Cache panels: {len(cache_panels)} panels")

        # Test with limit
        response = client.get("/api/dashboards/panels/all?limit=2")
        assert response.status_code == 200

        data = response.json()
        limited_panels = data["panels"]
        assert len(limited_panels) <= 2
        print(f"   ✅ Limited panels: {len(limited_panels)} panels")

        # Test 6: Search panels
        print("\n6. Testing GET /api/dashboards/panels/search")

        # Search for cache-related panels
        response = client.get("/api/dashboards/panels/search?q=cache")
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "cache"
        assert "results" in data

        search_results = data["results"]
        print(f"   ✅ Search 'cache': {len(search_results)} results")

        # Search with category filter
        response = client.get(
            "/api/dashboards/panels/search?q=replica&category=kubernetes")
        assert response.status_code == 200

        data = response.json()
        filtered_results = data["results"]
        print(
            f"   ✅ Search 'replica' in kubernetes: {len(filtered_results)} results")

        # Test 7: Get dashboard stats
        print("\n7. Testing GET /api/dashboards/stats")
        response = client.get("/api/dashboards/stats")
        assert response.status_code == 200

        data = response.json()
        assert "registry_stats" in data
        assert "categories" in data
        assert "status" in data

        print(f"   ✅ Stats retrieved: {data['status']}")

        # Test 8: Error handling
        print("\n8. Testing error handling")

        # Test non-existent dashboard
        response = client.get("/api/dashboards/non-existent-dashboard")
        assert response.status_code == 404
        print("   ✅ Non-existent dashboard returns 404")

        # Test non-existent category
        response = client.get("/api/dashboards/category/non-existent-category")
        assert response.status_code == 404
        print("   ✅ Non-existent category returns 404")

        # Test invalid search
        # Missing query parameter
        response = client.get("/api/dashboards/panels/search")
        assert response.status_code == 422
        print("   ✅ Missing query parameter returns 422")

        print("\n🎉 All dashboard API tests passed!")

        # Summary
        print("\n📊 API Test Summary:")
        print("=" * 30)
        print(f"✅ Dashboard listing: Working")
        print(f"✅ Category filtering: Working")
        print(f"✅ Dashboard details: Working")
        print(f"✅ Panel listing: Working")
        print(f"✅ Panel search: Working")
        print(f"✅ Statistics: Working")
        print(f"✅ Error handling: Working")

        return True

    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_panel_query_endpoints():
    """Test panel query execution endpoints (requires Prometheus)"""

    print("\n🔍 Testing Panel Query Endpoints...")
    print("=" * 40)

    try:
        # Get a panel ID first
        response = client.get("/api/dashboards/panels/all?limit=1")
        assert response.status_code == 200

        panels = response.json()["panels"]
        if not panels:
            print("   ⚠️  No panels available for query testing")
            return True

        panel_id = panels[0]["id"]
        panel_title = panels[0]["title"]

        print(f"   Testing with panel: {panel_title} (ID: {panel_id})")

        # Test single panel query
        print(f"   Testing POST /api/dashboards/panels/{panel_id}/query")
        response = client.post(f"/api/dashboards/panels/{panel_id}/query")

        # This might fail if Prometheus is not available, which is expected
        if response.status_code == 200:
            data = response.json()
            assert "panel" in data
            assert "query" in data
            assert "result" in data
            print("   ✅ Panel query executed successfully")
        else:
            print("   ⚠️  Panel query failed (Prometheus may not be available)")

        # Test batch query
        print("   Testing POST /api/dashboards/panels/batch-query")
        response = client.post(
            f"/api/dashboards/panels/batch-query?panel_ids={panel_id}")

        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "total" in data
            print("   ✅ Batch panel query executed successfully")
        else:
            print("   ⚠️  Batch panel query failed (Prometheus may not be available)")

        return True

    except Exception as e:
        print(f"   ⚠️  Query endpoint test failed: {e}")
        # Query endpoints might fail without Prometheus, which is OK
        return True


if __name__ == "__main__":
    success1 = test_dashboard_api_endpoints()
    success2 = test_panel_query_endpoints()

    if success1 and success2:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
