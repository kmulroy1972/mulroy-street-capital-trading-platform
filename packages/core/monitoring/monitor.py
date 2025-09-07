import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
from collections import deque, defaultdict

import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest
import structlog

logger = structlog.get_logger()

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Alert:
    id: str
    severity: AlertSeverity
    source: str
    title: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "severity": self.severity.value,
            "source": self.source,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class TradingMonitor:
    """Central monitoring service for the trading system"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.alerts: deque = deque(maxlen=1000)
        self.alert_handlers = []
        self.metrics_buffer = defaultdict(list)
        
        # Prometheus metrics
        self.setup_prometheus_metrics()
        
        # Structured logger
        self.logger = structlog.get_logger()
        
        # Alert thresholds
        self.thresholds = {
            "heartbeat_timeout": 60,  # seconds
            "daily_loss_limit": 1000,
            "order_reject_rate": 0.1,  # 10%
            "latency_95th": 1000,  # ms
            "error_rate": 0.05,  # 5%
            "position_concentration": 0.3,  # 30% in one position
        }
        
    def setup_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        # Trading metrics
        self.orders_placed = Counter('trading_orders_placed_total', 'Total orders placed', ['strategy', 'symbol', 'side'])
        self.orders_filled = Counter('trading_orders_filled_total', 'Total orders filled', ['strategy', 'symbol', 'side'])
        self.orders_rejected = Counter('trading_orders_rejected_total', 'Total orders rejected', ['strategy', 'reason'])
        
        # Performance metrics
        self.order_latency = Histogram('trading_order_latency_ms', 'Order placement latency', ['strategy'])
        self.fill_latency = Histogram('trading_fill_latency_ms', 'Order fill latency', ['strategy'])
        
        # P&L metrics
        self.daily_pnl = Gauge('trading_daily_pnl_dollars', 'Daily P&L in dollars')
        self.total_pnl = Gauge('trading_total_pnl_dollars', 'Total P&L in dollars')
        self.positions_value = Gauge('trading_positions_value_dollars', 'Total positions value')
        
        # Risk metrics
        self.risk_score = Gauge('trading_risk_score', 'Current risk score (0-100)')
        self.max_drawdown = Gauge('trading_max_drawdown_percent', 'Maximum drawdown percentage')
        self.sharpe_ratio = Gauge('trading_sharpe_ratio', 'Current Sharpe ratio')
        
        # System metrics
        self.heartbeat_lag = Gauge('system_heartbeat_lag_seconds', 'Heartbeat lag in seconds', ['component'])
        self.api_requests = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
        self.websocket_messages = Counter('websocket_messages_total', 'Total WebSocket messages', ['type'])
        
        # Market data metrics
        self.market_data_lag = Gauge('market_data_lag_ms', 'Market data lag in milliseconds', ['symbol'])
        self.bars_processed = Counter('market_bars_processed_total', 'Total market bars processed', ['symbol'])
        
    async def record_order(self, order: Dict, strategy: str):
        """Record order metrics"""
        self.orders_placed.labels(
            strategy=strategy,
            symbol=order.get('symbol'),
            side=order.get('side')
        ).inc()
        
        # Log structured event
        self.logger.info(
            "order_placed",
            order_id=order.get('id'),
            symbol=order.get('symbol'),
            side=order.get('side'),
            qty=order.get('qty'),
            strategy=strategy,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store in Redis for analysis
        await self.redis.lpush(
            f"orders:{datetime.utcnow().strftime('%Y%m%d')}",
            json.dumps(order)
        )
        await self.redis.expire(f"orders:{datetime.utcnow().strftime('%Y%m%d')}", 86400 * 7)  # 7 days
        
    async def record_fill(self, fill: Dict, strategy: str, latency_ms: float):
        """Record order fill metrics"""
        self.orders_filled.labels(
            strategy=strategy,
            symbol=fill.get('symbol'),
            side=fill.get('side')
        ).inc()
        
        self.fill_latency.labels(strategy=strategy).observe(latency_ms)
        
        self.logger.info(
            "order_filled",
            order_id=fill.get('order_id'),
            symbol=fill.get('symbol'),
            price=fill.get('price'),
            qty=fill.get('qty'),
            latency_ms=latency_ms,
            strategy=strategy
        )
        
    async def record_rejection(self, order: Dict, reason: str, strategy: str):
        """Record order rejection"""
        self.orders_rejected.labels(strategy=strategy, reason=reason).inc()
        
        self.logger.warning(
            "order_rejected",
            order=order,
            reason=reason,
            strategy=strategy
        )
        
        # Check rejection rate
        await self.check_rejection_rate(strategy)
        
    async def update_pnl(self, daily_pnl: float, total_pnl: float):
        """Update P&L metrics"""
        self.daily_pnl.set(daily_pnl)
        self.total_pnl.set(total_pnl)
        
        # Check for alerts
        if daily_pnl <= -self.thresholds["daily_loss_limit"]:
            await self.create_alert(
                severity=AlertSeverity.CRITICAL,
                source="risk_manager",
                title="Daily Loss Limit Breached",
                message=f"Daily P&L: ${daily_pnl:.2f} exceeds limit of ${self.thresholds['daily_loss_limit']}"
            )
        
    async def check_heartbeat(self, component: str, last_heartbeat: datetime):
        """Check component heartbeat"""
        lag = (datetime.utcnow() - last_heartbeat).total_seconds()
        self.heartbeat_lag.labels(component=component).set(lag)
        
        if lag > self.thresholds["heartbeat_timeout"]:
            await self.create_alert(
                severity=AlertSeverity.ERROR,
                source="monitor",
                title=f"{component} Heartbeat Lost",
                message=f"No heartbeat from {component} for {lag:.0f} seconds"
            )
            return False
        return True
    
    async def check_rejection_rate(self, strategy: str):
        """Check if rejection rate is too high"""
        # Get recent orders from Redis
        orders_key = f"orders:{datetime.utcnow().strftime('%Y%m%d')}"
        recent_orders = await self.redis.lrange(orders_key, 0, 99)  # Last 100
        
        if len(recent_orders) < 10:
            return
        
        rejected_count = sum(1 for o in recent_orders if json.loads(o).get('status') == 'rejected')
        rejection_rate = rejected_count / len(recent_orders)
        
        if rejection_rate > self.thresholds["order_reject_rate"]:
            await self.create_alert(
                severity=AlertSeverity.WARNING,
                source="monitor",
                title="High Order Rejection Rate",
                message=f"Strategy {strategy} rejection rate: {rejection_rate:.1%}",
                metadata={"strategy": strategy, "rate": rejection_rate}
            )
    
    async def create_alert(self, severity: AlertSeverity, source: str, title: str, 
                          message: str, metadata: Dict = None):
        """Create and dispatch an alert"""
        alert = Alert(
            id=f"{source}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
            severity=severity,
            source=source,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Store in Redis
        await self.redis.lpush("alerts:active", json.dumps(alert.to_dict()))
        await self.redis.expire("alerts:active", 86400)  # 24 hours
        
        # Log the alert
        log_method = {
            AlertSeverity.INFO: self.logger.info,
            AlertSeverity.WARNING: self.logger.warning,
            AlertSeverity.ERROR: self.logger.error,
            AlertSeverity.CRITICAL: self.logger.critical
        }.get(severity, self.logger.info)
        
        log_method(
            "alert_created",
            alert_id=alert.id,
            severity=severity.value,
            source=source,
            title=title,
            message=message,
            metadata=metadata
        )
        
        # Dispatch to handlers
        for handler in self.alert_handlers:
            asyncio.create_task(handler(alert))
        
        return alert
    
    async def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                self.logger.info(
                    "alert_resolved",
                    alert_id=alert_id,
                    resolved_at=alert.resolved_at.isoformat()
                )
                
                # Update in Redis
                await self.redis.lrem("alerts:active", 0, json.dumps(alert.to_dict()))
                await self.redis.lpush("alerts:resolved", json.dumps(alert.to_dict()))
                
                return True
        return False
    
    def add_alert_handler(self, handler):
        """Add a custom alert handler"""
        self.alert_handlers.append(handler)
    
    async def get_metrics_snapshot(self) -> Dict:
        """Get current metrics snapshot"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "pnl": {
                "daily": self.daily_pnl._value.get(),
                "total": self.total_pnl._value.get()
            },
            "risk": {
                "score": self.risk_score._value.get(),
                "max_drawdown": self.max_drawdown._value.get()
            },
            "orders": {
                "placed": sum(self.orders_placed._metrics.values()),
                "filled": sum(self.orders_filled._metrics.values()),
                "rejected": sum(self.orders_rejected._metrics.values())
            },
            "alerts": {
                "active": len([a for a in self.alerts if not a.resolved]),
                "total": len(self.alerts)
            }
        }
    
    def get_prometheus_metrics(self) -> bytes:
        """Get Prometheus metrics in exposition format"""
        return generate_latest()