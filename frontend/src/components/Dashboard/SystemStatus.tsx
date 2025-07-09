'use client';

import { useWebSocket } from '@/hooks/useWebSocket';
import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function SystemStatus() {
  const { isConnected, systemStatus, lastUpdate, reconnectAttempts } = useWebSocket();
  const [isExpanded, setIsExpanded] = useState(false);
  const [fallbackData, setFallbackData] = useState<any>(null);

  // Fallback: fetch data manually if WebSocket fails
  useEffect(() => {
    if (!isConnected && reconnectAttempts > 3) {
      fetchFallbackData();
    }
  }, [isConnected, reconnectAttempts]);

  const fetchFallbackData = async () => {
    try {
      // Get banking health directly from API
      const bankingResponse = await fetch('http://localhost:5050/api/banking/health');
      const bankingData = await bankingResponse.json();

      // Get cache data
      const cacheResponse = await fetch('http://localhost:5050/api/banking/cache');
      const cacheData = await cacheResponse.json();

      // Process the data
      const bankingResults = bankingData.result?.data?.result || [];
      const cacheResults = cacheData.result?.data?.result || [];

      setFallbackData({
        banking_services: {
          healthy: bankingResults.filter((r: any) => r.value[1] === '1').length,
          total: bankingResults.length,
          percentage: (bankingResults.filter((r: any) => r.value[1] === '1').length / bankingResults.length) * 100,
          services: bankingResults.map((r: any) => ({
            name: r.metric.instance,
            healthy: r.value[1] === '1',
            port: r.metric.instance.split(':')[1]
          }))
        },
        cache: {
          connected_clients: cacheResults.length > 0 ? parseInt(cacheResults[0].value[1]) : 0,
          hit_ratio: 0 // We'll need to fetch this separately
        },
        overall_health: bankingResults.filter((r: any) => r.value[1] === '1').length === bankingResults.length
      });
    } catch (error) {
      console.error('Error fetching fallback data:', error);
    }
  };

  const currentStatus = systemStatus || fallbackData;
  const connectionStatus = isConnected ? 'Live' : (reconnectAttempts > 0 ? `Reconnecting... (${reconnectAttempts})` : 'Offline');

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getHealthColor = (healthy: boolean) => {
    return healthy ? 'text-green-400' : 'text-red-400';
  };

  const getHealthIcon = (healthy: boolean) => {
    return healthy ? '✅' : '❌';
  };

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
          <h3 className="text-white font-semibold">System Status</h3>
          <span className="text-xs text-gray-400">{connectionStatus}</span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {isExpanded ? '▼' : '▶'}
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="bg-gray-700 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-300 text-sm">Banking Services</span>
            <span className={`text-lg font-bold ${currentStatus?.overall_health ? 'text-green-400' : 'text-red-400'}`}>
              {currentStatus?.banking_services.healthy || 0}/{currentStatus?.banking_services.total || 0}
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {currentStatus?.banking_services.percentage?.toFixed(1) || 0}% healthy
          </div>
        </div>

        <div className="bg-gray-700 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-300 text-sm">Cache</span>
            <span className="text-lg font-bold text-blue-400">
              {currentStatus?.cache.hit_ratio?.toFixed(1) || 0}%
            </span>
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {currentStatus?.cache.connected_clients || 0} clients
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && currentStatus && (
        <div className="border-t border-gray-600 pt-3">
          <h4 className="text-white font-medium mb-2">Service Details</h4>
          <div className="space-y-2">
            {currentStatus.banking_services.services.map((service: any, index: number) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-gray-300">
                  {service.name.split(':')[0]}
                  {service.port && <span className="text-gray-500">:{service.port}</span>}
                </span>
                <span className={getHealthColor(service.healthy)}>
                  {getHealthIcon(service.healthy)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last Update */}
      {lastUpdate && (
        <div className="text-xs text-gray-500 mt-2">
          Last updated: {formatTime(lastUpdate)}
        </div>
      )}

      {/* Fallback mode indicator */}
      {!isConnected && fallbackData && (
        <div className="text-xs text-yellow-400 mt-2">
          📡 Using fallback mode - manual refresh
        </div>
      )}
    </div>
  );
}