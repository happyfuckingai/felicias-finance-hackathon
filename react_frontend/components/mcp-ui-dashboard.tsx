'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { MCPUIComponent, MCPUIDashboard, renderMCPUIComponent } from '@/lib/mcp-ui-client';
import '@/lib/mcp-ui-registry.tsx';

// Initialize component registry

interface MCPUIDashboardProps {
  dashboard: MCPUIDashboard;
  className?: string;
}

export function MCPUIDashboardComponent({ dashboard, className }: MCPUIDashboardProps) {
  const [components, setComponents] = useState<MCPUIComponent[]>(dashboard.components);

  // Update components when dashboard changes
  useEffect(() => {
    setComponents(dashboard.components);
  }, [dashboard.components]);

  const getGridCols = (layout: string) => {
    switch (layout) {
      case 'grid-2':
        return 'grid-cols-1 md:grid-cols-2';
      case 'grid-3':
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
      case 'grid-4':
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      default:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3';
    }
  };

  const getComponentWidth = (width?: string) => {
    switch (width) {
      case '1/1':
        return 'col-span-full';
      case '1/2':
        return 'col-span-1 md:col-span-1';
      case '1/3':
        return 'col-span-1 md:col-span-1 lg:col-span-1';
      case '2/3':
        return 'col-span-full md:col-span-2';
      default:
        return 'col-span-1';
    }
  };

  return (
    <div className={`w-full ${className || ''}`}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-6"
      >
        {/* Dashboard Title */}
        {dashboard.title && (
          <div className="text-center">
            <h2 className="text-foreground text-2xl font-bold">{dashboard.title}</h2>
          </div>
        )}

        {/* Components Grid */}
        <div className={`grid gap-6 ${getGridCols(dashboard.layout || 'grid')}`}>
          {components.map((component, index) => {
            const width = getComponentWidth(component.layout?.width);

            return (
              <motion.div
                key={component.id || index}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className={width}
              >
                {renderMCPUIComponent(component)}
              </motion.div>
            );
          })}
        </div>

        {/* Auto-refresh indicator */}
        {dashboard.refreshInterval && (
          <div className="text-center">
            <p className="text-muted-foreground text-xs">
              Auto-refreshing every {Math.round(dashboard.refreshInterval / 1000)} seconds
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
}

// Hook for managing MCP-UI dashboard state
export function useMCPUIDashboard() {
  const [dashboard, setDashboard] = useState<MCPUIDashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async (dashboardData: MCPUIDashboard) => {
    setLoading(true);
    setError(null);

    try {
      setDashboard(dashboardData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const updateComponent = (componentId: string, updates: Partial<MCPUIComponent>) => {
    if (!dashboard) return;

    setDashboard((prev) => {
      if (!prev) return prev;

      return {
        ...prev,
        components: prev.components.map((comp) =>
          comp.id === componentId ? { ...comp, ...updates } : comp
        ),
      };
    });
  };

  const updateComponents = (updates: { [componentId: string]: Partial<MCPUIComponent> }) => {
    if (!dashboard) return;

    setDashboard((prev) => {
      if (!prev) return prev;

      return {
        ...prev,
        components: prev.components.map((comp) => {
          const update = updates[comp.id];
          return update ? { ...comp, ...update } : comp;
        }),
      };
    });
  };

  return {
    dashboard,
    loading,
    error,
    loadDashboard,
    updateComponent,
    updateComponents,
  };
}
