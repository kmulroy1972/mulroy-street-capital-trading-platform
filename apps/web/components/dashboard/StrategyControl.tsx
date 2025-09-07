'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Settings, 
  TrendingUp, 
  Eye,
  Zap 
} from 'lucide-react';

interface Strategy {
  name: string;
  version: string;
  enabled: boolean;
  mode: 'shadow' | 'canary' | 'enabled';
  status: 'running' | 'stopped' | 'error' | 'reloading';
  performance: {
    dailyPnL: number;
    totalTrades: number;
    winRate: number;
    lastSignal: string | null;
  };
  config: {
    position_size: number;
    max_positions: number;
    symbols: string[];
  };
}

interface StrategyControlProps {
  allowHotReload?: boolean;
  showBacktest?: boolean;
  editMode?: boolean;
}

export default function StrategyControl({ 
  allowHotReload = true, 
  showBacktest = true,
  editMode = false 
}: StrategyControlProps) {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await fetch('/api/strategies');
        const data = await response.json();
        setStrategies(data);
        if (data.length > 0 && !selectedStrategy) {
          setSelectedStrategy(data[0].name);
        }
      } catch (error) {
        console.error('Failed to fetch strategies:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStrategies();
    const interval = setInterval(fetchStrategies, 3000); // Update every 3 seconds
    return () => clearInterval(interval);
  }, [selectedStrategy]);

  const handleStrategyToggle = async (strategyName: string, enabled: boolean) => {
    try {
      await fetch(`/api/strategies/${strategyName}/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
    } catch (error) {
      console.error('Failed to toggle strategy:', error);
    }
  };

  const handleModeChange = async (strategyName: string, mode: string) => {
    try {
      await fetch(`/api/strategies/${strategyName}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
    } catch (error) {
      console.error('Failed to change strategy mode:', error);
    }
  };

  const handleHotReload = async (strategyName: string) => {
    try {
      await fetch(`/api/strategies/${strategyName}/reload`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Failed to reload strategy:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-400/20 text-green-400';
      case 'stopped': return 'bg-gray-400/20 text-gray-400';
      case 'error': return 'bg-red-400/20 text-red-400';
      case 'reloading': return 'bg-blue-400/20 text-blue-400';
      default: return 'bg-gray-400/20 text-gray-400';
    }
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'shadow': return <Eye className="w-3 h-3" />;
      case 'canary': return <Zap className="w-3 h-3" />;
      case 'enabled': return <Play className="w-3 h-3" />;
      default: return <Pause className="w-3 h-3" />;
    }
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-muted h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Strategy Control</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            <div className="h-4 bg-muted rounded"></div>
            <div className="h-4 bg-muted rounded w-3/4"></div>
            <div className="h-4 bg-muted rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStrategy = strategies.find(s => s.name === selectedStrategy);

  return (
    <Card className="bg-card border-muted h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Strategy Control</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Strategy Selector */}
        <div className="space-y-2">
          <div className="text-xs text-muted-foreground">Active Strategies</div>
          <div className="space-y-1">
            {strategies.map((strategy) => (
              <div
                key={strategy.name}
                className={`p-2 rounded border cursor-pointer transition-colors ${
                  selectedStrategy === strategy.name
                    ? 'border-primary bg-primary/10'
                    : 'border-muted hover:border-muted-foreground/50'
                }`}
                onClick={() => setSelectedStrategy(strategy.name)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`text-xs ${getRiskColor(strategy.mode.toUpperCase())}`}>
                      {getModeIcon(strategy.mode)}
                    </div>
                    <span className="text-xs font-medium">{strategy.name}</span>
                  </div>
                  <Badge className={getStatusColor(strategy.status)}>
                    {strategy.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategy Details */}
        {currentStrategy && (
          <div className="space-y-3 pt-2 border-t border-muted">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="text-muted-foreground">Daily P&L</div>
                <div className={currentStrategy.performance.dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {formatCurrency(currentStrategy.performance.dailyPnL)}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Win Rate</div>
                <div className="text-primary">
                  {((currentStrategy.performance.winRate ?? 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <div className="text-muted-foreground">Trades Today</div>
                <div className="text-primary">{currentStrategy.performance.totalTrades}</div>
              </div>
              <div>
                <div className="text-muted-foreground">Positions</div>
                <div className="text-primary">
                  {currentStrategy.config.max_positions - currentStrategy.config.position_size}
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Enabled</span>
                <Switch
                  checked={currentStrategy.enabled}
                  onCheckedChange={(enabled) => 
                    handleStrategyToggle(currentStrategy.name, enabled)
                  }
                />
              </div>

              <div className="flex gap-1">
                <Button
                  variant={currentStrategy.mode === 'shadow' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleModeChange(currentStrategy.name, 'shadow')}
                  className="flex-1 text-xs h-6"
                >
                  <Eye className="w-3 h-3 mr-1" />
                  Shadow
                </Button>
                <Button
                  variant={currentStrategy.mode === 'canary' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleModeChange(currentStrategy.name, 'canary')}
                  className="flex-1 text-xs h-6"
                >
                  <Zap className="w-3 h-3 mr-1" />
                  Canary
                </Button>
                <Button
                  variant={currentStrategy.mode === 'enabled' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleModeChange(currentStrategy.name, 'enabled')}
                  className="flex-1 text-xs h-6"
                >
                  <Play className="w-3 h-3 mr-1" />
                  Live
                </Button>
              </div>

              {allowHotReload && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleHotReload(currentStrategy.name)}
                  disabled={currentStrategy.status === 'reloading'}
                  className="w-full text-xs h-6"
                >
                  <RotateCcw className="w-3 h-3 mr-1" />
                  {currentStrategy.status === 'reloading' ? 'Reloading...' : 'Hot Reload'}
                </Button>
              )}
            </div>

            {/* Quick Stats */}
            <div className="text-[10px] text-muted-foreground">
              <div>Symbols: {currentStrategy.config.symbols.join(', ')}</div>
              <div>
                Last Signal: {currentStrategy.performance.lastSignal || 'None'}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between text-[10px] text-muted-foreground pt-2 border-t border-muted">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
            Engine
          </div>
          <div>
            {strategies.length} strategies
          </div>
        </div>
      </CardContent>
    </Card>
  );
}