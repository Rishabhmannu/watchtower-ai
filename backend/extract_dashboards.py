"""
Dashboard Extraction Script for WatchTower AI
Extracts panel information from Grafana JSON dashboards into CSV format
File: backend/extract_dashboards.py
"""

import json
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardExtractor:
    """Extract dashboard panels from JSON files to CSV format"""
    
    def __init__(self, dashboards_dir: str = "data/dashboards"):
        self.dashboards_dir = Path(dashboards_dir)
        self.panels_data = []
        
        # Category mapping based on filenames
        self.category_mapping = {
            'redis': 'cache',
            'cache': 'cache',
            'database': 'database',
            'db': 'database',
            'kubernetes': 'kubernetes',
            'k8s': 'kubernetes',
            'pod': 'kubernetes',
            'container': 'container',
            'rabbitmq': 'messaging',
            'message': 'messaging',
            'queue': 'messaging',
            'transaction': 'banking',
            'banking': 'banking',
            'ddos': 'security',
            'security': 'security',
            'monitoring': 'security',
            'threat': 'security',
            'auto-baselining': 'security',
            'tracing': 'analytics',
            'analytics': 'analytics'
        }
    
    def detect_category(self, filename: str) -> str:
        """Auto-detect category based on filename"""
        filename_lower = filename.lower()
        
        # Check each category mapping
        for keyword, category in self.category_mapping.items():
            if keyword in filename_lower:
                return category
        
        return 'general'
    
    def extract_all_dashboards(self) -> pd.DataFrame:
        """Extract panels from all dashboard JSON files"""
        logger.info(f"Extracting dashboards from {self.dashboards_dir}")
        
        if not self.dashboards_dir.exists():
            logger.error(f"Dashboard directory {self.dashboards_dir} does not exist")
            print(f"Error: Dashboard directory {self.dashboards_dir} does not exist")
            print("Please make sure you have JSON files in the data/dashboards/ directory")
            return pd.DataFrame()
        
        # Process each JSON file
        json_files = list(self.dashboards_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files")
        
        if not json_files:
            logger.error("No JSON files found in the dashboard directory")
            print("Error: No JSON files found in the dashboard directory")
            print("Please place your dashboard JSON files in data/dashboards/")
            return pd.DataFrame()
        
        for json_file in json_files:
            try:
                self.extract_dashboard_panels(json_file)
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {e}")
        
        # Create DataFrame
        if not self.panels_data:
            logger.error("No panel data extracted from any dashboard files")
            print("Error: No panel data extracted from any dashboard files")
            print("Please check that your JSON files contain valid Grafana dashboard data")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.panels_data)
        logger.info(f"Extracted {len(df)} panel rows from {len(json_files)} dashboards")
        
        return df
    
    def extract_dashboard_panels(self, json_file: Path):
        """Extract panels from a single dashboard JSON file"""
        logger.info(f"Processing {json_file.name}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            dashboard_data = json.load(f)
        
        # Extract dashboard metadata
        dashboard_uid = dashboard_data.get('uid', json_file.stem)
        dashboard_title = dashboard_data.get('title', json_file.stem)
        dashboard_category = self.detect_category(json_file.name)
        
        # Extract panels
        panels = dashboard_data.get('panels', [])
        panel_count = 0
        
        for panel in panels:
            if panel.get('type') == 'row':
                # Skip row panels as they're just layout elements
                continue
                
            panel_count += self.extract_panel_queries(
                panel, dashboard_uid, dashboard_title, dashboard_category
            )
        
        logger.info(f"  → Extracted {panel_count} panels from {dashboard_title}")
    
    def extract_panel_queries(self, panel: Dict, dashboard_uid: str, dashboard_title: str, dashboard_category: str) -> int:
        """Extract queries from a single panel (handles multiple queries per panel)"""
        try:
            panel_id = panel.get('id', 0)
            panel_title = panel.get('title', 'Unknown Panel')
            panel_type = panel.get('type', 'unknown')
            panel_description = panel.get('description', '')
            
            # Extract grid position
            grid_pos = panel.get('gridPos', {})
            grid_x = int(grid_pos.get('x', 0))
            grid_y = int(grid_pos.get('y', 0))
            grid_w = int(grid_pos.get('w', 12))
            grid_h = int(grid_pos.get('h', 8))
            
            # Extract field config for units and thresholds
            field_config = panel.get('fieldConfig', {})
            defaults = field_config.get('defaults', {})
            unit = defaults.get('unit', 'short')
            thresholds = defaults.get('thresholds', {})
            
            # Extract datasource info
            datasource = panel.get('datasource', {})
            datasource_type = datasource.get('type', 'prometheus')
            datasource_uid = datasource.get('uid', '')
            
            # Extract targets (queries)
            targets = panel.get('targets', [])
            query_count = 0
            
            if not targets:
                # Panel has no queries, create one row anyway
                unique_panel_id = f"{dashboard_uid}-{panel_id}"
                
                self.panels_data.append({
                    'dashboard_uid': dashboard_uid,
                    'dashboard_title': dashboard_title,
                    'dashboard_category': dashboard_category,
                    'panel_id': unique_panel_id,
                    'panel_title': panel_title,
                    'panel_type': panel_type,
                    'panel_description': panel_description,
                    'metric_query': '',
                    'query_ref_id': '',
                    'unit': unit,
                    'thresholds_config': json.dumps(thresholds),
                    'grid_x': grid_x,
                    'grid_y': grid_y,
                    'grid_w': grid_w,
                    'grid_h': grid_h,
                    'datasource_type': datasource_type,
                    'datasource_uid': datasource_uid
                })
                return 1
            
            # Process each query/target
            for target in targets:
                expr = target.get('expr', '')
                ref_id = target.get('refId', 'A')
                
                # Skip empty queries
                if not expr:
                    continue
                
                # Create unique panel ID combining dashboard and panel
                unique_panel_id = f"{dashboard_uid}-{panel_id}"
                if len(targets) > 1:
                    # Multiple queries in same panel, make them unique
                    unique_panel_id = f"{dashboard_uid}-{panel_id}-{ref_id}"
                
                self.panels_data.append({
                    'dashboard_uid': dashboard_uid,
                    'dashboard_title': dashboard_title,
                    'dashboard_category': dashboard_category,
                    'panel_id': unique_panel_id,
                    'panel_title': panel_title,
                    'panel_type': panel_type,
                    'panel_description': panel_description,
                    'metric_query': expr,
                    'query_ref_id': ref_id,
                    'unit': unit,
                    'thresholds_config': json.dumps(thresholds),
                    'grid_x': grid_x,
                    'grid_y': grid_y,
                    'grid_w': grid_w,
                    'grid_h': grid_h,
                    'datasource_type': datasource_type,
                    'datasource_uid': datasource_uid
                })
                query_count += 1
            
            return query_count
        
        except Exception as e:
            logger.error(f"Error extracting panel queries: {e}")
            return 0
    
    def save_to_csv(self, df: pd.DataFrame, output_file: str = "data/dashboard_panels.csv"):
        """Save extracted data to CSV file"""
        if df.empty:
            logger.warning("No data to save to CSV")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean the DataFrame before saving
        df_clean = df.copy()
        
        # Replace NaN with empty strings
        df_clean = df_clean.fillna('')
        
        # Replace infinity values with 0
        df_clean = df_clean.replace([float('inf'), float('-inf')], 0)
        
        # Ensure numeric columns are proper integers
        numeric_columns = ['grid_x', 'grid_y', 'grid_w', 'grid_h']
        for col in numeric_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
        
        # Convert all columns to strings to ensure CSV compatibility
        for col in df_clean.columns:
            if col not in numeric_columns:
                df_clean[col] = df_clean[col].astype(str)
        
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df_clean)} panel rows to {output_path}")
        
        # Print summary statistics
        logger.info("Summary Statistics:")
        logger.info(f"  Total panels: {len(df_clean)}")
        logger.info(f"  Categories: {df_clean['dashboard_category'].value_counts().to_dict()}")
        logger.info(f"  Panel types: {df_clean['panel_type'].value_counts().to_dict()}")
        logger.info(f"  Dashboards: {df_clean['dashboard_uid'].nunique()}")

def main():
    """Main extraction function"""
    try:
        extractor = DashboardExtractor()
        
        # Extract all dashboards
        df = extractor.extract_all_dashboards()
        
        if df.empty:
            logger.error("No data extracted. Check your dashboard files.")
            print("No data extracted. Please check that:")
            print("1. Dashboard JSON files exist in data/dashboards/")
            print("2. JSON files are valid and contain panels")
            print("3. Run the script from the backend directory")
            return
        
        # Save to CSV
        extractor.save_to_csv(df)
        
        # Display first few rows
        print("\nFirst 5 rows of extracted data:")
        print(df.head().to_string())
        
        print(f"\nExtraction complete! CSV file created with {len(df)} panels.")
        print("You can now restart your backend server to load the new data.")
        
    except Exception as e:
        logger.error(f"Error in main extraction: {e}")
        print(f"Error during extraction: {e}")
        print("Please check the logs and your dashboard files.")

if __name__ == "__main__":
    main()
