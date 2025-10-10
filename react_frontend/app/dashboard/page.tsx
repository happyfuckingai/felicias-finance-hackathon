'use client';

import React from 'react';
import { motion } from 'motion/react';
import { useAuth } from '@/lib/auth-context';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { GlassCard, GlassCardContent, GlassCardHeader, GlassCardTitle } from '@/components/mcp-ui/glass';
import { Button } from '@/components/ui/button';
import { MCPUIDashboardComponent } from '@/components/mcp-ui-dashboard';
import { BalanceCard } from '@/components/mcp-ui/banking/balance-card';
import { PortfolioChart } from '@/components/mcp-ui/crypto/portfolio-chart';
import { RiskDashboard } from '@/components/mcp-ui/crypto/risk-dashboard';
import { SignOut, User, Gear, CreditCard } from '@phosphor-icons/react';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  // Mock dashboard data
  const mockDashboard = {
    components: [
      {
        id: 'balance',
        type: 'balance-card',
        title: 'Account Balance',
        value: '$12,345.67',
        subtitle: 'Available Balance',
        trend: '+2.5%',
        trendDirection: 'positive',
        lastUpdated: new Date().toISOString(),
      },
      {
        id: 'portfolio',
        type: 'portfolio-chart',
        title: 'Portfolio Performance',
        chartType: 'area',
        data: [
          { date: '2024-01-01', value: 10000 },
          { date: '2024-02-01', value: 10500 },
          { date: '2024-03-01', value: 11200 },
          { date: '2024-04-01', value: 11800 },
          { date: '2024-05-01', value: 12300 },
        ],
        xAxis: 'date',
        yAxis: 'value',
        color: '#8b5cf6',
      },
      {
        id: 'risk',
        type: 'risk-dashboard',
        title: 'Risk Assessment',
        riskLevel: 'medium',
        riskScore: 65,
        recommendations: [
          'Diversify crypto holdings',
          'Consider dollar-cost averaging',
          'Monitor market volatility',
        ],
      },
    ],
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        {/* Header */}
        <header className="border-b border-white/10 bg-black/20 backdrop-blur-xl">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold text-white">Felicia's Finance</h1>
                <div className="text-sm text-white/70">
                  Welcome back, {user?.name || user?.email}
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-white/70">
                  <CreditCard className="w-4 h-4" />
                  <span>{user?.subscription?.plan || 'Free'} Plan</span>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  className="text-white/70 hover:text-white"
                >
                  <Gear className="w-4 h-4 mr-2" />
                  Settings
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-white/70 hover:text-white"
                >
                  <SignOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Financial Overview */}
            <div className="lg:col-span-2 space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <GlassCard depth="surface" className="p-6">
                  <GlassCardHeader>
                    <GlassCardTitle>Financial Overview</GlassCardTitle>
                  </GlassCardHeader>
                  <GlassCardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <BalanceCard component={mockDashboard.components[0]} />
                      <PortfolioChart component={mockDashboard.components[1]} />
                    </div>
                  </GlassCardContent>
                </GlassCard>
              </motion.div>

              {/* AI Assistant Section */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <GlassCard depth="surface" className="p-6">
                  <GlassCardHeader>
                    <GlassCardTitle>AI Financial Assistant</GlassCardTitle>
                  </GlassCardHeader>
                  <GlassCardContent>
                    <p className="text-white/70 mb-4">
                      Get personalized financial advice and insights powered by AI.
                    </p>
                    <Button className="bg-primary hover:bg-primary-hover">
                      Start Conversation
                    </Button>
                  </GlassCardContent>
                </GlassCard>
              </motion.div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <RiskDashboard component={mockDashboard.components[2]} />
              </motion.div>

              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <GlassCard depth="surface" className="p-6">
                  <GlassCardHeader>
                    <GlassCardTitle>Quick Actions</GlassCardTitle>
                  </GlassCardHeader>
                  <GlassCardContent className="space-y-3">
                    <Button variant="outline" className="w-full justify-start">
                      <CreditCard className="w-4 h-4 mr-2" />
                      Transfer Money
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <User className="w-4 h-4 mr-2" />
                      Pay Bills
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Gear className="w-4 h-4 mr-2" />
                      Investment Goals
                    </Button>
                  </GlassCardContent>
                </GlassCard>
              </motion.div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}