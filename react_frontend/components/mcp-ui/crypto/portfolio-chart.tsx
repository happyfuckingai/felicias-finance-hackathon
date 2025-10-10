import React from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface PortfolioChartProps {
  component: MCPUIComponent;
}

export function PortfolioChart({ component }: PortfolioChartProps) {
  const {
    title,
    chartType = 'area',
    data = [],
    xAxis,
    yAxis,
    color,
    height = '300px',
    showChange = false,
  } = component;

  // Transform data for the chart
  const chartData = data.map((item: any) => {
    const transformed: any = { ...item };
    if (xAxis) {
      transformed[xAxis] = item[xAxis];
    }
    if (yAxis) {
      transformed[yAxis] = item[yAxis];
    }
    return transformed;
  });

  const renderChart = () => {
    if (chartType === 'area') {
      return (
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxis || 'date'} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
            }}
            formatter={(value: any, name: string) => [
              showChange && name === yAxis
                ? `${value} (${chartData.find((d: any) => d[yAxis] === value)?.change || 0}%)`
                : value,
              name === yAxis ? 'Value' : name,
            ]}
          />
          <Area
            type="monotone"
            dataKey={yAxis || 'value'}
            stroke={color || '#10b981'}
            fill={color || '#10b981'}
            fillOpacity={0.2}
            strokeWidth={2}
          />
        </AreaChart>
      );
    }

    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">Chart type not supported</p>
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {title || 'Portfolio Performance'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ width: '100%', height }}>
          <ResponsiveContainer>{renderChart()}</ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
