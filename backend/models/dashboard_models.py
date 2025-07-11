"""
Dashboard data models for WatchTower AI
File: backend/models/dashboard_models.py
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PanelType(str, Enum):
    """Types of dashboard panels"""
    GAUGE = "gauge"
    STAT = "stat"
    TIMESERIES = "timeseries"
    TABLE = "table"
    PIECHART = "piechart"
    BARGAUGE = "bargauge"
    HEATMAP = "heatmap"
    ROW = "row"


class ThresholdMode(str, Enum):
    """Threshold evaluation modes"""
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"


@dataclass
class ThresholdStep:
    """Individual threshold step"""
    color: str
    value: Optional[float] = None


@dataclass
class Threshold:
    """Panel threshold configuration"""
    mode: ThresholdMode
    steps: List[ThresholdStep]


@dataclass
class Target:
    """PromQL query target"""
    expr: str
    refId: str
    legendFormat: Optional[str] = None
    interval: Optional[str] = None
    instant: bool = False


@dataclass
class GridPos:
    """Panel grid position"""
    h: int  # height
    w: int  # width
    x: int  # x position
    y: int  # y position


@dataclass
class DashboardPanel:
    """Individual dashboard panel"""
    id: int
    title: str
    type: PanelType
    targets: List[Target]
    gridPos: GridPos
    datasource: Dict[str, Any]
    description: Optional[str] = None
    unit: Optional[str] = None
    thresholds: Optional[Threshold] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def get_main_query(self) -> Optional[str]:
        """Get the main PromQL query for this panel"""
        if self.targets:
            return self.targets[0].expr
        return None

    def get_category_hint(self) -> str:
        """Get category hint based on panel title and queries"""
        title_lower = self.title.lower()
        query = self.get_main_query() or ""

        if "redis" in title_lower or "cache" in title_lower or "redis" in query:
            return "cache"
        elif "kubernetes" in title_lower or "k8s" in title_lower or "kube" in query:
            return "kubernetes"
        elif "database" in title_lower or "db" in title_lower or "postgres" in query:
            return "database"
        elif "rabbitmq" in title_lower or "message" in title_lower or "queue" in query:
            return "messaging"
        elif "transaction" in title_lower or "banking" in title_lower:
            return "banking"
        elif "ddos" in title_lower or "security" in title_lower or "detection" in query:
            return "security"
        elif "container" in title_lower or "docker" in title_lower or "cadvisor" in query:
            return "container"
        else:
            return "general"


@dataclass
class DashboardRow:
    """Dashboard row grouping"""
    id: int
    title: str
    collapsed: bool = False
    panels: List[DashboardPanel] = None

    def __post_init__(self):
        if self.panels is None:
            self.panels = []


@dataclass
class Dashboard:
    """Complete dashboard structure"""
    id: int
    uid: str
    title: str
    tags: List[str]
    panels: List[DashboardPanel]
    rows: List[DashboardRow]
    description: Optional[str] = None
    category: Optional[str] = None

    def __post_init__(self):
        if self.panels is None:
            self.panels = []
        if self.rows is None:
            self.rows = []

    def get_panel_by_id(self, panel_id: int) -> Optional[DashboardPanel]:
        """Get panel by ID"""
        for panel in self.panels:
            if panel.id == panel_id:
                return panel
        return None

    def get_panels_by_type(self, panel_type: PanelType) -> List[DashboardPanel]:
        """Get all panels of a specific type"""
        return [panel for panel in self.panels if panel.type == panel_type]

    def get_panels_by_category(self, category: str) -> List[DashboardPanel]:
        """Get panels that match a category"""
        return [panel for panel in self.panels if panel.get_category_hint() == category]

    def get_query_panels(self) -> List[DashboardPanel]:
        """Get panels that have PromQL queries (excluding rows)"""
        return [panel for panel in self.panels if panel.type != PanelType.ROW and panel.targets]

    def get_panel_count(self) -> int:
        """Get total number of queryable panels"""
        return len(self.get_query_panels())


@dataclass
class DashboardSummary:
    """Dashboard summary for API responses"""
    id: int
    uid: str
    title: str
    category: str
    panel_count: int
    tags: List[str]
    description: Optional[str] = None


@dataclass
class PanelSummary:
    """Panel summary for API responses"""
    id: int
    title: str
    type: str
    category: str
    query: Optional[str]
    description: Optional[str] = None
    unit: Optional[str] = None
    has_thresholds: bool = False
