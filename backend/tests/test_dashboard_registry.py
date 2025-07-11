"""
Test dashboard registry functionality
File: backend/tests/test_dashboard_registry.py
"""

from core.dashboard_registry import DashboardRegistry
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_dashboard_registry():
    """Test the dashboard registry functionality"""

    print("🚀 Testing Dashboard Registry...")
    print("=" * 50)

    # Initialize registry
    registry = DashboardRegistry()

    try:
        # Test 1: Basic registry stats
        stats = registry.get_registry_stats()
        print(f"✅ Registry loaded successfully!")
        print(f"   Total dashboards: {stats['total_dashboards']}")
        print(f"   Total panels: {stats['total_panels']}")
        print(f"   Categories: {stats['categories']}")

        # Test 2: Categories
        categories = registry.get_all_categories()
        print(f"\n📊 Categories found: {sorted(categories)}")

        # Test 3: Panel distribution
        print("\n📈 Panels by category:")
        for category, count in stats['panels_by_category'].items():
            print(f"   {category}: {count} panels")

        # Test 4: Dashboard summaries
        print("\n📋 Dashboard summaries:")
        summaries = registry.get_dashboard_summaries()
        for summary in summaries:
            print(
                f"   {summary.title} ({summary.category}): {summary.panel_count} panels")

        # Test 5: Search functionality
        print("\n🔍 Search tests:")

        # Search for cache-related panels
        cache_panels = registry.search_panels("cache")
        print(f"   'cache' search: {len(cache_panels)} results")
        for panel in cache_panels:
            print(f"     - {panel.title} ({panel.get_category_hint()})")

        # Search for kubernetes panels
        k8s_panels = registry.search_panels("replica")
        print(f"   'replica' search: {len(k8s_panels)} results")
        for panel in k8s_panels:
            print(f"     - {panel.title} ({panel.get_category_hint()})")

        # Test 6: Category filtering
        print("\n🏷️ Category filtering tests:")

        cache_category_panels = registry.get_panels_by_category("cache")
        print(f"   Cache category: {len(cache_category_panels)} panels")

        k8s_category_panels = registry.get_panels_by_category("kubernetes")
        print(f"   Kubernetes category: {len(k8s_category_panels)} panels")

        # Test 7: Individual dashboard retrieval
        print("\n📊 Individual dashboard tests:")

        redis_dashboard = registry.get_dashboard("redis-cache-performance")
        if redis_dashboard:
            print(f"   Redis dashboard found: {redis_dashboard.title}")
            print(
                f"   Query panels: {len(redis_dashboard.get_query_panels())}")

        k8s_dashboard = registry.get_dashboard("enhanced-pod-autoscaling")
        if k8s_dashboard:
            print(f"   K8s dashboard found: {k8s_dashboard.title}")
            print(f"   Query panels: {len(k8s_dashboard.get_query_panels())}")

        # Test 8: Panel summaries
        print("\n📝 Panel summaries test:")
        panel_summaries = registry.get_panel_summaries()
        print(f"   Total panel summaries: {len(panel_summaries)}")

        # Show first few panel summaries
        for i, summary in enumerate(panel_summaries[:5]):
            print(f"   {i+1}. {summary.title} ({summary.type})")
            print(f"      Query: {summary.query}")
            print(f"      Unit: {summary.unit}")
            print(f"      Thresholds: {summary.has_thresholds}")
            print()

        # Test 9: Category-specific panel summaries
        cache_summaries = registry.get_panel_summaries("cache")
        print(f"📊 Cache-specific panel summaries: {len(cache_summaries)}")

        print("\n🎉 All registry tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dashboard_registry()
    exit(0 if success else 1)
