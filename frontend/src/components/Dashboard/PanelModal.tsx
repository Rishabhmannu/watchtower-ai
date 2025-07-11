/**
 * Panel Modal Component - Detailed panel view
 * File: frontend/src/components/Dashboard/PanelModal.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import { DashboardPanel, PanelQueryResult, HEALTH_STATUS_CONFIG, PANEL_TYPE_ICONS } from '@/types/dashboard';
import { dashboardApi } from '@/lib/dashboardApi';

interface PanelModalProps {
  panel: DashboardPanel;
  onClose: () => void;
}

export default function PanelModal({ panel, onClose }: PanelModalProps) {
  const [queryResult, setQueryResult] = useState<PanelQueryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('5m');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Execute panel query
  const executeQuery = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await dashboardApi.executePanelQuery(panel.id, timeRange);
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
    executeQuery();

    if (autoRefresh) {
      const interval = setInterval(executeQuery, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [panel.id, timeRange, autoRefresh]);

  // Get metric value and raw data
  const getMetricData = () => {
    if (!queryResult?.result?.data?.data?.result?.[0]) {
      return { value: 'N/A', rawValue: null, metric: {} };
    }

    const result = queryResult.result.data.data.result[0];
    const rawValue = result.value[1];
    const formattedValue = dashboardApi.formatMetricValue(rawValue, panel.unit);

    return {
      value: formattedValue,
      rawValue: parseFloat(rawValue),
      metric: result.metric
    };
  };

  const metricData = getMetricData();
  const healthConfig = HEALTH_STATUS_CONFIG[queryResult?.health_status || 'unknown'];
  const panelIcon = PANEL_TYPE_ICONS[panel.type] || '📊';

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={handleBackdropClick}
    >
      <div className="bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{panelIcon}</span>
            <div>
              <h2 className="text-xl font-bold text-white">{panel.title}</h2>
              <p className="text-sm text-gray-300">
                {panel.type} • {panel.category} • ID: {panel.id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-full transition-colors"
          >
            <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Controls */}
        <div className="p-6 border-b bg-gray-900 border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-300">Time Range:</label>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="px-3 py-1 border border-gray-700 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-800 text-white"
                >
                  <option value="5m">Last 5 minutes</option>
                  <option value="15m">Last 15 minutes</option>
                  <option value="30m">Last 30 minutes</option>
                  <option value="1h">Last 1 hour</option>
                  <option value="6h">Last 6 hours</option>
                  <option value="24h">Last 24 hours</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-300">Auto-refresh:</label>
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-700 rounded focus:ring-blue-500 bg-gray-800"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={executeQuery}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Refreshing...' : 'Refresh'}
              </button>

              {lastUpdated && (
                <span className="text-xs text-gray-400">
                  Updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Metric Value Display */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Current Value */}
            <div className={`p-6 rounded-lg border-2 border-gray-700 ${healthConfig.bgColor}`}>
              <div className="text-center">
                <div className="text-4xl mb-2">{healthConfig.icon}</div>
                <div className={`text-3xl font-bold mb-2 ${healthConfig.color}`}>
                  {metricData.value}
                </div>
                <div className={`text-sm font-medium px-3 py-1 rounded-full ${healthConfig.bgColor} ${healthConfig.color}`}>
                  {queryResult?.health_status || 'unknown'}
                </div>
              </div>
            </div>

            {/* Panel Information */}
            <div className="p-6 bg-gray-900 rounded-lg">
              <h3 className="font-semibold text-white mb-4">Panel Information</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-300">Type:</span>
                  <span className="font-medium">{panel.type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Category:</span>
                  <span className="font-medium capitalize">{panel.category}</span>
                </div>
                {panel.unit && (
                  <div className="flex justify-between">
                    <span className="text-gray-300">Unit:</span>
                    <span className="font-medium">{panel.unit}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-300">Has Thresholds:</span>
                  <span className="font-medium">{panel.has_thresholds ? 'Yes' : 'No'}</span>
                </div>
                {metricData.rawValue !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-300">Raw Value:</span>
                    <span className="font-medium">{metricData.rawValue.toFixed(6)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Description */}
          {panel.description && (
            <div className="mb-6 p-4 bg-blue-900 rounded-lg">
              <h3 className="font-semibold text-white mb-2">Description</h3>
              <p className="text-gray-200">{panel.description}</p>
            </div>
          )}

          {/* Query Information */}
          <div className="mb-6">
            <h3 className="font-semibold text-white mb-3">PromQL Query</h3>
            <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
              <pre>{panel.query}</pre>
            </div>
          </div>

          {/* Thresholds */}
          {panel.thresholds && (
            <div className="mb-6">
              <h3 className="font-semibold text-white mb-3">Thresholds</h3>
              <div className="space-y-2">
                {panel.thresholds.steps.map((step, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded-full bg-${step.color}-500`}></div>
                      <span className="text-sm font-medium capitalize text-white">{step.color}</span>
                    </div>
                    <span className="text-sm text-gray-300">
                      {step.value !== undefined ? `≥ ${step.value}` : 'Default'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metric Labels */}
          {Object.keys(metricData.metric).length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-white mb-3">Metric Labels</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {Object.entries(metricData.metric).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg">
                    <span className="text-sm font-medium text-gray-200">{key}:</span>
                    <span className="text-sm text-gray-300 font-mono">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-900 border border-red-700 rounded-lg">
              <div className="flex items-center">
                <span className="text-red-300 text-lg mr-2">❌</span>
                <div>
                  <h3 className="text-red-200 font-semibold">Query Error</h3>
                  <p className="text-red-400 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Raw Response */}
          {queryResult && (
            <div>
              <h3 className="font-semibold text-white mb-3">Raw Response</h3>
              <details className="bg-gray-900 rounded-lg">
                <summary className="p-4 cursor-pointer hover:bg-gray-800 font-medium text-gray-200">
                  Show Raw JSON Response
                </summary>
                <div className="p-4 border-t border-gray-700">
                  <pre className="text-xs text-gray-200 overflow-x-auto">
                    {JSON.stringify(queryResult, null, 2)}
                  </pre>
                </div>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}