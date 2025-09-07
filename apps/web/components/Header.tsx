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

  // Get current time in 12-hour format
  const currentTime = new Date();
  const nycTime = currentTime.toLocaleTimeString('en-US', { 
    timeZone: 'America/New_York',
    hour12: true,
    hour: 'numeric',
    minute: '2-digit'
  });
  const tokyoTime = currentTime.toLocaleTimeString('en-US', { 
    timeZone: 'Asia/Tokyo',
    hour12: true,
    hour: 'numeric',
    minute: '2-digit'
  });

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-lg">
      <div className="px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <span className="text-primary">▲</span> MULROY STREET CAPITAL
          </h1>
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
    </header>
  );
}