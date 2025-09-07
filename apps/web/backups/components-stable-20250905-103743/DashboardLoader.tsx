'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import dashboardConfig from '@/config/dashboard.config.json';

// Dynamically import widgets
const widgetComponents = {
  AccountOverview: dynamic(() => import('./dashboard/AccountOverview')),
  PositionsTable: dynamic(() => import('./dashboard/PositionsTable')),
  OrderEntry: dynamic(() => import('./dashboard/OrderEntry')),
  PerformanceChart: dynamic(() => import('./dashboard/PerformanceChart')),
  RiskMonitor: dynamic(() => import('./dashboard/RiskMonitor')),
  StrategyControl: dynamic(() => import('./dashboard/StrategyControl')),
  MetricsDashboard: dynamic(() => import('./dashboard/MetricsDashboard')),
  AlertsPanel: dynamic(() => import('./dashboard/AlertsPanel')),
};

export function DashboardLoader() {
  const [config, setConfig] = useState(dashboardConfig);
  const [editMode, setEditMode] = useState(false);

  // Watch for config changes
  useEffect(() => {
    const checkForConfigChanges = async () => {
      try {
        const response = await fetch('/api/config/dashboard');
        const newConfig = await response.json();
        if (JSON.stringify(newConfig) !== JSON.stringify(config)) {
          setConfig(newConfig);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard config:', error);
      }
    };

    const interval = setInterval(checkForConfigChanges, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, [config]);

  return (
    <div className="relative">
      {/* Edit mode toggle */}
      <button
        onClick={() => setEditMode(!editMode)}
        className="absolute top-4 right-4 z-50 px-3 py-1 text-xs bg-primary/20 border border-primary rounded"
      >
        {editMode ? 'Save Layout' : 'Edit Layout'}
      </button>

      {/* Render widgets based on config */}
      <div className="grid grid-cols-12 gap-4 p-6">
        {config.widgets.map((widget) => {
          const Component = widgetComponents[widget.type];
          if (!Component) return null;

          return (
            <div
              key={widget.id}
              className={`col-span-${widget.position.width} row-span-${widget.position.height}`}
              style={{
                gridColumn: `span ${widget.position.width}`,
                gridRow: `span ${widget.position.height}`,
              }}
            >
              <Component {...widget.config} editMode={editMode} />
            </div>
          );
        })}
      </div>
    </div>
  );
}