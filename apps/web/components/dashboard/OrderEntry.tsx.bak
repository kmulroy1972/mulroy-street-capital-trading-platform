'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export function OrderEntry() {
  const [symbol, setSymbol] = useState('');
  const [orderType, setOrderType] = useState('Market');
  const [quantity, setQuantity] = useState('');
  const [price, setPrice] = useState('');

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">Order Entry</h2>
        <button className="text-text-tertiary hover:text-text-secondary">
          <ChevronDown className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-xs text-text-secondary mb-1 block">Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full bg-background border border-border rounded px-3 py-2 text-sm font-mono focus:border-primary focus:outline-none"
            placeholder="AAPL"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-text-secondary mb-1 block">Type</label>
            <select 
              value={orderType}
              onChange={(e) => setOrderType(e.target.value)}
              className="w-full bg-background border border-border rounded px-3 py-2 text-sm focus:border-primary focus:outline-none"
            >
              <option>Market</option>
              <option>Limit</option>
              <option>Stop</option>
              <option>Stop Limit</option>
            </select>
          </div>

          <div>
            <label className="text-xs text-text-secondary mb-1 block">Quantity</label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full bg-background border border-border rounded px-3 py-2 text-sm font-mono focus:border-primary focus:outline-none"
              placeholder="100"
            />
          </div>
        </div>

        {orderType !== 'Market' && (
          <div>
            <label className="text-xs text-text-secondary mb-1 block">Price</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full bg-background border border-border rounded px-3 py-2 text-sm font-mono focus:border-primary focus:outline-none"
              placeholder="0.00"
            />
          </div>
        )}

        <div className="flex gap-2">
          <button className="flex-1 bg-primary hover:bg-primary-dim text-background font-semibold py-2 rounded transition-colors neon-glow">
            BUY • [B]
          </button>
          <button className="flex-1 bg-danger hover:bg-danger-dim text-white font-semibold py-2 rounded transition-colors danger-glow">
            SELL • [S]
          </button>
        </div>

        <div className="pt-2 border-t border-border">
          <div className="flex items-center justify-between text-xs">
            <span className="text-text-secondary">Risk Level: SPY, Breaker</span>
            <span className="text-text-tertiary">MarketLorde InOut/OCO Day Bsc Confirm Trade</span>
          </div>
        </div>
      </div>
    </div>
  );
}