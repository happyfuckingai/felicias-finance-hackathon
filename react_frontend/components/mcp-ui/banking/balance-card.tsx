import React from 'react';
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardSubtitle,
  GlassCardTitle,
  GlassCardValue,
} from '@/components/mcp-ui/glass';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface BalanceCardProps {
  component: MCPUIComponent;
}

export function BalanceCard({ component }: BalanceCardProps) {
  const { title, value, subtitle, trend, trendDirection, lastUpdated } = component;

  // Determine trend styling based on direction
  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'positive':
        return 'text-green-300'; // var(--text-success)
      case 'negative':
        return 'text-red-300'; // var(--text-error)
      default:
        return 'text-white/55'; // var(--text-secondary)
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'positive':
        return '↗️';
      case 'negative':
        return '↘️';
      default:
        return '→';
    }
  };

  return (
    <GlassCard className="w-full" depth="surface">
      <GlassCardHeader>
        <GlassCardTitle>{title || 'Account Balance'}</GlassCardTitle>
      </GlassCardHeader>
      <GlassCardContent>
        <GlassCardValue>{value}</GlassCardValue>
        {subtitle && <GlassCardSubtitle>{subtitle}</GlassCardSubtitle>}
        {trend && trendDirection && (
          <div className={`mt-3 text-sm font-medium ${getTrendColor(trendDirection)}`}>
            {getTrendIcon(trendDirection)} {trend}
          </div>
        )}
        {lastUpdated && (
          <GlassCardSubtitle className="mt-2">
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </GlassCardSubtitle>
        )}
      </GlassCardContent>
    </GlassCard>
  );
}
