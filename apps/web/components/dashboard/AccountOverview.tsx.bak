'use client';

import { useQuery } from '@tanstack/react-query';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { api } from '@/lib/api-client';
import { formatCurrency, formatPercent } from '@/lib/utils';

export function AccountOverview() {
  const { data: account, isLoading } = useQuery({
    queryKey: ['account'],
    queryFn: async () => (await api.getAccount()).data,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="glass-card p-6 animate-pulse">Loading...</div>;
  }

  const metrics = [
    {
      label: 'Equity',
      value: formatCurrency(account?.equity || 0),
      change: account?.daily_pnl || 0,
      icon: DollarSign,
    },
    {
      label: 'Cash',
      value: formatCurrency(account?.cash || 0),
      icon: DollarSign,
    },
    {
      label: 'Daily P&L',
      value: formatCurrency(account?.daily_pnl || 0),
      isProfit: (account?.daily_pnl || 0) >= 0,
      icon: (account?.daily_pnl || 0) >= 0 ? TrendingUp : TrendingDown,
    },
  ];

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Account Overview</h2>
        <div className="flex items-center gap-2">
          <span className="status-dot bg-primary"></span>
          <span className="text-xs text-text-secondary">MARKET OPEN</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {metrics.map((metric, i) => (
          <div key={i} className="space-y-1">
            <div className="flex items-center gap-2">
              <metric.icon className="w-4 h-4 text-text-tertiary" />
              <span className="text-xs text-text-secondary">{metric.label}</span>
            </div>
            <p className={`data-cell text-lg font-semibold ${
              metric.isProfit !== undefined
                ? metric.isProfit ? 'text-primary' : 'text-danger'
                : 'text-text-primary'
            }`}>
              {metric.value}
            </p>
            {metric.change !== undefined && (
              <p className={`text-xs ${metric.change >= 0 ? 'text-primary' : 'text-danger'}`}>
                {metric.change >= 0 ? '+' : ''}{formatCurrency(metric.change)}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}