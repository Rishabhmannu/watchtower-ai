"""
CSV-based Dashboard Registry for WatchTower AI
Loads dashboard panels from CSV instead of parsing JSON files
File: backend/core/dashboard_registry.py
"""

import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PanelData:
    """Simple data class for panel information"""
    dashboard_uid: str
    dashboard_title: str
    dashboard_category: str
    panel_id: str
    panel_title: str
    panel_type: str
    panel_description: str
    metric_query: str
    query_ref_id: str
    unit: str
    thresholds_config: str
    grid_x: int
    grid_y: int
    grid_w: int
    grid_h: int
    datasource_type: str
    datasource_uid: str

class DashboardRegistry:
    """CSV-based dashboard registry for managing all banking system dashboards"""
    
    def __init__(self, csv_file: str = "data/dashboard_panels.csv"):
        self.csv_file = Path(csv_file)
        self.df: Optional[pd.DataFrame] = None
        self.panels_by_id: Dict[str, PanelData] = {}
        self.loaded = False
        
        # Load CSV data
        self.load_dashboard_data()
    
    def load_dashboard_data(self):
        """Load dashboard panel data from CSV file"""
        try:
            if not self.csv_file.exists():
                logger.warning(f"CSV file {self.csv_file} does not exist. Run extract_dashboards.py first.")
                # Create empty DataFrame to prevent errors
                self.df = pd.DataFrame()
                return
            
            # Load CSV with proper handling of NaN values
            self.df = pd.read_csv(self.csv_file)
            logger.info(f"Loaded {len(self.df)} panels from {self.csv_file}")
            
            # Clean the DataFrame - replace NaN/inf values with defaults
            self.df = self.df.fillna('')  # Fill NaN with empty strings
            self.df = self.df.replace([float('inf'), float('-inf')], 0)  # Replace inf with 0
            
            # Ensure numeric columns are proper integers
            numeric_columns = ['grid_x', 'grid_y', 'grid_w', 'grid_h']
            for col in numeric_columns:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0).astype(int)
            
            # Create panels_by_id dictionary for quick lookup
            self.panels_by_id = {}
            for _, row in self.df.iterrows():
                panel_data = PanelData(
                    dashboard_uid=str(row['dashboard_uid']),
                    dashboard_title=str(row['dashboard_title']),
                    dashboard_category=str(row['dashboard_category']),
                    panel_id=str(row['panel_id']),
                    panel_title=str(row['panel_title']),
                    panel_type=str(row['panel_type']),
                    panel_description=str(row['panel_description']),
                    metric_query=str(row['metric_query']),
                    query_ref_id=str(row['query_ref_id']),
                    unit=str(row['unit']),
                    thresholds_config=str(row['thresholds_config']),
                    grid_x=int(row['grid_x']),
                    grid_y=int(row['grid_y']),
                    grid_w=int(row['grid_w']),
                    grid_h=int(row['grid_h']),
                    datasource_type=str(row['datasource_type']),
                    datasource_uid=str(row['datasource_uid'])
                )
                self.panels_by_id[panel_data.panel_id] = panel_data
            
            self.loaded = True
            logger.info(f"Indexed {len(self.panels_by_id)} panels by ID")
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
            self.df = pd.DataFrame()
            self.loaded = False
    
    def get_panel_by_id(self, panel_id: str) -> Optional[PanelData]:
        """Get panel by ID"""
        return self.panels_by_id.get(panel_id)
    
    def get_panels_by_category(self, category: str) -> List[PanelData]:
        """Get all panels in a category"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            filtered_df = self.df[self.df['dashboard_category'] == category]
            return [self.panels_by_id[panel_id] for panel_id in filtered_df['panel_id'].tolist() if panel_id in self.panels_by_id]
        except Exception as e:
            logger.error(f"Error getting panels by category: {e}")
            return []
    
    def get_panels_by_dashboard_uid(self, dashboard_uid: str) -> List[Dict[str, Any]]:
        """Get all panels for a specific dashboard UID"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            filtered_df = self.df[self.df['dashboard_uid'] == dashboard_uid]
            
            panels = []
            for _, row in filtered_df.iterrows():
                panels.append({
                    'id': str(row['panel_id']),
                    'title': str(row['panel_title']),
                    'type': str(row['panel_type']),
                    'category': str(row['dashboard_category']),
                    'query': str(row['metric_query']),
                    'description': str(row['panel_description']),
                    'unit': str(row['unit']),
                    'has_thresholds': bool(row['thresholds_config'] and row['thresholds_config'] != '{}'),
                    'dashboard_title': str(row['dashboard_title']),
                    'dashboard_uid': str(row['dashboard_uid'])
                })
            
            return panels
        except Exception as e:
            logger.error(f"Error getting panels by dashboard UID: {e}")
            return []
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            return sorted(self.df['dashboard_category'].unique().tolist())
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_dashboards_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get dashboard summaries by category"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            filtered_df = self.df[self.df['dashboard_category'] == category]
            
            # Group by dashboard to get unique dashboards
            dashboards = []
            for dashboard_uid, group in filtered_df.groupby('dashboard_uid'):
                dashboard_info = group.iloc[0]  # Get first row for dashboard info
                dashboards.append({
                    'uid': str(dashboard_info['dashboard_uid']),
                    'title': str(dashboard_info['dashboard_title']),
                    'category': str(dashboard_info['dashboard_category']),
                    'panel_count': len(group)
                })
            
            return dashboards
        except Exception as e:
            logger.error(f"Error getting dashboards by category: {e}")
            return []
    
    def get_dashboard_summaries(self) -> List[Dict[str, Any]]:
        """Get all dashboard summaries"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            summaries = []
            for dashboard_uid, group in self.df.groupby('dashboard_uid'):
                dashboard_info = group.iloc[0]  # Get first row for dashboard info
                summaries.append({
                    'id': len(summaries) + 1,  # Generate sequential ID
                    'uid': str(dashboard_info['dashboard_uid']),
                    'title': str(dashboard_info['dashboard_title']),
                    'category': str(dashboard_info['dashboard_category']),
                    'panel_count': len(group),
                    'tags': [str(dashboard_info['dashboard_category'])],
                    'description': f"Dashboard with {len(group)} panels"
                })
            return summaries
        except Exception as e:
            logger.error(f"Error getting dashboard summaries: {e}")
            return []
    
    def get_all_panels(self) -> List[Dict[str, Any]]:
        """Get all panels with their information"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            panels = []
            for _, row in self.df.iterrows():
                panels.append({
                    'id': str(row['panel_id']),
                    'title': str(row['panel_title']),
                    'type': str(row['panel_type']),
                    'category': str(row['dashboard_category']),
                    'query': str(row['metric_query']),
                    'description': str(row['panel_description']),
                    'unit': str(row['unit']),
                    'has_thresholds': bool(row['thresholds_config'] and row['thresholds_config'] != '{}'),
                    'dashboard_title': str(row['dashboard_title']),
                    'dashboard_uid': str(row['dashboard_uid'])
                })
            
            return panels
        except Exception as e:
            logger.error(f"Error getting all panels: {e}")
            return []
    
    def search_panels(self, query: str) -> List[Dict[str, Any]]:
        """Search panels by query string"""
        if self.df is None or self.df.empty:
            return []
        
        try:
            query_lower = query.lower()
            
            # Search in panel title, description, and metric query
            mask = (
                self.df['panel_title'].str.lower().str.contains(query_lower, na=False) |
                self.df['panel_description'].str.lower().str.contains(query_lower, na=False) |
                self.df['metric_query'].str.lower().str.contains(query_lower, na=False) |
                self.df['dashboard_title'].str.lower().str.contains(query_lower, na=False)
            )
            
            filtered_df = self.df[mask]
            
            results = []
            for _, row in filtered_df.iterrows():
                results.append({
                    'id': str(row['panel_id']),
                    'title': str(row['panel_title']),
                    'type': str(row['panel_type']),
                    'category': str(row['dashboard_category']),
                    'query': str(row['metric_query']),
                    'description': str(row['panel_description']),
                    'dashboard_title': str(row['dashboard_title'])
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching panels: {e}")
            return []
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        if self.df is None or self.df.empty:
            return {
                'total_panels': 0,
                'total_dashboards': 0,
                'categories': {},
                'panel_types': {},
                'panels_by_category': {},
                'loaded': self.loaded,
                'error': 'No dashboard data loaded. Run extract_dashboards.py first.'
            }
        
        try:
            stats = {
                'total_panels': len(self.df),
                'total_dashboards': self.df['dashboard_uid'].nunique(),
                'categories': self.df['dashboard_category'].value_counts().to_dict(),
                'panel_types': self.df['panel_type'].value_counts().to_dict(),
                'panels_by_category': self.df.groupby('dashboard_category').size().to_dict(),
                'loaded': self.loaded
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting registry stats: {e}")
            return {
                'total_panels': 0,
                'total_dashboards': 0,
                'categories': {},
                'panel_types': {},
                'panels_by_category': {},
                'loaded': False,
                'error': str(e)
            }
    
    def get_panel_query(self, panel_id: str) -> Optional[str]:
        """Get the metric query for a specific panel"""
        panel = self.get_panel_by_id(panel_id)
        return panel.metric_query if panel else None
    
    def get_panel_thresholds(self, panel_id: str) -> Optional[Dict]:
        """Get thresholds configuration for a panel"""
        panel = self.get_panel_by_id(panel_id)
        if not panel or not panel.thresholds_config:
            return None
        
        try:
            return json.loads(panel.thresholds_config)
        except json.JSONDecodeError:
            logger.error(f"Error parsing thresholds for panel {panel_id}")
            return None

# Legacy compatibility class for existing code
class DashboardPanel:
    """Legacy compatibility class"""
    
    def __init__(self, panel_data: PanelData):
        self.id = panel_data.panel_id
        self.title = panel_data.panel_title
        self.type = panel_data.panel_type
        self.metric_query = panel_data.metric_query
        self.unit = panel_data.unit
        self.thresholds = self._parse_thresholds(panel_data.thresholds_config)
    
    def get_main_query(self) -> str:
        """Get the main metric query"""
        return self.metric_query
    
    def get_category_hint(self) -> str:
        """Get category hint"""
        return "general"
    
    def _parse_thresholds(self, thresholds_config: str) -> Optional[Dict]:
        """Parse thresholds configuration"""
        if not thresholds_config:
            return None
        
        try:
            return json.loads(thresholds_config)
        except json.JSONDecodeError:
            return None

# Compatibility wrapper for existing API
def get_legacy_panel_by_id(registry: DashboardRegistry, panel_id: str) -> Optional[DashboardPanel]:
    """Get panel in legacy format for API compatibility"""
    panel_data = registry.get_panel_by_id(panel_id)
    if not panel_data:
        return None
    
    return DashboardPanel(panel_data)
