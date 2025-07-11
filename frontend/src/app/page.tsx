/**
 * Main page with dashboard navigation
 * File: frontend/src/app/page.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import ChatInterface from '@/components/Chat/ChatInterface';
import SystemStatus from '@/components/Dashboard/SystemStatus';

export default function HomePage() {
  const [systemStats, setSystemStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load system overview
  useEffect(() => {
    loadSystemOverview();
  }, []);

  const loadSystemOverview = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('http://localhost:5050/api/system/overview');
      const data = await response.json();
      setSystemStats(data);
    } catch (error) {
      console.error('Failed to load system overview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 shadow-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-white">
                🏢 WatchTower AI
              </h1>
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-400">
                <span>•</span>
                <span>Intelligent Banking System Monitoring</span>
              </div>
            </div>
            
            <nav className="flex items-center space-x-4">
              <Link 
                href="/dashboard" 
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                📊 Dashboard
              </Link>
              <div className="text-sm text-gray-400">
                Real-time Monitoring
              </div>
            </nav>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-8 mb-8">
          <div className="max-w-3xl">
            <h2 className="text-3xl font-bold mb-4">
              🚀 Revolutionary Banking System Monitoring
            </h2>
            <p className="text-xl mb-6 text-blue-100">
              AI-powered monitoring agent for your banking infrastructure. 
              Monitor 31+ services, query dashboards with natural language, 
              and get intelligent insights.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link 
                href="/dashboard" 
                className="px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                📊 View Dashboard
              </Link>
              <button 
                onClick={loadSystemOverview}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold hover:bg-blue-400 transition-colors"
              >
                🔄 Refresh Status
              </button>
            </div>
          </div>
        </div>

        {/* System Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* System Stats */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                📊 System Overview
              </h3>
              
              {isLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
              ) : systemStats ? (
                <div className="space-y-4">
                  {/* Services */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {systemStats.total_services}
                      </div>
                      <div className="text-sm text-gray-400">Total Services</div>
                    </div>
                    
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {systemStats.dashboard_integration?.total_dashboards || 0}
                      </div>
                      <div className="text-sm text-gray-400">Dashboards</div>
                    </div>
                    
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {systemStats.dashboard_integration?.total_panels || 0}
                      </div>
                      <div className="text-sm text-gray-400">Panels</div>
                    </div>
                    
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {systemStats.dashboard_integration?.categories || 0}
                      </div>
                      <div className="text-sm text-gray-400">Categories</div>
                    </div>
                  </div>

                  {/* Features */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="font-medium text-white">🔧 Monitoring Features</h4>
                      <div className="text-sm text-gray-400 space-y-1">
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.monitoring?.prometheus_connected ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          Prometheus Connected
                        </div>
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.monitoring?.enhanced_features_available ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          Enhanced Features
                        </div>
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.ai_features?.dashboard_queries_enabled ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          Dashboard Integration
                        </div>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <h4 className="font-medium text-white">🤖 AI Features</h4>
                      <div className="text-sm text-gray-400 space-y-1">
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.ai_features?.openai_available ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          OpenAI Available
                        </div>
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.ai_features?.chat_enabled ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          Chat Enabled
                        </div>
                        <div className="flex items-center">
                          <span className={`w-3 h-3 rounded-full mr-2 ${systemStats.ai_features?.natural_language_queries ? 'bg-green-500' : 'bg-red-500'}`}></span>
                          Natural Language
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <span className="text-2xl mb-2 block">⚠️</span>
                  <p>Unable to load system overview</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                🚀 Quick Actions
              </h3>
              <div className="space-y-3">
                <Link 
                  href="/dashboard"
                  className="block w-full p-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-center font-medium"
                >
                  📊 View Dashboard
                </Link>
                <Link 
                  href="/dashboard?category=cache"
                  className="block w-full p-3 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors text-center font-medium"
                >
                  🗄️ Cache Monitoring
                </Link>
                <Link 
                  href="/dashboard?category=kubernetes"
                  className="block w-full p-3 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors text-center font-medium"
                >
                  ☸️ Kubernetes Monitoring
                </Link>
                <Link 
                  href="/dashboard?category=database"
                  className="block w-full p-3 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 transition-colors text-center font-medium"
                >
                  🗃️ Database Monitoring
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-lg shadow-sm border">
            <ChatInterface />
          </div>
          
          <div className="bg-gray-800 rounded-lg shadow-sm border">
            <SystemStatus />
          </div>
        </div>
      </div>
    </div>
  );
}
