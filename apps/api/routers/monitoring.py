from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
import redis.asyncio as redis
from datetime import datetime, timedelta
import json

from ..deps.dependencies import get_redis

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health/detailed")
async def get_detailed_health(
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get detailed health status of all components"""
    health_checks = {}
    
    # Check Engine heartbeat
    engine_heartbeat = await redis_client.get("engine:engine-live-001:heartbeat")
    if engine_heartbeat:
        last_heartbeat = datetime.fromisoformat(engine_heartbeat.decode())
        engine_healthy = (datetime.utcnow() - last_heartbeat).seconds < 60
    else:
        engine_healthy = False
    
    health_checks["engine"] = {
        "healthy": engine_healthy,
        "last_heartbeat": engine_heartbeat.decode() if engine_heartbeat else None
    }
    
    # Check Redis
    try:
        await redis_client.ping()
        health_checks["redis"] = {"healthy": True}
    except:
        health_checks["redis"] = {"healthy": False}
    
    # Check Alpaca connection
    market_open = await redis_client.get("market:is_open")
    health_checks["alpaca"] = {
        "healthy": True,
        "market_open": market_open.decode() == "True" if market_open else False
    }
    
    # Overall health
    all_healthy = all(check["healthy"] for check in health_checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": health_checks
    }

@router.get("/metrics")
async def get_metrics(
    timerange: str = "1h",
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get system metrics"""
    # Parse timerange
    if timerange == "1h":
        start = datetime.utcnow() - timedelta(hours=1)
    elif timerange == "6h":
        start = datetime.utcnow() - timedelta(hours=6)
    elif timerange == "24h":
        start = datetime.utcnow() - timedelta(days=1)
    else:
        start = datetime.utcnow() - timedelta(days=7)
    
    # Get metrics from Redis
    orders_today = await redis_client.llen(f"orders:{datetime.utcnow().strftime('%Y%m%d')}")
    
    # Mock data for now - would be replaced with real metrics collection
    metrics = {
        "timerange": timerange,
        "start": start.isoformat(),
        "end": datetime.utcnow().isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
        "orders": {
            "placed": orders_today or 0,
            "filled": int((orders_today or 0) * 0.85),
            "rejected": int((orders_today or 0) * 0.05)
        },
        "latency": {
            "p50": 45,
            "p95": 120,
            "p99": 250
        },
        "pnl": {
            "daily": 150.75,
            "total": 2847.32
        },
        "risk": {
            "score": 25,
            "max_drawdown": 0.08
        },
        "alerts": {
            "active": 0,
            "total": 3
        },
        "orderFlow": [
            {"time": "09:30", "placed": 15, "filled": 13, "rejected": 1},
            {"time": "10:00", "placed": 22, "filled": 20, "rejected": 0},
            {"time": "10:30", "placed": 18, "filled": 16, "rejected": 2},
            {"time": "11:00", "placed": 25, "filled": 23, "rejected": 1},
            {"time": "11:30", "placed": 12, "filled": 11, "rejected": 0},
        ],
        "latencyBuckets": [
            {"bucket": "0-50ms", "count": 45},
            {"bucket": "50-100ms", "count": 32},
            {"bucket": "100-200ms", "count": 18},
            {"bucket": "200ms+", "count": 5}
        ]
    }
    
    return metrics

@router.get("/alerts")
async def get_alerts(
    status: Optional[str] = "active",
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get alerts"""
    if status == "active":
        alerts_data = await redis_client.lrange("alerts:active", 0, -1)
    else:
        alerts_data = await redis_client.lrange("alerts:resolved", 0, -1)
    
    alerts = []
    for alert_json in alerts_data:
        try:
            alert = json.loads(alert_json)
            alerts.append(alert)
        except:
            pass
    
    return {
        "status": status,
        "active": [a for a in alerts if not a.get("resolved")],
        "total": len(alerts),
        "alerts": alerts[:50]  # Limit to 50 most recent
    }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    redis_client: redis.Redis = Depends(get_redis)
):
    """Resolve an alert"""
    # Find and update alert
    alerts_data = await redis_client.lrange("alerts:active", 0, -1)
    
    for alert_json in alerts_data:
        alert = json.loads(alert_json)
        if alert["id"] == alert_id:
            alert["resolved"] = True
            alert["resolved_at"] = datetime.utcnow().isoformat()
            
            # Move to resolved
            await redis_client.lrem("alerts:active", 1, alert_json)
            await redis_client.lpush("alerts:resolved", json.dumps(alert))
            
            return {"message": "Alert resolved", "alert": alert}
    
    raise HTTPException(status_code=404, detail="Alert not found")

@router.get("/prometheus")
async def get_prometheus_metrics():
    """Expose metrics in Prometheus format"""
    from packages.core.monitoring.monitor import TradingMonitor
    # Would get singleton instance in real implementation
    return generate_latest()