/**
 * Dashboard Card Component - Interactive panel cards
 * File: frontend/src/components/Dashboard/DashboardCard.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import { DashboardPanel, PanelQueryResult, HEALTH_STATUS_CONFIG, PANEL_TYPE_ICONS, CATEGORY_COLORS } from '@/types/dashboard';
import { dashboardApi } from '@/lib/dashboardApi';

interface DashboardCardProps {
  panel: DashboardPanel;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onClick?: (panel: DashboardPanel) => void;
}

export default function DashboardCard({
  panel,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
  onClick
}: DashboardCardProps) {
  const [queryResult, setQueryResult] = useState<PanelQueryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Execute panel query
  const executeQuery = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await dashboardApi.executePanelQuery(panel.id);
      setQueryResult(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute query');
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    // Execute initial query
    executeQuery();

    // Set up auto-refresh
    if (autoRefresh) {
      const interval = setInterval(executeQuery, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [panel.id, autoRefresh, refreshInterval]);

  // Get metric value from query result
  const getMetricValue = (): string => {
    if (!queryResult?.result?.data?.data?.result?.[0]?.value) {
      return 'N/A';
    }

    const value = queryResult.result.data.data.result[0].value[1];
    return dashboardApi.formatMetricValue(value, panel.unit);
  };

  // Get health status configuration
  const healthConfig = HEALTH_STATUS_CONFIG[queryResult?.health_status || 'unknown'];
  const panelIcon = PANEL_TYPE_ICONS[panel.type] || '📊';
  const categoryColor = CATEGORY_COLORS[panel.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.general;

  return (
    <div
      className={`
        relative bg-gray-800 rounded-lg shadow-md border-2 border-gray-700 transition-all duration-300 hover:shadow-lg cursor-pointer
        ${healthConfig.borderColor}
        ${isLoading ? 'animate-pulse' : ''}
      `}
      onClick={() => onClick?.(panel)}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{panelIcon}</span>
            <h3 className="text-sm font-semibold text-white truncate" title={panel.title}>
              {panel.title}
            </h3>
          </div>
          <div className="flex items-center space-x-1">
            <span className={`inline-block w-2 h-2 rounded-full ${categoryColor}`} title={panel.category}></span>
            <span className="text-lg">{healthConfig.icon}</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Metric Value */}
        <div className="text-center mb-3">
          {isLoading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : error ? (
            <div className="text-red-500 text-xs">
              <span className="block text-lg">❌</span>
              <span>{error}</span>
            </div>
          ) : (
            <div className={`text-2xl font-bold ${healthConfig.color}`}>
              {getMetricValue()}
            </div>
          )}
        </div>

        {/* Health Status */}
        <div className={`text-center mb-3 px-2 py-1 rounded-full text-xs font-medium ${healthConfig.bgColor} ${healthConfig.color}`}>
          {queryResult?.health_status || 'unknown'}
        </div>

        {/* Panel Info */}
        <div className="text-xs text-gray-400 space-y-1">
          <div className="flex justify-between">
            <span>Type:</span>
            <span className="font-medium">{panel.type}</span>
          </div>
          <div className="flex justify-between">
            <span>Category:</span>
            <span className="font-medium capitalize">{panel.category}</span>
          </div>
          {panel.unit && (
            <div className="flex justify-between">
              <span>Unit:</span>
              <span className="font-medium">{panel.unit}</span>
            </div>
          )}
        </div>

        {/* Description */}
        {panel.description && (
          <div className="mt-3 text-xs text-gray-300 border-t border-gray-700 pt-2">
            <p className="line-clamp-2">{panel.description}</p>
          </div>
        )}

        {/* Query Preview */}
        <div className="mt-3 text-xs text-gray-400 border-t border-gray-700 pt-2">
          <details className="group">
            <summary className="cursor-pointer hover:text-gray-200 font-medium">
              PromQL Query
            </summary>
            <code className="block mt-1 p-2 bg-gray-900 rounded text-xs font-mono overflow-x-auto text-gray-100">
              {panel.query}
            </code>
          </details>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-900 border-t border-gray-700 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>ID: {panel.id}</span>
          {lastUpdated && (
            <span title={lastUpdated.toLocaleString()}>
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-800 bg-opacity-70 flex items-center justify-center rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <span className="text-sm text-gray-300">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
}