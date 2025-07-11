/**
 * Dashboard API client for frontend
 * File: frontend/src/lib/dashboardApi.ts
 */

import { 
  DashboardApiResponse, 
  Dashboard, 
  DashboardSummary, 
  PanelSearchResponse, 
  PanelQueryResult, 
  CategoryResponse,
  DashboardStats
} from '@/types/dashboard';

const API_BASE_URL = 'http://localhost:5050/api/dashboards';

class DashboardApiClient {
  private async fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get all dashboards
   */
  async getAllDashboards(): Promise<DashboardApiResponse> {
    return this.fetchApi<DashboardApiResponse>('/');
  }

  /**
   * Get dashboard categories
   */
  async getCategories(): Promise<CategoryResponse> {
    return this.fetchApi<CategoryResponse>('/categories');
  }

  /**
   * Get dashboards by category
   */
  async getDashboardsByCategory(category: string): Promise<{
    category: string;
    dashboards: DashboardSummary[];
  }> {
    return this.fetchApi<{
      category: string;
      dashboards: DashboardSummary[];
    }>(`/category/${encodeURIComponent(category)}`);
  }

  /**
   * Get specific dashboard by UID
   */
  async getDashboard(uid: string): Promise<Dashboard> {
    return this.fetchApi<Dashboard>(`/${encodeURIComponent(uid)}`);
  }

  /**
   * Get all panels with optional filtering
   */
  async getAllPanels(params?: {
    category?: string;
    limit?: number;
  }): Promise<{
    panels: Array<{
      id: number;
      title: string;
      type: string;
      category: string;
      query: string;
      description?: string;
      unit?: string;
      has_thresholds: boolean;
    }>;
    total: number;
    filtered_by?: string;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append('category', params.category);
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
    return this.fetchApi<any>(`/panels/all${query}`);
  }

  /**
   * Search panels
   */
  async searchPanels(query: string, category?: string): Promise<PanelSearchResponse> {
    const searchParams = new URLSearchParams({ q: query });
    if (category) searchParams.append('category', category);

    return this.fetchApi<PanelSearchResponse>(`/panels/search?${searchParams.toString()}`);
  }

  /**
   * Execute panel query
   */
  async executePanelQuery(
    panelId: number, 
    timeRange: string = '5m'
  ): Promise<PanelQueryResult> {
    return this.fetchApi<PanelQueryResult>(`/panels/${panelId}/query?time_range=${timeRange}`, {
      method: 'POST',
    });
  }

  /**
   * Execute batch panel queries
   */
  async executeBatchPanelQueries(
    panelIds: number[],
    timeRange: string = '5m'
  ): Promise<{
    time_range: string;
    results: Array<{
      panel_id: number;
      title: string;
      type: string;
      category: string;
      query: string;
      unit?: string;
      result: any;
      health_status: string;
      error?: string;
    }>;
    total: number;
    success_count: number;
  }> {
    const params = new URLSearchParams({ time_range: timeRange });
    panelIds.forEach(id => params.append('panel_ids', id.toString()));

    return this.fetchApi<any>(`/panels/batch-query?${params.toString()}`, {
      method: 'POST',
    });
  }

  /**
   * Get dashboard statistics
   */
  async getDashboardStats(): Promise<{
    registry_stats: DashboardStats;
    categories: string[];
    status: string;
  }> {
    return this.fetchApi<any>('/stats');
  }

  /**
   * Format metric value for display
   */
  formatMetricValue(value: string | number, unit?: string): string {
    if (typeof value === 'string') {
      value = parseFloat(value);
    }

    if (isNaN(value)) {
      return 'N/A';
    }

    // Format based on unit
    switch (unit) {
      case 'percent':
        return `${value.toFixed(1)}%`;
      case 'bytes':
        return this.formatBytes(value);
      case 'decmbytes':
        return `${value.toFixed(1)} MB`;
      case 'short':
        return this.formatShort(value);
      case 'ms':
        return `${value.toFixed(2)}ms`;
      case 'reqps':
        return `${value.toFixed(2)}/s`;
      default:
        return value.toFixed(2);
    }
  }

  /**
   * Format bytes for display
   */
  private formatBytes(bytes: number): string {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  }

  /**
   * Format short numbers for display
   */
  private formatShort(value: number): string {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  }

  /**
   * Get health status from metric value and thresholds
   */
  getHealthStatus(
    value: number,
    thresholds?: {
      mode: 'absolute' | 'percentage';
      steps: Array<{ color: string; value?: number }>;
    }
  ): 'healthy' | 'warning' | 'critical' | 'unknown' {
    if (!thresholds || !thresholds.steps) {
      return 'unknown';
    }

    // Sort steps by value (None values first)
    const sortedSteps = [...thresholds.steps].sort((a, b) => {
      if (a.value === undefined) return -1;
      if (b.value === undefined) return 1;
      return a.value - b.value;
    });

    // Find the appropriate threshold
    let currentColor = 'green'; // default
    for (const step of sortedSteps) {
      if (step.value === undefined) {
        currentColor = step.color;
      } else if (value >= step.value) {
        currentColor = step.color;
      }
    }

    // Map colors to health status
    const colorToHealth: Record<string, 'healthy' | 'warning' | 'critical' | 'unknown'> = {
      green: 'healthy',
      yellow: 'warning',
      red: 'critical',
      blue: 'healthy'
    };

    return colorToHealth[currentColor] || 'unknown';
  }
}

// Export singleton instance
export const dashboardApi = new DashboardApiClient();
export default dashboardApi;