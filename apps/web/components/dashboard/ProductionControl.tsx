'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ShieldIcon, ExclamationTriangleIcon, PlayIcon, PauseIcon, StopIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

interface ProductionStatus {
  state: string;
  checklist: Record<string, boolean>;
  shadow_stats?: {
    total_intents: number;
    duration_hours: number;
    would_be_pnl: number;
  };
  canary_stats?: {
    total_trades: number;
    success_rate: number;
    total_pnl: number;
  };
  daily_pnl?: number;
  positions_count?: number;
  trades_today?: number;
}

export function ProductionControl() {
  const [systemState, setSystemState] = useState('initializing');
  const [confirmationCode, setConfirmationCode] = useState('');
  
  const { data: status, refetch } = useQuery<ProductionStatus>({
    queryKey: ['production-status'],
    queryFn: async () => {
      const response = await fetch('/api/production/status');
      return response.json();
    },
    refetchInterval: 2000,
  });

  const runPreflight = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/production/preflight', { method: 'POST' });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const startShadow = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/production/shadow', { method: 'POST' });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const startCanary = useMutation({
    mutationFn: async (size: number) => {
      const response = await fetch('/api/production/canary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ size }),
      });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const enableLive = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('/api/production/live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirmation: code }),
      });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const emergencyStop = useMutation({
    mutationFn: async (reason: string) => {
      const response = await fetch('/api/production/emergency-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const pauseTrading = useMutation({
    mutationFn: async (duration: number) => {
      const response = await fetch('/api/production/pause', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration }),
      });
      return response.json();
    },
    onSuccess: () => refetch(),
  });

  const getStateColor = (state: string) => {
    const colors = {
      initializing: 'text-text-secondary',
      testing: 'text-blue-500',
      shadow: 'text-purple-500',
      canary: 'text-yellow-500',
      ramping: 'text-orange-500',
      live: 'text-primary',
      paused: 'text-warning',
      emergency_stop: 'text-red-400',
    };
    return colors[state] || 'text-text-secondary';
  };

  const getStateIcon = (state: string) => {
    const iconProps = { className: "w-5 h-5" };
    const icons = {
      initializing: <ShieldIcon {...iconProps} />,
      testing: <ShieldIcon {...iconProps} />,
      shadow: <ShieldIcon {...iconProps} />,
      canary: <ExclamationTriangleIcon {...iconProps} />,
      ramping: <ExclamationTriangleIcon {...iconProps} />,
      live: <PlayIcon {...iconProps} />,
      paused: <PauseIcon {...iconProps} />,
      emergency_stop: <StopIcon {...iconProps} />,
    };
    return icons[state] || <ShieldIcon {...iconProps} />;
  };

  return (
    <div className="space-y-6">
      {/* System State */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text-primary">Production Control Center</h2>
          <div className={`flex items-center gap-2 ${getStateColor(status?.state || 'initializing')}`}>
            {getStateIcon(status?.state || 'initializing')}
            <span className="text-lg font-semibold uppercase">{status?.state || 'INITIALIZING'}</span>
          </div>
        </div>

        {/* Pre-flight Checklist */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-text-primary">Pre-Flight Checklist</h3>
            <button
              onClick={() => runPreflight.mutate()}
              disabled={runPreflight.isPending}
              className="px-3 py-1 text-xs bg-primary/20 text-primary border border-primary rounded hover:bg-primary/30 disabled:opacity-50"
            >
              {runPreflight.isPending ? 'Checking...' : 'Run Check'}
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            {status?.checklist && Object.entries(status.checklist).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-2 bg-background rounded">
                <span className="text-xs text-text-secondary">
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                {value ? (
                  <CheckCircleIcon className="w-4 h-4 text-primary" />
                ) : (
                  <XCircleIcon className="w-4 h-4 text-red-400" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Control Flow */}
        <div className="space-y-3">
          {/* Shadow Mode */}
          <div className="p-4 bg-background rounded border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Shadow Mode</p>
                <p className="text-xs text-text-secondary mt-1">
                  Trade simulation without placing orders
                </p>
                {status?.shadow_stats && (
                  <p className="text-xs text-text-tertiary mt-1">
                    {status.shadow_stats.total_intents} intents generated
                  </p>
                )}
              </div>
              <button
                onClick={() => startShadow.mutate()}
                disabled={status?.state !== 'testing' || startShadow.isPending}
                className="px-4 py-2 bg-purple-500/20 text-purple-500 border border-purple-500 rounded hover:bg-purple-500/30 disabled:opacity-50"
              >
                {startShadow.isPending ? 'Starting...' : 'Start Shadow'}
              </button>
            </div>
          </div>

          {/* Canary Mode */}
          <div className="p-4 bg-background rounded border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-text-primary">Canary Mode</p>
                <p className="text-xs text-text-secondary mt-1">
                  Small test trades with real money
                </p>
                {status?.canary_stats && (
                  <p className="text-xs text-text-tertiary mt-1">
                    Success rate: {((status.canary_stats.success_rate ?? 0) * 100).toFixed(1)}%
                  </p>
                )}
              </div>
              <button
                onClick={() => {
                  const size = prompt('Initial position size (shares)', '1');
                  if (size) startCanary.mutate(parseInt(size));
                }}
                disabled={status?.state !== 'shadow' || startCanary.isPending}
                className="px-4 py-2 bg-yellow-500/20 text-yellow-500 border border-yellow-500 rounded hover:bg-yellow-500/30 disabled:opacity-50"
              >
                {startCanary.isPending ? 'Starting...' : 'Start Canary'}
              </button>
            </div>
          </div>

          {/* Live Trading */}
          <div className="p-4 bg-background rounded border border-red-400">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-400">Live Trading</p>
                <p className="text-xs text-text-secondary mt-1">
                  Full automated trading with real money
                </p>
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Confirmation code"
                  value={confirmationCode}
                  onChange={(e) => setConfirmationCode(e.target.value)}
                  className="px-2 py-1 text-xs bg-background border border-border rounded"
                />
                <button
                  onClick={() => enableLive.mutate(confirmationCode)}
                  disabled={status?.state !== 'ramping' || enableLive.isPending}
                  className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-400 rounded hover:bg-red-500/30 disabled:opacity-50"
                >
                  {enableLive.isPending ? 'Enabling...' : 'Enable Live'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Emergency Controls */}
        <div className="mt-6 pt-6 border-t border-border">
          <h3 className="text-sm font-medium text-red-400 mb-3">Emergency Controls</h3>
          <div className="flex gap-2">
            <button
              onClick={() => {
                if (confirm('Are you sure you want to pause trading?')) {
                  pauseTrading.mutate(60);
                }
              }}
              disabled={pauseTrading.isPending}
              className="px-4 py-2 bg-warning/20 text-warning border border-warning rounded hover:bg-warning/30 disabled:opacity-50"
            >
              {pauseTrading.isPending ? 'Pausing...' : 'Pause Trading'}
            </button>
            <button
              onClick={() => {
                const reason = prompt('Reason for emergency stop:');
                if (reason && confirm('This will IMMEDIATELY stop all trading. Continue?')) {
                  emergencyStop.mutate(reason);
                }
              }}
              disabled={emergencyStop.isPending}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
            >
              {emergencyStop.isPending ? 'Stopping...' : '🚨 EMERGENCY STOP'}
            </button>
          </div>
        </div>
      </div>

      {/* Live Statistics */}
      {status?.state === 'live' && (
        <div className="grid grid-cols-3 gap-4">
          <div className="glass-card p-4">
            <p className="text-xs text-text-secondary mb-2">Daily P&L</p>
            <p className={`text-2xl font-bold ${(status.daily_pnl || 0) >= 0 ? 'text-primary' : 'text-red-400'}`}>
              ${(status.daily_pnl ?? 0).toFixed(2)}
            </p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-text-secondary mb-2">Active Positions</p>
            <p className="text-2xl font-bold text-text-primary">{status.positions_count || 0}</p>
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-text-secondary mb-2">Today's Trades</p>
            <p className="text-2xl font-bold text-text-primary">{status.trades_today || 0}</p>
          </div>
        </div>
      )}

      {/* Warning Banner for Live Mode */}
      {status?.state === 'live' && (
        <div className="bg-red-500/10 border border-red-400 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-400 flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-red-400">Live Trading Active</p>
              <p className="text-xs text-text-secondary mt-1">
                System is trading with real money. Monitor closely during market hours.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}