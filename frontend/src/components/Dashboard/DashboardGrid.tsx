/**
 * Dashboard Grid Component - Main dashboard interface
 * File: frontend/src/components/Dashboard/DashboardGrid.tsx
 */

"use client";

import { useState, useEffect } from 'react';
import DashboardCard from './DashboardCard';
import ServiceCard from './ServiceCard';
import PanelModal from './PanelModal';
import { DashboardPanel, DashboardSummary, CATEGORY_COLORS } from '@/types/dashboard';
import { dashboardApi } from '@/lib/dashboardApi';

interface DashboardGridProps {
  selectedCategory?: string;
  searchQuery?: string;
}

export default function DashboardGrid({ selectedCategory, searchQuery }: DashboardGridProps) {
  const [dashboards, setDashboards] = useState<DashboardSummary[]>([]);
  const [allPanels, setAllPanels] = useState<DashboardPanel[]>([]);
  const [filteredPanels, setFilteredPanels] = useState<DashboardPanel[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedDashboard, setSelectedDashboard] = useState<string | null>(null);
  const [selectedPanel, setSelectedPanel] = useState<DashboardPanel | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [selectedService, setSelectedService] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    loadDashboards();
    loadCategories();
    loadStats();
  }, []);

  // Load all dashboards
  const loadDashboards = async () => {
    try {
      setIsLoading(true);
      const response = await dashboardApi.getAllDashboards();
      setDashboards(response.dashboards);

      // Load all panels from all dashboards
      const allPanelsPromises = response.dashboards.map(dashboard =>
        dashboardApi.getDashboard(dashboard.uid)
      );

      const dashboardDetails = await Promise.all(allPanelsPromises);
      const panels = dashboardDetails.flatMap(dashboard => dashboard.panels || []);
      setAllPanels(panels);
      setFilteredPanels(panels);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboards');
    } finally {
      setIsLoading(false);
    }
  };

  // Load categories
  const loadCategories = async () => {
    try {
      const response = await dashboardApi.getCategories();
      setCategories(response.categories);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  // Load stats
  const loadStats = async () => {
    try {
      const response = await dashboardApi.getDashboardStats();
      setStats(response); // ← FIXED: set stats directly
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  // Filter panels based on category and search query
  useEffect(() => {
    let filtered = [...allPanels];

    // Filter by category
    if (selectedCategory && selectedCategory !== 'all') {
      filtered = filtered.filter(panel => panel.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(panel =>
        panel.title.toLowerCase().includes(query) ||
        panel.query.toLowerCase().includes(query) ||
        panel.description?.toLowerCase().includes(query)
      );
    }

    setFilteredPanels(filtered);
  }, [allPanels, selectedCategory, searchQuery]);

  // Handle panel click
  const handlePanelClick = (panel: DashboardPanel) => {
    setSelectedPanel(panel);
  };

  // Handle dashboard selection
  const handleDashboardSelect = (dashboardUid: string) => {
    setSelectedDashboard(dashboardUid === selectedDashboard ? null : dashboardUid);
  };

  // Handle service selection
  const handleServiceSelect = (category: string) => {
    setSelectedService(category === selectedService ? null : category);
  };

  // Group panels by category
  const groupPanelsByCategory = () => {
    const grouped: { [key: string]: DashboardPanel[] } = {};
    allPanels.forEach(panel => {
      if (!grouped[panel.category]) {
        grouped[panel.category] = [];
      }
      grouped[panel.category].push(panel);
    });
    return grouped;
  };

  // Get panels for selected service
  const getSelectedServicePanels = () => {
    if (!selectedService) return [];
    return allPanels.filter(panel => panel.category === selectedService);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboards...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <span className="text-red-500 text-lg mr-2">❌</span>
          <div>
            <h3 className="text-red-800 font-semibold">Error Loading Dashboards</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </div>
        <button
          onClick={loadDashboards}
          className="mt-3 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white">📊 WatchTower AI Dashboard</h2>
          <div className="flex space-x-4 text-sm text-gray-300">
            <span>📋 {stats?.total_dashboards || 0} Dashboards</span>
            <span>🔧 {stats?.total_panels || 0} Panels</span>
            <span>📁 {Object.keys(stats?.categories || {}).length} Categories</span>
          </div>
        </div>

      {/* Navigation Breadcrumbs */}
      <div className="flex items-center space-x-2 text-sm text-gray-400">
        <span>🏠 Services</span>
        {selectedService && (
          <>
            <span>→</span>
            <span className="text-white capitalize">{selectedService}</span>
            <button
              onClick={() => setSelectedService(null)}
              className="ml-2 text-blue-400 hover:text-blue-300"
            >
              ← Back to Services
            </button>
          </>
        )}
      </div>
    </div>

    {!selectedService ? (
      // Services View
      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            🏢 Banking System Services
          </h3>
          <div className="text-sm text-gray-300">
            Click on a service to view its monitoring panels
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Object.entries(groupPanelsByCategory()).map(([category, panels]) => (
            <ServiceCard
              key={category}
              category={category}
              panels={panels}
              onClick={handleServiceSelect}
              isSelected={selectedService === category}
            />
          ))}
        </div>
      </div>
    ) : (
      // Selected Service Panels View
      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">
            🔧 {selectedService.charAt(0).toUpperCase() + selectedService.slice(1)} Service Panels
          </h3>
          <div className="text-sm text-gray-300">
            Showing {getSelectedServicePanels().length} panels
          </div>
        </div>

        {getSelectedServicePanels().length === 0 ? (
          <div className="text-center py-12">
            <span className="text-4xl mb-4 block">📭</span>
            <h3 className="text-lg font-medium text-white mb-2">No Panels Found</h3>
            <p className="text-gray-300">
              No panels found for the {selectedService} service.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {getSelectedServicePanels().map((panel, index) => (
              <DashboardCard
                key={`${panel.id}-${index}`}
                panel={panel}
                onClick={handlePanelClick}
              />
            ))}
          </div>
        )}
      </div>
    )}

    {/* Panel Modal */}
    {selectedPanel && (
      <PanelModal
        panel={selectedPanel}
        onClose={() => setSelectedPanel(null)}
      />
    )}
  </div>
);
}