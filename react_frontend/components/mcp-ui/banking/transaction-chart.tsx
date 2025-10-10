import React from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { MCPUIComponent } from '@/lib/mcp-ui-client';

interface TransactionChartProps {
  component: MCPUIComponent;
}

export function TransactionChart({ component }: TransactionChartProps) {
  const { title, chartType = 'bar', data = [], xAxis, yAxes = [], colors = {} } = component;

  // Transform data for the chart
  const chartData = data.map((item: any) => {
    const transformed: any = { ...item };
    if (xAxis) {
      transformed[xAxis] = item[xAxis];
    }
    return transformed;
  });

  const renderChart = () => {
    if (chartType === 'line') {
      return (
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxis || 'date'} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
            }}
          />
          {yAxes.map((axis: string, index: number) => (
            <Line
              key={axis}
              type="monotone"
              dataKey={axis}
              stroke={colors[axis] || `hsl(${index * 60}, 70%, 50%)`}
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          ))}
        </LineChart>
      );
    }

    return (
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xAxis || 'date'} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--background))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
          }}
        />
        {yAxes.map((axis: string, index: number) => (
          <Bar
            key={axis}
            dataKey={axis}
            fill={colors[axis] || `hsl(${index * 60}, 70%, 50%)`}
            radius={[2, 2, 0, 0]}
          />
        ))}
      </BarChart>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-sm font-medium">
          {title || 'Transaction Chart'}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ width: '100%', height: component.height || '300px' }}>
          <ResponsiveContainer>{renderChart()}</ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
