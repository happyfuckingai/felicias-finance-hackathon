import React from 'react';
import { Shield, TrendUp, Warning } from '@phosphor-icons/react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface RiskDashboardProps {
  component: MCPUIComponent;
}

export function RiskDashboard({ component }: RiskDashboardProps) {
  const { title, metrics, riskLevel, recommendations } = component;

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high':
        return <Warning className="h-5 w-5" />;
      case 'medium':
        return <TrendUp className="h-5 w-5" />;
      case 'low':
        return <Shield className="h-5 w-5" />;
      default:
        return <Shield className="h-5 w-5" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {title || 'Risk Analysis'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Risk Level Indicator */}
          <div
            className={`flex items-center space-x-3 rounded-lg border p-3 ${getRiskColor(riskLevel)}`}
          >
            {getRiskIcon(riskLevel)}
            <div>
              <p className="font-medium">
                Risk Level: {riskLevel?.charAt(0).toUpperCase() + riskLevel?.slice(1)}
              </p>
              <p className="text-sm opacity-80">Based on current portfolio metrics</p>
            </div>
          </div>

          {/* Key Metrics */}
          {metrics && (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(metrics).map(([key, value]: [string, any]) => (
                <div key={key} className="text-center">
                  <p className="text-2xl font-bold">{value}</p>
                  <p className="text-muted-foreground text-xs">
                    {key.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Recommendations */}
          {recommendations && recommendations.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Recommendations:</h4>
              <ul className="space-y-1">
                {recommendations.map((rec: string, index: number) => (
                  <li key={index} className="text-muted-foreground flex items-start text-sm">
                    <span className="mt-1.5 mr-2 h-1 w-1 flex-shrink-0 rounded-full bg-current" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
