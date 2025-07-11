"""
Dashboard parser for converting Grafana JSON to structured data
File: backend/core/dashboard_parser.py
"""

import json
import logging
from typing import Dict, List, Optional, Any
from models.dashboard_models import (
    Dashboard, DashboardPanel, DashboardRow, Target, GridPos,
    Threshold, ThresholdStep, PanelType, ThresholdMode
)

logger = logging.getLogger(__name__)


class DashboardParser:
    """Parser for Grafana dashboard JSON files"""

    def __init__(self):
        self.supported_panel_types = {
            "gauge", "stat", "timeseries", "table", "piechart",
            "bargauge", "heatmap", "row"
        }

    def parse_dashboard_json(self, json_content: str, category: str = "general") -> Dashboard:
        """Parse a Grafana dashboard JSON string into Dashboard object"""
        try:
            data = json.loads(json_content)
            return self._parse_dashboard_data(data, category)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error(f"Failed to parse dashboard: {e}")
            raise ValueError(f"Dashboard parsing error: {e}")

    def _parse_dashboard_data(self, data: Dict[str, Any], category: str) -> Dashboard:
        """Parse dashboard data dictionary"""
        # Extract basic dashboard info
        dashboard_id = data.get("id", 0)
        uid = data.get("uid", f"dashboard_{dashboard_id}")
        title = data.get("title", "Unknown Dashboard")
        tags = data.get("tags", [])
        description = data.get("description")

        # Parse panels
        panels = []
        rows = []

        panels_data = data.get("panels", [])
        for panel_data in panels_data:
            try:
                if panel_data.get("type") == "row":
                    row = self._parse_row(panel_data)
                    rows.append(row)
                else:
                    panel = self._parse_panel(panel_data)
                    if panel:
                        panels.append(panel)
            except Exception as e:
                logger.warning(
                    f"Failed to parse panel {panel_data.get('id', 'unknown')}: {e}")
                continue

        # Auto-detect category if not provided
        if category == "general":
            category = self._detect_category(title, tags, panels)

        return Dashboard(
            id=dashboard_id,
            uid=uid,
            title=title,
            tags=tags,
            panels=panels,
            rows=rows,
            description=description,
            category=category
        )

    def _parse_panel(self, panel_data: Dict[str, Any]) -> Optional[DashboardPanel]:
        """Parse individual panel data"""
        panel_id = panel_data.get("id", 0)
        title = panel_data.get("title", "Unknown Panel")
        panel_type = panel_data.get("type", "stat")

        # Skip unsupported panel types
        if panel_type not in self.supported_panel_types:
            logger.warning(f"Unsupported panel type: {panel_type}")
            return None

        # Parse targets (PromQL queries)
        targets = []
        targets_data = panel_data.get("targets", [])
        for target_data in targets_data:
            target = self._parse_target(target_data)
            if target:
                targets.append(target)

        # Parse grid position
        grid_pos_data = panel_data.get("gridPos", {})
        grid_pos = GridPos(
            h=grid_pos_data.get("h", 8),
            w=grid_pos_data.get("w", 12),
            x=grid_pos_data.get("x", 0),
            y=grid_pos_data.get("y", 0)
        )

        # Parse datasource
        datasource = panel_data.get("datasource", {})

        # Parse thresholds
        thresholds = self._parse_thresholds(panel_data)

        # Parse field config for units and limits
        field_config = panel_data.get("fieldConfig", {})
        defaults = field_config.get("defaults", {})

        unit = defaults.get("unit")
        min_value = defaults.get("min")
        max_value = defaults.get("max")
        description = panel_data.get("description")

        return DashboardPanel(
            id=panel_id,
            title=title,
            type=PanelType(panel_type),
            targets=targets,
            gridPos=grid_pos,
            datasource=datasource,
            description=description,
            unit=unit,
            thresholds=thresholds,
            min_value=min_value,
            max_value=max_value
        )

    def _parse_target(self, target_data: Dict[str, Any]) -> Optional[Target]:
        """Parse PromQL target/query"""
        expr = target_data.get("expr")
        if not expr:
            return None

        ref_id = target_data.get("refId", "A")
        legend_format = target_data.get("legendFormat")
        interval = target_data.get("interval")
        instant = target_data.get("instant", False)

        return Target(
            expr=expr,
            refId=ref_id,
            legendFormat=legend_format,
            interval=interval,
            instant=instant
        )

    def _parse_thresholds(self, panel_data: Dict[str, Any]) -> Optional[Threshold]:
        """Parse panel thresholds"""
        try:
            field_config = panel_data.get("fieldConfig", {})
            defaults = field_config.get("defaults", {})
            thresholds_data = defaults.get("thresholds", {})

            if not thresholds_data:
                return None

            mode = thresholds_data.get("mode", "absolute")
            steps_data = thresholds_data.get("steps", [])

            steps = []
            for step_data in steps_data:
                step = ThresholdStep(
                    color=step_data.get("color", "green"),
                    value=step_data.get("value")
                )
                steps.append(step)

            return Threshold(
                mode=ThresholdMode(mode),
                steps=steps
            )
        except Exception as e:
            logger.warning(f"Failed to parse thresholds: {e}")
            return None

    def _parse_row(self, row_data: Dict[str, Any]) -> DashboardRow:
        """Parse dashboard row"""
        row_id = row_data.get("id", 0)
        title = row_data.get("title", "")
        collapsed = row_data.get("collapsed", False)

        return DashboardRow(
            id=row_id,
            title=title,
            collapsed=collapsed
        )

    def _detect_category(self, title: str, tags: List[str], panels: List[DashboardPanel]) -> str:
        """Auto-detect dashboard category"""
        title_lower = title.lower()
        tags_lower = [tag.lower() for tag in tags]

        # Check title for category hints
        if "redis" in title_lower or "cache" in title_lower:
            return "cache"
        elif "kubernetes" in title_lower or "k8s" in title_lower or "pod" in title_lower:
            return "kubernetes"
        elif "database" in title_lower or "db" in title_lower or "postgres" in title_lower:
            return "database"
        elif "rabbitmq" in title_lower or "message" in title_lower or "queue" in title_lower:
            return "messaging"
        elif "transaction" in title_lower or "banking" in title_lower:
            return "banking"
        elif "ddos" in title_lower or "security" in title_lower or "detection" in title_lower:
            return "security"
        elif "container" in title_lower or "docker" in title_lower:
            return "container"

        # Check tags
        for tag in tags_lower:
            if tag in ["redis", "cache"]:
                return "cache"
            elif tag in ["kubernetes", "k8s", "pod"]:
                return "kubernetes"
            elif tag in ["database", "db", "postgres"]:
                return "database"
            elif tag in ["rabbitmq", "message", "queue"]:
                return "messaging"
            elif tag in ["banking", "transaction"]:
                return "banking"
            elif tag in ["security", "ddos", "detection"]:
                return "security"
            elif tag in ["container", "docker"]:
                return "container"

        # Check panel queries for hints
        category_hints = {}
        for panel in panels:
            category = panel.get_category_hint()
            category_hints[category] = category_hints.get(category, 0) + 1

        # Return most common category hint
        if category_hints:
            return max(category_hints, key=category_hints.get)

        return "general"

    def get_dashboard_summary(self, dashboard: Dashboard) -> Dict[str, Any]:
        """Get dashboard summary for API responses"""
        query_panels = dashboard.get_query_panels()

        return {
            "id": dashboard.id,
            "uid": dashboard.uid,
            "title": dashboard.title,
            "category": dashboard.category,
            "panel_count": len(query_panels),
            "tags": dashboard.tags,
            "description": dashboard.description,
            "panels": [
                {
                    "id": panel.id,
                    "title": panel.title,
                    "type": panel.type.value,
                    "category": panel.get_category_hint(),
                    "query": panel.get_main_query(),
                    "description": panel.description,
                    "unit": panel.unit,
                    "has_thresholds": panel.thresholds is not None
                }
                for panel in query_panels
            ]
        }
