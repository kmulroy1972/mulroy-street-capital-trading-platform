'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, CheckCircle, X, Bell, BellOff } from 'lucide-react';

interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  source: string;
  title: string;
  message: string;
  timestamp: string;
  resolved: boolean;
  resolved_at?: string;
  metadata?: any;
}

interface AlertsData {
  status: string;
  active: Alert[];
  total: number;
  alerts: Alert[];
}

interface AlertsPanelProps {
  editMode?: boolean;
}

export default function AlertsPanel({ editMode = false }: AlertsPanelProps) {
  const [showResolved, setShowResolved] = useState(false);
  const [mutedAlerts, setMutedAlerts] = useState(new Set<string>());
  const [alerts, setAlerts] = useState<AlertsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch(`/api/monitoring/alerts?status=${showResolved ? 'all' : 'active'}`);
        const data = await response.json();
        setAlerts(data);
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, [showResolved]);

  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/monitoring/alerts/${alertId}/resolve`, {
        method: 'POST',
      });
      if (response.ok) {
        // Refresh alerts
        const alertsResponse = await fetch(`/api/monitoring/alerts?status=${showResolved ? 'all' : 'active'}`);
        const data = await alertsResponse.json();
        setAlerts(data);
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  const getSeverityIcon = (severity: string) => {
    const icons = {
      critical: <AlertTriangle className="w-4 h-4 text-red-400" />,
      error: <AlertTriangle className="w-4 h-4 text-orange-400" />,
      warning: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
      info: <Bell className="w-4 h-4 text-blue-400" />,
    };
    return icons[severity] || icons.info;
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      critical: 'bg-red-400/10 border-red-400 text-red-400',
      error: 'bg-orange-400/10 border-orange-400 text-orange-400',
      warning: 'bg-yellow-400/10 border-yellow-400 text-yellow-400',
      info: 'bg-blue-400/10 border-blue-400 text-blue-400',
    };
    return colors[severity] || colors.info;
  };

  const toggleMute = (alertId: string) => {
    const newMuted = new Set(mutedAlerts);
    if (newMuted.has(alertId)) {
      newMuted.delete(alertId);
    } else {
      newMuted.add(alertId);
    }
    setMutedAlerts(newMuted);
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-muted h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Alerts</CardTitle>
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

  return (
    <Card className="bg-card border-muted h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>Alerts</span>
            <span className="px-2 py-1 text-xs bg-red-400/20 text-red-400 rounded">
              {alerts?.active?.length || 0} Active
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowResolved(!showResolved)}
            className="text-xs h-6"
          >
            {showResolved ? 'Hide' : 'Show'} Resolved
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {alerts?.alerts?.map((alert) => (
            <div
              key={alert.id}
              className={`p-2 rounded border transition-all text-xs ${
                alert.resolved
                  ? 'opacity-50 bg-muted/30 border-muted'
                  : getSeverityColor(alert.severity)
              } ${mutedAlerts.has(alert.id) ? 'opacity-30' : ''}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2 flex-1">
                  {getSeverityIcon(alert.severity)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{alert.title}</p>
                    <p className="text-[10px] mt-1 opacity-80 line-clamp-2">{alert.message}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] opacity-60">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                      <span className="text-[10px] opacity-60">
                        {alert.source}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-1">
                  {!alert.resolved && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleMute(alert.id)}
                        className="p-1 h-6 w-6"
                        title={mutedAlerts.has(alert.id) ? "Unmute" : "Mute"}
                      >
                        {mutedAlerts.has(alert.id) ? 
                          <BellOff className="w-3 h-3" /> : 
                          <Bell className="w-3 h-3" />
                        }
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => resolveAlert(alert.id)}
                        className="p-1 h-6 w-6"
                        title="Resolve"
                      >
                        <CheckCircle className="w-3 h-3" />
                      </Button>
                    </>
                  )}
                  {alert.resolved && (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {(!alerts?.alerts || alerts.alerts.length === 0) && (
            <div className="text-center py-6 text-muted-foreground">
              <Bell className="w-6 h-6 mx-auto mb-2 opacity-50" />
              <p className="text-xs">No alerts</p>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex justify-between text-[10px] text-muted-foreground pt-2 border-t border-muted mt-3">
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
            Monitoring
          </div>
          <div>
            {alerts?.total || 0} total today
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

const DEFAULT_CONFIG = `monitoring:
  alerts:
    discord:
      enabled: false
      webhook_url: "YOUR_WEBHOOK_URL"
      min_severity: warning
  
  thresholds:
    heartbeat_timeout: 60
    daily_loss_limit: 1000
    order_reject_rate: 0.1
    latency_95th: 1000
    error_rate: 0.05
    position_concentration: 0.3
    max_drawdown: 0.15
  
  logging:
    level: INFO
    format: json
`;