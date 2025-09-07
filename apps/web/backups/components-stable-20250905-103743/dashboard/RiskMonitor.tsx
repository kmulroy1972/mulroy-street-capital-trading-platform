'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Shield, ShieldAlert, StopCircle } from 'lucide-react';

interface RiskMetrics {
  dailyPnL: number;
  weeklyPnL: number;
  totalExposure: number;
  positionCount: number;
  marginUsed: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  activeAlerts: RiskAlert[];
  limits: {
    dailyLossLimit: number;
    weeklyLossLimit: number;
    maxPositionSize: number;
    maxExposure: number;
  };
}

interface RiskAlert {
  id: string;
  type: 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
}

interface RiskMonitorProps {
  showAlerts?: boolean;
  alertThreshold?: number;
  editMode?: boolean;
}

export default function RiskMonitor({ 
  showAlerts = true, 
  alertThreshold = 0.5,
  editMode = false 
}: RiskMonitorProps) {
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [emergencyStop, setEmergencyStop] = useState(false);

  useEffect(() => {
    const fetchRiskMetrics = async () => {
      try {
        const response = await fetch('/api/risk/metrics');
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch risk metrics:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRiskMetrics();
    const interval = setInterval(fetchRiskMetrics, 2000); // Update every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const handleEmergencyStop = async () => {
    try {
      const response = await fetch('/api/risk/emergency-stop', {
        method: 'POST',
      });
      if (response.ok) {
        setEmergencyStop(true);
      }
    } catch (error) {
      console.error('Failed to trigger emergency stop:', error);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'HIGH': return 'text-orange-400';
      case 'CRITICAL': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'LOW': return <Shield className="w-4 h-4" />;
      case 'MEDIUM': return <AlertTriangle className="w-4 h-4" />;
      case 'HIGH': return <ShieldAlert className="w-4 h-4" />;
      case 'CRITICAL': return <StopCircle className="w-4 h-4" />;
      default: return <Shield className="w-4 h-4" />;
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number, total: number) => {
    if (!total || total === 0) return '0.0%';
    return `${(((value ?? 0) / total) * 100).toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-muted h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Risk Monitor</CardTitle>
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

  if (!metrics) {
    return (
      <Card className="bg-card border-muted h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Risk Monitor</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-sm">Failed to load risk data</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-muted h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span>Risk Monitor</span>
          <div className={`flex items-center gap-1 ${getRiskColor(metrics.riskLevel)}`}>
            {getRiskIcon(metrics.riskLevel)}
            <span className="text-xs">{metrics.riskLevel}</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Risk Overview */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <div className="text-muted-foreground">Daily P&L</div>
            <div className={metrics.dailyPnL >= 0 ? 'text-green-400' : 'text-red-400'}>
              {formatCurrency(metrics.dailyPnL)}
            </div>
            <div className="text-muted-foreground text-[10px]">
              {formatPercentage(Math.abs(metrics.dailyPnL), metrics.limits.dailyLossLimit)} of limit
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Weekly P&L</div>
            <div className={metrics.weeklyPnL >= 0 ? 'text-green-400' : 'text-red-400'}>
              {formatCurrency(metrics.weeklyPnL)}
            </div>
            <div className="text-muted-foreground text-[10px]">
              {formatPercentage(Math.abs(metrics.weeklyPnL), metrics.limits.weeklyLossLimit)} of limit
            </div>
          </div>
        </div>

        {/* Exposure Metrics */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <div className="text-muted-foreground">Total Exposure</div>
            <div className="text-primary">
              {formatCurrency(metrics.totalExposure)}
            </div>
            <div className="text-muted-foreground text-[10px]">
              {formatPercentage(metrics.totalExposure, metrics.limits.maxExposure)} of limit
            </div>
          </div>
          <div>
            <div className="text-muted-foreground">Active Positions</div>
            <div className="text-primary">
              {metrics.positionCount}
            </div>
            <div className="text-muted-foreground text-[10px]">
              Margin: {formatCurrency(metrics.marginUsed)}
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        {showAlerts && metrics.activeAlerts.length > 0 && (
          <div className="space-y-1">
            <div className="text-muted-foreground text-xs">Active Alerts</div>
            <div className="space-y-1 max-h-20 overflow-y-auto">
              {metrics.activeAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className={`text-[10px] p-1 rounded border-l-2 ${
                    alert.type === 'critical'
                      ? 'border-red-400 bg-red-400/10 text-red-400'
                      : alert.type === 'error'
                      ? 'border-orange-400 bg-orange-400/10 text-orange-400'
                      : 'border-yellow-400 bg-yellow-400/10 text-yellow-400'
                  }`}
                >
                  {alert.message}
                </div>
              ))}
              {metrics.activeAlerts.length > 3 && (
                <div className="text-muted-foreground text-[10px]">
                  +{metrics.activeAlerts.length - 3} more alerts
                </div>
              )}
            </div>
          </div>
        )}

        {/* Emergency Controls */}
        <div className="pt-2 border-t border-muted">
          <Button
            variant="destructive"
            size="sm"
            onClick={handleEmergencyStop}
            disabled={emergencyStop}
            className="w-full text-xs h-7"
          >
            <StopCircle className="w-3 h-3 mr-1" />
            {emergencyStop ? 'STOPPED' : 'Emergency Stop'}
          </Button>
        </div>

        {/* Status Indicators */}
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
            Live
          </div>
          <div>
            Last: {new Date().toLocaleTimeString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
