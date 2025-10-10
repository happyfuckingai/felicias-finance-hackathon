import React from 'react';
import { Minus, TrendDown, TrendUp } from '@phosphor-icons/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface TradingSignalsProps {
  component: MCPUIComponent;
}

export function TradingSignals({ component }: TradingSignalsProps) {
  const { title, signals = [], lastUpdated } = component;

  const getSignalIcon = (signal: string) => {
    switch (signal?.toUpperCase()) {
      case 'BUY':
        return <TrendUp className="h-4 w-4 text-green-600" />;
      case 'SELL':
        return <TrendDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal?.toUpperCase()) {
      case 'BUY':
        return 'bg-green-50 border-green-200';
      case 'SELL':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {title || 'Trading Signals'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {signals.length === 0 ? (
          <div className="py-6 text-center">
            <p className="text-muted-foreground text-sm">No trading signals available</p>
          </div>
        ) : (
          <div className="space-y-3">
            {signals.map((signal: any, index: number) => (
              <div
                key={index}
                className={`flex items-center justify-between rounded-lg border p-3 ${getSignalColor(signal.signal)}`}
              >
                <div className="flex items-center space-x-3">
                  {getSignalIcon(signal.signal)}
                  <div>
                    <p className="text-sm font-medium">{signal.token_id || signal.token}</p>
                    <p className="text-muted-foreground text-xs">
                      {signal.analysis_method?.replace('_', ' ').toUpperCase() || 'TECHNICAL'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold">{signal.signal}</p>
                  <p className={`text-xs ${getConfidenceColor(signal.confidence)}`}>
                    {(signal.confidence * 100).toFixed(0)}% confidence
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {lastUpdated && (
          <p className="text-muted-foreground mt-3 text-xs">
            Last updated: {new Date(lastUpdated).toLocaleString()}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
