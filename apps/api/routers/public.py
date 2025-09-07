from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
import redis.asyncio as redis
from datetime import datetime

from ..models import (
    HealthResponse, AccountResponse, PositionResponse, 
    OrderResponse, PnLResponse
)
from ..deps.dependencies import get_dao, get_redis
from ..dao.database import TradingDAO

router = APIRouter(prefix="/api", tags=["public"])

@router.get("/health", response_model=HealthResponse)
async def get_health(
    dao: TradingDAO = Depends(get_dao),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Check system health including engine heartbeat"""
    try:
        # Check engine heartbeat from Redis
        heartbeat = await redis_client.get("engine:engine-001:heartbeat")
        last_heartbeat = datetime.fromisoformat(heartbeat.decode()) if heartbeat else None
        
        # Determine health status
        if not heartbeat:
            status = "unhealthy"
            engine_status = "offline"
        elif (datetime.utcnow() - last_heartbeat).seconds > 60:
            status = "degraded"
            engine_status = "stale"
        else:
            status = "healthy"
            engine_status = "running"
            
        return HealthResponse(
            status=status,
            engine_status=engine_status,
            last_heartbeat=last_heartbeat,
            version="1.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            engine_status="error",
            last_heartbeat=None,
            version="1.0.0"
        )

@router.get("/account", response_model=AccountResponse)
async def get_account(dao: TradingDAO = Depends(get_dao)):
    """Get current account information"""
    account = await dao.get_latest_account_snapshot()
    if not account:
        raise HTTPException(status_code=404, detail="No account data available")
    return AccountResponse(**account)

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(dao: TradingDAO = Depends(get_dao)):
    """Get all current positions"""
    positions = await dao.get_positions()
    return [PositionResponse(**pos) for pos in positions]

@router.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = Query(None, regex="^(open|filled|cancelled)$"),
    dao: TradingDAO = Depends(get_dao)
):
    """Get orders with optional status filter"""
    orders = await dao.get_orders(status)
    return [OrderResponse(**order) for order in orders]

@router.get("/pnl", response_model=PnLResponse)
async def get_pnl(
    window: str = Query("1d", regex="^(1d|1w|1m|ytd|all)$"),
    dao: TradingDAO = Depends(get_dao)
):
    """Get P&L metrics for specified time window"""
    pnl_data = await dao.get_pnl(window)
    if not pnl_data:
        raise HTTPException(status_code=404, detail="No P&L data available")
    return PnLResponse(window=window, **pnl_data)