import redis.asyncio as redis
from fastapi import Depends
from typing import AsyncGenerator

from ..dao.database import DatabasePool, TradingDAO
from ..config import APIConfig

db_pool = DatabasePool()
redis_pool = None

async def get_database() -> DatabasePool:
    return db_pool

async def get_dao() -> TradingDAO:
    return TradingDAO(db_pool)

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    global redis_pool
    if not redis_pool:
        config = APIConfig()
        redis_pool = await redis.from_url(config.redis_url)
    try:
        yield redis_pool
    finally:
        pass  # Keep connection alive