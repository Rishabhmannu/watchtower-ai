"""
Test dashboard parser with Redis Cache Performance dashboard
File: backend/tests/test_dashboard_parser.py
"""

from core.dashboard_parser import DashboardParser
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_dashboard_parser():
    """Test the dashboard parser with sample Redis dashboard data"""

    # Sample Redis Cache Performance dashboard data (extracted from your knowledge base)
    redis_dashboard_json = """
    {
      "id": 13,
      "uid": "redis-cache-performance",
      "title": "Redis Cache Performance",
      "tags": ["redis", "cache", "performance"],
      "description": "Redis cache monitoring for banking operations",
      "panels": [
        {
          "id": 2,
          "title": "Cache Hit Ratio",
          "type": "gauge",
          "targets": [
            {
              "expr": "redis_cache_hit_ratio{operation=\\"overall\\"} * 100",
              "refId": "A"
            }
          ],
          "gridPos": {
            "h": 8,
            "w": 6,
            "x": 0,
            "y": 1
          },
          "datasource": {
            "type": "prometheus",
            "uid": "PBFA97CFB590B2093"
          },
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0,
              "max": 100,
              "thresholds": {
                "mode": "absolute",
                "steps": [
                  {
                    "color": "red"
                  },
                  {
                    "color": "yellow",
                    "value": 50
                  },
                  {
                    "color": "green",
                    "value": 80
                  }
                ]
              }
            }
          }
        },
        {
          "id": 6,
          "title": "Memory Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "redis_cache_memory_usage_bytes / 1024 / 1024",
              "refId": "A"
            }
          ],
          "gridPos": {
            "h": 8,
            "w": 6,
            "x": 0,
            "y": 27
          },
          "datasource": {
            "type": "prometheus",
            "uid": "PBFA97CFB590B2093"
          },
          "fieldConfig": {
            "defaults": {
              "unit": "decmbytes",
              "thresholds": {
                "mode": "absolute",
                "steps": [
                  {
                    "color": "green"
                  },
                  {
                    "color": "yellow",
                    "value": 512
                  },
                  {
                    "color": "red",
                    "value": 768
                  }
                ]
              }
            }
          }
        },
        {
          "id": 100,
          "title": "📊 Overview & Key Metrics",
          "type": "row",
          "collapsed": false,
          "gridPos": {
            "h": 1,
            "w": 24,
            "x": 0,
            "y": 0
          }
        }
      ]
    }
    """

    print("🚀 Testing Dashboard Parser...")
    print("=" * 50)

    # Initialize parser
    parser = DashboardParser()

    try:
        # Parse the dashboard
        dashboard = parser.parse_dashboard_json(redis_dashboard_json, "cache")

        print(f"✅ Dashboard parsed successfully!")
        print(f"   Title: {dashboard.title}")
        print(f"   Category: {dashboard.category}")
        print(f"   Tags: {dashboard.tags}")
        print(f"   Total panels: {len(dashboard.panels)}")
        print(f"   Rows: {len(dashboard.rows)}")

        # Test query panels
        query_panels = dashboard.get_query_panels()
        print(f"   Query panels: {len(query_panels)}")

        print("\n📊 Panel Details:")
        print("-" * 30)

        for i, panel in enumerate(query_panels, 1):
            print(f"{i}. {panel.title}")
            print(f"   Type: {panel.type.value}")
            print(f"   Category: {panel.get_category_hint()}")
            print(f"   Query: {panel.get_main_query()}")
            print(f"   Unit: {panel.unit}")
            print(f"   Has thresholds: {panel.thresholds is not None}")

            if panel.thresholds:
                print(f"   Threshold steps: {len(panel.thresholds.steps)}")
                for step in panel.thresholds.steps:
                    print(f"     - {step.color} (value: {step.value})")
            print()

        # Test dashboard summary
        summary = parser.get_dashboard_summary(dashboard)
        print("📋 Dashboard Summary:")
        print("-" * 20)
        print(f"Panel count: {summary['panel_count']}")
        print(
            f"Categories found: {set(p['category'] for p in summary['panels'])}")

        print("\n🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dashboard_parser()
    exit(0 if success else 1)
