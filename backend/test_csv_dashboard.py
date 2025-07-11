#!/usr/bin/env python3
"""
Test script for CSV-based dashboard registry
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.dashboard_registry import DashboardRegistry

def test_dashboard_registry():
    """Test the CSV-based dashboard registry"""
    print("Testing CSV-based Dashboard Registry...")
    
    # Initialize registry
    registry = DashboardRegistry()
    
    # Test basic functionality
    print(f"Registry loaded: {registry.loaded}")
    print(f"Total panels: {len(registry.panels_by_id)}")
    
    # Test getting categories
    categories = registry.get_all_categories()
    print(f"Categories: {categories}")
    
    # Test getting dashboard summaries
    summaries = registry.get_dashboard_summaries()
    print(f"Dashboard summaries: {len(summaries)}")
    for summary in summaries[:3]:  # Show first 3
        print(f"  - {summary['title']} ({summary['category']}) - {summary['panel_count']} panels")
    
    # Test getting panels by category
    if categories:
        first_category = categories[0]
        panels = registry.get_panels_by_category(first_category)
        print(f"Panels in '{first_category}': {len(panels)}")
    
    # Test getting all panels
    all_panels = registry.get_all_panels()
    print(f"All panels: {len(all_panels)}")
    
    # Test search functionality
    search_results = registry.search_panels("cpu")
    print(f"Search results for 'cpu': {len(search_results)}")
    
    # Test getting panel by ID
    if all_panels:
        first_panel_id = all_panels[0]['id']
        panel_data = registry.get_panel_by_id(first_panel_id)
        if panel_data:
            print(f"Panel {first_panel_id}: {panel_data.panel_title}")
            print(f"  Query: {panel_data.metric_query[:50]}...")
    
    # Test getting panels by dashboard UID
    if summaries:
        first_dashboard_uid = summaries[0]['uid']
        dashboard_panels = registry.get_panels_by_dashboard_uid(first_dashboard_uid)
        print(f"Panels for dashboard {first_dashboard_uid}: {len(dashboard_panels)}")
    
    # Test registry stats
    stats = registry.get_registry_stats()
    print(f"Registry stats: {stats}")
    
    print("✅ CSV-based Dashboard Registry test completed successfully!")

if __name__ == "__main__":
    test_dashboard_registry() 