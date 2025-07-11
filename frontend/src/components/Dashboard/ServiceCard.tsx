/**
 * Service Card Component - Shows services grouped by category with health status
 * File: frontend/src/components/Dashboard/ServiceCard.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import { DashboardPanel, HEALTH_STATUS_CONFIG, CATEGORY_COLORS } from '@/types/dashboard';
import { dashboardApi } from '@/lib/dashboardApi';

interface ServiceCardProps {
  category: string;
  panels: DashboardPanel[];
  onClick: (category: string) => void;
  isSelected?: boolean;
}

export default function ServiceCard({ category, panels, onClick, isSelected }: ServiceCardProps) {
  const [aggregatedHealth, setAggregatedHealth] = useState<'healthy' | 'critical' | 'warning' | 'unknown' | 'no_data'>('unknown');
  const [healthyCount, setHealthyCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Calculate aggregated health from panels
  useEffect(() => {
    if (panels.length === 0) {
      setAggregatedHealth('unknown');
      return;
    }

    checkServiceHealth();
  }, [panels]);

  const checkServiceHealth = async () => {
    setIsLoading(true);
    let healthy = 0;
    let unhealthy = 0;
    let warning = 0;
    let unknown = 0;

    try {
      // Sample a few panels to check health (to avoid too many API calls)
      const samplePanels = panels.slice(0, Math.min(3, panels.length));

      // Treat 'unhealthy' as 'critical' for aggregation
      for (const panel of samplePanels) {
        try {
          const result = await dashboardApi.executePanelQuery(panel.id, '5m');

          switch (result.health_status as string) {
            case 'healthy':
              healthy++;
              break;
            case 'critical':
            case 'unhealthy':
              unhealthy++;
              break;
            case 'warning':
              warning++;
              break;
            case 'no_data':
              unknown++;
              break;
            default:
              unknown++;
          }
        } catch (error) {
          unknown++;
        }
      }

      setHealthyCount(healthy);

      // Aggregate health logic
      if (unhealthy > 0) {
        setAggregatedHealth('critical');
      } else if (warning > 0) {
        setAggregatedHealth('warning');
      } else if (healthy > 0) {
        setAggregatedHealth('healthy');
      } else if (unknown > 0) {
        setAggregatedHealth('no_data');
      } else {
        setAggregatedHealth('unknown');
      }
    } catch (error) {
      console.error(`Error checking health for ${category}:`, error);
      setAggregatedHealth('unknown');
    } finally {
      setIsLoading(false);
    }
  };

  const healthConfig = HEALTH_STATUS_CONFIG[aggregatedHealth];
  const categoryColor = CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.general;

  return (
    <div
      className={`
        relative bg-gray-800 rounded-lg shadow-md border-2 border-gray-700 transition-all duration-300 hover:shadow-lg cursor-pointer
        ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        ${isLoading ? 'animate-pulse' : ''}
      `}
      onClick={() => onClick(category)}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-4 h-4 rounded-full ${categoryColor}`}></div>
            <h3 className="text-lg font-semibold text-white capitalize">{category}</h3>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{healthConfig.icon}</span>
            {isLoading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Health Status */}
        <div className="text-center mb-4">
          <div className={`text-2xl font-bold ${healthConfig.color} mb-2`}>
            {healthyCount}/{panels.length}
          </div>
          <div className={`text-sm font-medium px-3 py-1 rounded-full ${healthConfig.bgColor} ${healthConfig.color}`}>
            {aggregatedHealth}
          </div>
        </div>

        {/* Service Info */}
        <div className="text-sm text-gray-400 space-y-2">
          <div className="flex justify-between">
            <span>Total Panels:</span>
            <span className="font-medium text-white">{panels.length}</span>
          </div>
          <div className="flex justify-between">
            <span>Category:</span>
            <span className="font-medium text-white capitalize">{category}</span>
          </div>
          <div className="flex justify-between">
            <span>Status:</span>
            <span className={`font-medium ${healthConfig.color}`}>
              {aggregatedHealth === 'healthy' ? 'All Systems Operational' :
                aggregatedHealth === 'critical' ? 'Issues Detected' :
                  aggregatedHealth === 'warning' ? 'Warnings Present' :
                    aggregatedHealth === 'no_data' ? 'No Data Available' :
                      'Status Unknown'}
            </span>
          </div>
        </div>

        {/* Click Instruction */}
        <div className="mt-4 text-center text-xs text-gray-500">
          Click to view {panels.length} panels →
        </div>
      </div>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-800 bg-opacity-70 flex items-center justify-center rounded-lg">
          <div className="text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-1"></div>
            <span className="text-xs text-gray-300">Checking Health...</span>
          </div>
        </div>
      )}
    </div>
  );
}