/**
 * Dashboard TypeScript types for frontend
 * File: frontend/src/types/dashboard.ts
 */

export interface ThresholdStep {
  color: string;
  value?: number;
}

export interface Threshold {
  mode: 'absolute' | 'percentage';
  steps: ThresholdStep[];
}

export interface GridPos {
  h: number;
  w: number;
  x: number;
  y: number;
}

export interface DashboardPanel {
  id: number;
  title: string;
  type: 'gauge' | 'stat' | 'timeseries' | 'table' | 'piechart' | 'bargauge' | 'heatmap';
  category: string;
  query: string;
  description?: string;
  unit?: string;
  has_thresholds: boolean;
  thresholds?: Threshold;
  grid_pos?: GridPos;
}

export interface Dashboard {
  id: number;
  uid: string;
  title: string;
  category: string;
  panel_count: number;
  tags: string[];
  description?: string;
  panels: DashboardPanel[];
}

export interface DashboardSummary {
  id: number;
  uid: string;
  title: string;
  category: string;
  panel_count: number;
  tags: string[];
  description?: string;
}

export interface PanelQueryResult {
  panel: {
    id: number;
    title: string;
    type: string;
    category: string;
    query: string;
    unit?: string;
    has_thresholds: boolean;
  };
  query: string;
  time_range: string;
  result: {
    status: string;
    data?: {
      status: string;
      data?: {
        result: Array<{
          metric: Record<string, string>;
          value: [number, string];
        }>;
      };
    };
  };
  health_status: 'healthy' | 'warning' | 'critical' | 'unknown' | 'no_data' | 'unhealthy';
  timestamp?: string;
}

export interface DashboardStats {
  total_dashboards: number;
  total_panels: number;
  categories: number;
  panels_by_category: Record<string, number>;
}

export interface DashboardApiResponse {
  dashboards: DashboardSummary[];
  stats: DashboardStats;
}

export interface PanelSearchResult {
  id: number;
  title: string;
  type: string;
  category: string;
  query: string;
  description?: string;
  unit?: string;
  has_thresholds: boolean;
}

export interface PanelSearchResponse {
  query: string;
  category?: string;
  results: PanelSearchResult[];
  total: number;
}

export interface CategoryResponse {
  categories: string[];
  panels_by_category: Record<string, number>;
}

// Health status colors and icons
export const HEALTH_STATUS_CONFIG = {
  healthy: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    icon: '✅'
  },
  unhealthy: {  // ← ADDED THIS - backend returns "unhealthy" for down services
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    icon: '🚨'
  },
  warning: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    icon: '⚠️'
  },
  critical: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    icon: '🚨'
  },
  unknown: {
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    icon: '❓'
  },
  no_data: {
    color: 'text-gray-400',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    icon: '📭'
  }
} as const;

// Panel type icons
export const PANEL_TYPE_ICONS = {
  gauge: '📊',
  stat: '📈',
  timeseries: '📉',
  table: '📋',
  piechart: '🥧',
  bargauge: '📊',
  heatmap: '🔥'
} as const;

// Category colors
export const CATEGORY_COLORS = {
  cache: 'bg-blue-500',
  database: 'bg-green-500',
  kubernetes: 'bg-purple-500',
  messaging: 'bg-orange-500',
  banking: 'bg-emerald-500',
  security: 'bg-red-500',
  container: 'bg-cyan-500',
  general: 'bg-gray-500'
} as const;