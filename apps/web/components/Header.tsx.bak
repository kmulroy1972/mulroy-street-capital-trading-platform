'use client';

import { Cloud, CloudOff, Settings, Power } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

export function Header() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.getHealth()).data,
    refetchInterval: 10000,
  });

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-lg">
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <span className="text-primary">▲</span> MULROY STREET CAPITAL
          </h1>
          
          <div className="flex items-center gap-4 text-sm text-text-secondary">
            <span className="flex items-center gap-1">
              <span className="text-text-tertiary">NYC</span>
              <span>16:30</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="text-text-tertiary">🌡️</span>
              <span>78°F</span>
            </span>
            <span>Partly Cloudy</span>
            <span className="flex items-center gap-1">
              <span className="text-text-tertiary">TYO</span>
              <span>05:30</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {health?.status === 'healthy' ? (
              <>
                <Cloud className="w-4 h-4 text-primary" />
                <span className="text-xs text-primary">MSC API: Connected</span>
              </>
            ) : (
              <>
                <CloudOff className="w-4 h-4 text-danger" />
                <span className="text-xs text-danger">MSC API: Disconnected</span>
              </>
            )}
            <span className="text-xs text-text-secondary">• 32ms</span>
            <span className="text-xs text-primary">• MARKET OPEN</span>
          </div>
          
          <div className="flex items-center gap-2">
            <button className="p-2 hover:bg-card-hover rounded transition-colors">
              <Settings className="w-4 h-4 text-text-secondary" />
            </button>
            <button className="p-2 hover:bg-danger/20 rounded transition-colors group">
              <Power className="w-4 h-4 text-text-secondary group-hover:text-danger" />
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 pb-3 flex gap-6">
        {['Main', 'Staging', 'Safe', 'Status'].map((tab) => (
          <button
            key={tab}
            className={`px-4 py-1 text-sm font-medium rounded transition-colors ${
              tab === 'Main'
                ? 'bg-primary/20 text-primary border border-primary'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </header>
  );
}