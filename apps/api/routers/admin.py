from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
import redis.asyncio as redis
import json

from ..models import StrategyInfo, ConfigUpdate
from ..auth.jwt_auth import verify_admin
from ..deps.dependencies import get_dao, get_redis
from ..dao.database import TradingDAO

router = APIRouter(prefix="/api", tags=["admin"])

@router.get("/strategies", response_model=List[StrategyInfo], dependencies=[Depends(verify_admin)])
async def get_strategies(
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get all strategies and their current status"""
    # Get strategy info from Redis
    strategies = []
    strategy_keys = await redis_client.keys("strategy:*:status")
    
    for key in strategy_keys:
        strategy_name = key.decode().split(":")[1]
        status_bytes = await redis_client.get(key)
        status = status_bytes.decode() if status_bytes else "disabled"
        
        strategies.append(StrategyInfo(
            name=strategy_name,
            version="1.0.0",
            status=status,
            last_signal=None,
            positions_count=0,
            daily_pnl=0
        ))
    
    return strategies

@router.put("/strategies/{name}/toggle", dependencies=[Depends(verify_admin)])
async def toggle_strategy(
    name: str,
    status: str = Body(..., regex="^(disabled|shadow|canary|enabled)$"),
    redis_client: redis.Redis = Depends(get_redis),
    dao: TradingDAO = Depends(get_dao),
    current_user: str = Depends(verify_admin)
):
    """Change strategy execution mode"""
    # Update strategy status in Redis
    await redis_client.set(f"strategy:{name}:status", status)
    
    # Log the change
    config_change = {
        "action": "strategy_toggle",
        "strategy": name,
        "new_status": status
    }
    await dao.save_config_revision(config_change, current_user)
    
    # Notify engine via Redis pub/sub
    await redis_client.publish("engine:commands", json.dumps({
        "command": "strategy_update",
        "strategy": name,
        "status": status
    }))
    
    return {"message": f"Strategy {name} set to {status}"}

@router.get("/config", dependencies=[Depends(verify_admin)])
async def get_config(
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get current trading configuration"""
    config_bytes = await redis_client.get("engine:config")
    if not config_bytes:
        return {
            "daily_loss_limit": 1000.0,
            "max_position_size": 10000.0,
            "strategies_enabled": [],
            "trading_enabled": True
        }
    return json.loads(config_bytes.decode())

@router.put("/config", dependencies=[Depends(verify_admin)])
async def update_config(
    config: ConfigUpdate,
    redis_client: redis.Redis = Depends(get_redis),
    dao: TradingDAO = Depends(get_dao),
    current_user: str = Depends(verify_admin)
):
    """Update trading configuration with validation"""
    # Get current config
    current_bytes = await redis_client.get("engine:config")
    current_config = json.loads(current_bytes.decode()) if current_bytes else {}
    
    # Update with new values
    update_dict = config.dict(exclude_unset=True)
    current_config.update(update_dict)
    
    # Validate limits
    if current_config.get("daily_loss_limit", 0) < 100:
        raise HTTPException(status_code=400, detail="Daily loss limit too low")
    
    # Save to Redis
    await redis_client.set("engine:config", json.dumps(current_config))
    
    # Save revision history
    await dao.save_config_revision(current_config, current_user)
    
    # Notify engine
    await redis_client.publish("engine:commands", json.dumps({
        "command": "config_update",
        "config": current_config
    }))
    
    return {"message": "Configuration updated", "config": current_config}

@router.post("/controls/flatten_all", dependencies=[Depends(verify_admin)])
async def flatten_all_positions(
    redis_client: redis.Redis = Depends(get_redis),
    current_user: str = Depends(verify_admin)
):
    """Emergency: close all positions immediately"""
    await redis_client.publish("engine:commands", json.dumps({
        "command": "flatten_all",
        "user": current_user
    }))
    return {"message": "Flatten all command sent to engine"}

@router.post("/controls/trading_enabled", dependencies=[Depends(verify_admin)])
async def set_trading_enabled(
    enabled: bool = Body(...),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: str = Depends(verify_admin)
):
    """Enable or disable all trading (kill switch)"""
    await redis_client.set("engine:trading_enabled", str(enabled))
    await redis_client.publish("engine:commands", json.dumps({
        "command": "trading_enabled",
        "enabled": enabled,
        "user": current_user
    }))
    return {"message": f"Trading {'enabled' if enabled else 'disabled'}"}