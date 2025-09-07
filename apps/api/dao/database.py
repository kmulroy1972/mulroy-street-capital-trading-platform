import asyncpg
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
from decimal import Decimal

class DatabasePool:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def init(self, database_url: str) -> None:
        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            
    async def execute_query(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
            
    async def execute_command(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

class TradingDAO:
    def __init__(self, db: DatabasePool):
        self.db = db
        
    async def get_latest_account_snapshot(self) -> Optional[Dict]:
        query = """
        SELECT equity, cash, buying_power, positions_count, daily_pnl, total_pnl, created_at
        FROM account_snapshots
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = await self.db.execute_query(query)
        return dict(result[0]) if result else None
        
    async def get_positions(self) -> List[Dict]:
        query = """
        SELECT symbol, qty, avg_entry_price, current_price, 
               market_value, unrealized_pnl, unrealized_pnl_pct
        FROM positions
        WHERE qty != 0
        ORDER BY ABS(market_value) DESC
        """
        results = await self.db.execute_query(query)
        return [dict(r) for r in results]
        
    async def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        query = """
        SELECT id, symbol, side, order_type, qty, filled_qty, 
               status, created_at, filled_at, limit_price
        FROM orders
        WHERE ($1::text IS NULL OR status = $1)
        ORDER BY created_at DESC
        LIMIT 100
        """
        results = await self.db.execute_query(query, status)
        return [dict(r) for r in results]
        
    async def get_pnl(self, window: str) -> Optional[Dict]:
        # Calculate date range based on window
        now = datetime.utcnow()
        if window == "1d":
            start_date = now - timedelta(days=1)
        elif window == "1w":
            start_date = now - timedelta(weeks=1)
        elif window == "1m":
            start_date = now - timedelta(days=30)
        elif window == "ytd":
            start_date = datetime(now.year, 1, 1)
        else:  # all
            start_date = datetime(2020, 1, 1)
            
        query = """
        SELECT 
            COALESCE(SUM(realized_pnl), 0) as realized_pnl,
            COALESCE(SUM(unrealized_pnl), 0) as unrealized_pnl,
            COUNT(*) as trades_count,
            COALESCE(AVG(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END), 0) as win_rate,
            0.0 as sharpe_ratio,
            0.0 as max_drawdown
        FROM trades
        WHERE created_at >= $1
        """
        result = await self.db.execute_query(query, start_date)
        if result:
            data = dict(result[0])
            data['total_pnl'] = data['realized_pnl'] + data['unrealized_pnl']
            return data
        return None
        
    async def save_config_revision(self, config: Dict, user: str) -> int:
        query = """
        INSERT INTO config_revisions (config_json, created_by, created_at)
        VALUES ($1, $2, $3)
        RETURNING id
        """
        result = await self.db.execute_query(
            query, 
            json.dumps(config), 
            user, 
            datetime.utcnow()
        )
        return result[0]['id']