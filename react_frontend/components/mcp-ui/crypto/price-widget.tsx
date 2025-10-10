import React, { useState } from 'react';
import { TrendDown, TrendUp } from '@phosphor-icons/react';
import {
  GlassCard,
  GlassCardContent,
  GlassCardHeader,
  GlassCardSubtitle,
  GlassCardTitle,
} from '@/components/mcp-ui/glass';
import { usePriceUpdates } from '@/hooks/useMCPUIStreaming';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface PriceWidgetProps {
  component: MCPUIComponent;
}

export function PriceWidget({ component }: PriceWidgetProps) {
  const {
    title,
    price: initialPrice,
    change: initialChange,
    changeType: initialChangeType,
    volume: initialVolume,
    lastUpdated: initialLastUpdated,
  } = component;

  // State for real-time updates
  const [price, setPrice] = useState(initialPrice);
  const [change, setChange] = useState(initialChange);
  const [changeType, setChangeType] = useState(initialChangeType);
  const [volume, setVolume] = useState(initialVolume);
  const [lastUpdated, setLastUpdated] = useState(initialLastUpdated);

  // Extract token ID from title (e.g., "BTC Price" -> "BTC")
  const tokenId = title?.split(' ')[0] || 'UNKNOWN';

  // Real-time price updates
  usePriceUpdates(tokenId.toLowerCase(), (data) => {
    setPrice(`$${data.price?.toLocaleString() || data.price}`);
    setChange(`${data.change_24h >= 0 ? '+' : ''}${data.change_24h?.toFixed(2) || 0}%`);
    setChangeType(data.change_24h >= 0 ? 'positive' : 'negative');
    setVolume(`$${(data.volume_24h / 1000000)?.toFixed(1) || 0}M`);
    setLastUpdated(data.timestamp);
  });

  const isPositive = changeType === 'positive';

  // Glassmorphism color scheme
  const trendColor = isPositive ? 'text-green-300' : 'text-red-300'; // var(--text-success/error)
  const volumeColor = 'text-white/55'; // var(--text-tertiary)

  return (
    <GlassCard className="w-full" variant="price">
      <GlassCardHeader>
        <GlassCardTitle>{title || 'Price'}</GlassCardTitle>
      </GlassCardHeader>
      <GlassCardContent>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            {/* Price display with larger font */}
            <div className="font-mono text-2xl font-bold text-white/95">{price}</div>
            {/* Trend indicator with animation */}
            <div
              className={`mt-2 flex items-center text-sm font-medium transition-colors duration-300 ${trendColor}`}
            >
              {isPositive ? (
                <TrendUp className="mr-1 h-4 w-4 animate-pulse" />
              ) : (
                <TrendDown className="mr-1 h-4 w-4 animate-pulse" />
              )}
              {change}
            </div>
          </div>
          {volume && (
            <div className="ml-4 text-right">
              <GlassCardSubtitle className="text-xs">24h Volume</GlassCardSubtitle>
              <p className={`text-sm font-medium ${volumeColor}`}>{volume}</p>
            </div>
          )}
        </div>
        {lastUpdated && (
          <GlassCardSubtitle className="mt-3">
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </GlassCardSubtitle>
        )}
      </GlassCardContent>
    </GlassCard>
  );
}
