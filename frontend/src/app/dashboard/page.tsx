/**
 * Dashboard Page - Main dashboard interface
 * File: frontend/src/app/dashboard/page.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import DashboardGrid from '@/components/Dashboard/DashboardGrid';
import { dashboardApi } from '@/lib/dashboardApi';
import { CATEGORY_COLORS } from '@/types/dashboard';

export default function DashboardPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load categories
  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setIsLoading(true);
      const response = await dashboardApi.getCategories();
      setCategories(['all', ...response.categories]);
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategories(['all']);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  // Handle category change
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
  };

  // Clear filters
  const clearFilters = () => {
    setSelectedCategory('all');
    setSearchQuery('');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 shadow-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-white">
                🏢 WatchTower AI Dashboard
              </h1>
              <div className="hidden md:flex items-center space-x-2 text-sm text-gray-400">
                <span>•</span>
                <span>Interactive Monitoring</span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-400">
                Real-time Banking System Monitoring
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-gray-800 rounded-lg shadow-sm border-gray-700 p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Search */}
            <div className="flex-1 max-w-md">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search panels by title, query, or description..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Category Filter */}
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-white">Category:</label>
              <select
                value={selectedCategory}
                onChange={(e) => handleCategoryChange(e.target.value)}
                className="px-3 py-2 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Clear Filters */}
            {(selectedCategory !== 'all' || searchQuery) && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Active Filters */}
          {(selectedCategory !== 'all' || searchQuery) && (
            <div className="mt-4 flex flex-wrap gap-2">
              {selectedCategory !== 'all' && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-blue-900 text-blue-300 rounded-full text-sm">
                  <div className={`w-2 h-2 rounded-full ${CATEGORY_COLORS[selectedCategory as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS.general}`}></div>
                  <span>Category: {selectedCategory}</span>
                  <button
                    onClick={() => setSelectedCategory('all')}
                    className="ml-1 hover:text-blue-400"
                  >
                    ×
                  </button>
                </div>
              )}
              {searchQuery && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-green-900 text-green-300 rounded-full text-sm">
                  <span>Search: "{searchQuery}"</span>
                  <button
                    onClick={() => setSearchQuery('')}
                    className="ml-1 hover:text-green-400"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-gradient-to-r from-blue-900 to-purple-900 border border-blue-700 rounded-lg p-6 mb-6">
          <div className="flex items-start space-x-3">
            <div className="text-2xl">💡</div>
            <div>
              <h3 className="font-semibold text-white mb-2">How to Use Dashboard</h3>
              <div className="text-sm text-gray-300 space-y-2">
                <p>• <strong>View Panel Cards:</strong> Each card shows real-time metrics with health indicators</p>
                <p>• <strong>Click on Cards:</strong> Click any panel card to view detailed information and raw data</p>
                <p>• <strong>Filter by Category:</strong> Use the category dropdown to filter panels by service type</p>
                <p>• <strong>Search:</strong> Search panels by title, PromQL query, or description</p>
                <p>• <strong>Auto-refresh:</strong> Cards automatically update every 30 seconds</p>
                <p>• <strong>Health Colors:</strong>
                  <span className="ml-2 inline-flex items-center space-x-1">
                    <span className="text-green-400">✅ Healthy</span>
                    <span className="text-yellow-400">⚠️ Warning</span>
                    <span className="text-red-400">🚨 Critical</span>
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <DashboardGrid
          selectedCategory={selectedCategory === 'all' ? undefined : selectedCategory}
          searchQuery={searchQuery}
        />
      </div>
    </div>
  );
}