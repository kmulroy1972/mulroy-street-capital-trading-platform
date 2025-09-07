#!/usr/bin/env python3
"""
Health check script for Docker containers
"""

import sys
import asyncio
import os
from datetime import datetime, timedelta

import redis.asyncio as redis

async def check_engine_health():
    """Check if the trading engine is healthy"""
    try:
        # Connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        r = await redis.from_url(redis_url)
        
        # Check for recent heartbeat
        engine_id = os.getenv('ENGINE_ID', 'engine-live-001')
        heartbeat = await r.get(f"engine:{engine_id}:heartbeat")
        
        if heartbeat:
            last_heartbeat = datetime.fromisoformat(heartbeat.decode())
            if (datetime.utcnow() - last_heartbeat).seconds < 120:  # 2 minutes
                print("✅ Engine healthy")
                await r.close()
                return True
        
        print("❌ Engine heartbeat missing or stale")
        await r.close()
        return False
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_engine_health())
    sys.exit(0 if result else 1)