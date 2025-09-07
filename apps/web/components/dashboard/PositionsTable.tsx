'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface Position {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
}

export function PositionsTable() {
  const { data: positions = [], isLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => (await api.getPositions()).data as Position[],
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="glass-card p-6 animate-pulse">Loading positions...</div>;
  }

  return (
    <div className="glass-card p-6">
      <h2 className="text-lg font-semibold text-text-primary mb-4">
        Positions / Orders / Activity
      </h2>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-2 text-xs text-text-secondary font-medium">Symbol</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">Qty</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">Avg Price</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">Current</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">P&L</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">P&L %</th>
              <th className="text-right py-2 text-xs text-text-secondary font-medium">Value</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position: Position) => (
              <tr key={position.symbol} className="border-b border-border/50 hover:bg-card-hover transition-colors">
                <td className="py-3">
                  <span className="font-medium text-text-primary">{position.symbol}</span>
                </td>
                <td className="text-right data-cell">{position.qty}</td>
                <td className="text-right data-cell">{formatCurrency(position.avg_entry_price)}</td>
                <td className="text-right data-cell">{formatCurrency(position.current_price)}</td>
                <td className={`text-right data-cell ${position.unrealized_pnl >= 0 ? 'text-primary' : 'text-danger'}`}>
                  <div className="flex items-center justify-end gap-1">
                    {position.unrealized_pnl >= 0 ? 
                      <TrendingUp className="w-3 h-3" /> : 
                      <TrendingDown className="w-3 h-3" />
                    }
                    {formatCurrency(position.unrealized_pnl)}
                  </div>
                </td>
                <td className={`text-right data-cell ${position.unrealized_pnl_pct >= 0 ? 'text-primary' : 'text-danger'}`}>
                  {formatPercent(position.unrealized_pnl_pct)}
                </td>
                <td className="text-right data-cell">{formatCurrency(position.market_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {positions.length === 0 && (
          <div className="text-center py-8 text-text-secondary">
            No positions held
          </div>
        )}
      </div>
    </div>
  );
}