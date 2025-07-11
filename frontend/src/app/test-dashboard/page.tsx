/**
 * Test Dashboard Page - For testing components without full backend
 * File: frontend/src/app/test-dashboard/page.tsx
 */

"use client";

import { useState } from 'react';
import { DashboardPanel, HEALTH_STATUS_CONFIG, PANEL_TYPE_ICONS, CATEGORY_COLORS } from '@/types/dashboard';

// Mock data for testing
const mockPanels: DashboardPanel[] = [
  {
    id: 1,
    title: "Cache Hit Ratio",
    type: "gauge",
    category: "cache",
    query: "redis_cache_hit_ratio{operation=\"overall\"} * 100",
    description: "Percentage of cache hits vs misses",
    unit: "percent",
    has_thresholds: true,
    thresholds: {
      mode: "absolute",
      steps: [
        { color: "red", value: undefined },
        { color: "yellow", value: 50 },
        { color: "green", value: 80 }
      ]
    }
  },
  {
    id: 2,
    title: "Memory Usage",
    type: "stat",
    category: "cache",
    query: "redis_cache_memory_usage_bytes / 1024 / 1024",
    description: "Redis memory usage in MB",
    unit: "decmbytes",
    has_thresholds: true,
    thresholds: {
      mode: "absolute",
      steps: [
        { color: "green", value: undefined },
        { color: "yellow", value: 512 },
        { color: "red", value: 768 }
      ]
    }
  },
  {
    id: 3,
    title: "Current Replicas",
    type: "stat",
    category: "kubernetes",
    query: "kube_horizontalpodautoscaler_status_current_replicas{namespace=\"banking-k8s-test\"}",
    description: "Current number of pod replicas",
    unit: "short",
    has_thresholds: true
  },
  {
    id: 4,
    title: "Connection Pool Utilization",
    type: "gauge",
    category: "database",
    query: "(banking_db_connections_active / banking_db_connections_max) * 100",
    description: "Database connection pool utilization percentage",
    unit: "percent",
    has_thresholds: true
  }
];

export default function TestDashboardPage() {
  const [selectedPanel, setSelectedPanel] = useState<DashboardPanel | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Filter panels by category
  const filteredPanels = selectedCategory === 'all'
    ? mockPanels
    : mockPanels.filter(panel => panel.category === selectedCategory);

  // Get unique categories
  const categories = ['all', ...Array.from(new Set(mockPanels.map(panel => panel.category)))];

  // Mock health statuses
  const mockHealthStatuses = ['healthy', 'warning', 'critical', 'unknown'];
  const getRandomHealthStatus = () => mockHealthStatuses[Math.floor(Math.random() * mockHealthStatuses.length)];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <h1 className="text-xl font-bold text-gray-800">
              🧪 Dashboard Components Test
            </h1>
            <div className="text-sm text-gray-600">
              Testing frontend components
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-800">
              Component Testing
            </h2>

            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">Category:</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Test Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {/* Component Status */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="font-semibold text-gray-800 mb-4">✅ Component Status</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                <span>Dashboard Types - Loaded</span>
              </div>
              <div className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                <span>Mock Panels - {mockPanels.length} items</span>
              </div>
              <div className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                <span>Categories - {categories.length - 1} types</span>
              </div>
              <div className="flex items-center">
                <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                <span>Health Indicators - Working</span>
              </div>
            </div>
          </div>

          {/* Health Status Legend */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="font-semibold text-gray-800 mb-4">🎨 Health Status Legend</h3>
            <div className="space-y-2">
              {Object.entries(HEALTH_STATUS_CONFIG).map(([status, config]) => (
                <div key={status} className={`flex items-center p-2 rounded ${config.bgColor} ${config.borderColor} border`}>
                  <span className="text-lg mr-2">{config.icon}</span>
                  <span className={`text-sm font-medium ${config.color}`}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Panel Types */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="font-semibold text-gray-800 mb-4">📊 Panel Types</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {Object.entries(PANEL_TYPE_ICONS).map(([type, icon]) => (
                <div key={type} className="flex items-center p-2 bg-gray-50 rounded">
                  <span className="text-lg mr-2">{icon}</span>
                  <span className="capitalize">{type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Mock Dashboard Cards */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            🔧 Mock Dashboard Cards
            <span className="ml-2 text-sm text-gray-600">
              (Showing {filteredPanels.length} of {mockPanels.length} panels)
            </span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredPanels.map(panel => {
              const healthStatus = getRandomHealthStatus() as keyof typeof HEALTH_STATUS_CONFIG;
              const healthConfig = HEALTH_STATUS_CONFIG[healthStatus];
              const panelIcon = PANEL_TYPE_ICONS[panel.type] || '📊';
              const categoryColor = CATEGORY_COLORS[panel.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.general;

              return (
                <div
                  key={panel.id}
                  className={`bg-white rounded-lg shadow-md border-2 transition-all duration-300 hover:shadow-lg cursor-pointer ${healthConfig.borderColor}`}
                  onClick={() => setSelectedPanel(panel)}
                >
                  {/* Header */}
                  <div className="p-4 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{panelIcon}</span>
                        <h3 className="text-sm font-semibold text-gray-800 truncate" title={panel.title}>
                          {panel.title}
                        </h3>
                      </div>
                      <div className="flex items-center space-x-1">
                        <span className={`inline-block w-2 h-2 rounded-full ${categoryColor}`}></span>
                        <span className="text-lg">{healthConfig.icon}</span>
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <div className="text-center mb-3">
                      <div className={`text-2xl font-bold ${healthConfig.color}`}>
                        {Math.floor(Math.random() * 100)}{panel.unit === 'percent' ? '%' : ''}
                      </div>
                    </div>

                    <div className={`text-center mb-3 px-2 py-1 rounded-full text-xs font-medium ${healthConfig.bgColor} ${healthConfig.color}`}>
                      {healthStatus}
                    </div>

                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex justify-between">
                        <span>Type:</span>
                        <span className="font-medium">{panel.type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Category:</span>
                        <span className="font-medium capitalize">{panel.category}</span>
                      </div>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 rounded-b-lg">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>ID: {panel.id}</span>
                      <span>Mock Data</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Panel Info */}
        {selectedPanel && (
          <div className="mt-6 bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              📝 Selected Panel: {selectedPanel.title}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-800 mb-2">Panel Information</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">ID:</span>
                    <span className="font-medium">{selectedPanel.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium">{selectedPanel.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Category:</span>
                    <span className="font-medium">{selectedPanel.category}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Unit:</span>
                    <span className="font-medium">{selectedPanel.unit || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-800 mb-2">PromQL Query</h4>
                <div className="bg-gray-900 text-gray-100 p-3 rounded text-xs font-mono overflow-x-auto">
                  {selectedPanel.query}
                </div>
              </div>
            </div>

            <button
              onClick={() => setSelectedPanel(null)}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}