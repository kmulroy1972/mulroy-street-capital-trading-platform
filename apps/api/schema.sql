-- Create tables for the trading journal
CREATE TABLE IF NOT EXISTS account_snapshots (
    id SERIAL PRIMARY KEY,
    equity DECIMAL(15,2),
    cash DECIMAL(15,2),
    buying_power DECIMAL(15,2),
    positions_count INT,
    daily_pnl DECIMAL(15,2),
    total_pnl DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS positions (
    symbol VARCHAR(10) PRIMARY KEY,
    qty DECIMAL(15,4),
    avg_entry_price DECIMAL(15,4),
    current_price DECIMAL(15,4),
    market_value DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    unrealized_pnl_pct DECIMAL(8,4),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(50) PRIMARY KEY,
    symbol VARCHAR(10),
    side VARCHAR(10),
    order_type VARCHAR(20),
    qty DECIMAL(15,4),
    filled_qty DECIMAL(15,4),
    status VARCHAR(20),
    limit_price DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50),
    symbol VARCHAR(10),
    side VARCHAR(10),
    qty DECIMAL(15,4),
    price DECIMAL(15,4),
    realized_pnl DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS config_revisions (
    id SERIAL PRIMARY KEY,
    config_json JSONB,
    created_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alpaca-specific tables
CREATE TABLE IF NOT EXISTS alpaca_orders (
    id VARCHAR(50) PRIMARY KEY,
    client_order_id VARCHAR(100) UNIQUE,
    symbol VARCHAR(10),
    side VARCHAR(10),
    order_type VARCHAR(20),
    qty DECIMAL(15,4),
    filled_qty DECIMAL(15,4) DEFAULT 0,
    status VARCHAR(20),
    limit_price DECIMAL(15,4),
    stop_price DECIMAL(15,4),
    filled_avg_price DECIMAL(15,4),
    time_in_force VARCHAR(10),
    submitted_at TIMESTAMP,
    filled_at TIMESTAMP,
    canceled_at TIMESTAMP,
    expired_at TIMESTAMP,
    asset_class VARCHAR(20) DEFAULT 'us_equity',
    legs JSONB,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alpaca_positions (
    symbol VARCHAR(10) PRIMARY KEY,
    asset_id VARCHAR(50),
    qty DECIMAL(15,4),
    avg_entry_price DECIMAL(15,4),
    side VARCHAR(10),
    market_value DECIMAL(15,2),
    cost_basis DECIMAL(15,2),
    unrealized_pl DECIMAL(15,2),
    unrealized_plpc DECIMAL(8,4),
    unrealized_intraday_pl DECIMAL(15,2),
    unrealized_intraday_plpc DECIMAL(8,4),
    current_price DECIMAL(15,4),
    lastday_price DECIMAL(15,4),
    change_today DECIMAL(8,4),
    exchange VARCHAR(20),
    asset_class VARCHAR(20) DEFAULT 'us_equity',
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alpaca_account_snapshots (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(50),
    status VARCHAR(20),
    currency VARCHAR(10),
    buying_power DECIMAL(15,2),
    regt_buying_power DECIMAL(15,2),
    daytrading_buying_power DECIMAL(15,2),
    non_marginable_buying_power DECIMAL(15,2),
    cash DECIMAL(15,2),
    accrued_fees DECIMAL(15,2),
    pending_transfer_in DECIMAL(15,2),
    pending_transfer_out DECIMAL(15,2),
    portfolio_value DECIMAL(15,2),
    pattern_day_trader BOOLEAN,
    trading_blocked BOOLEAN,
    transfers_blocked BOOLEAN,
    account_blocked BOOLEAN,
    created_account_at TIMESTAMP,
    trade_suspended_by_user BOOLEAN,
    multiplier DECIMAL(8,2),
    shorting_enabled BOOLEAN,
    equity DECIMAL(15,2),
    last_equity DECIMAL(15,2),
    long_market_value DECIMAL(15,2),
    short_market_value DECIMAL(15,2),
    initial_margin DECIMAL(15,2),
    maintenance_margin DECIMAL(15,2),
    sma DECIMAL(15,2),
    daytrade_count INT,
    balance_asof VARCHAR(20),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS market_bars (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    timeframe VARCHAR(10),
    timestamp BIGINT,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    close_price DECIMAL(15,4),
    volume DECIMAL(15,0),
    trade_count INT,
    vwap DECIMAL(15,4),
    source VARCHAR(20) DEFAULT 'alpaca',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timeframe, timestamp)
);

CREATE TABLE IF NOT EXISTS market_trades (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    timestamp BIGINT,
    price DECIMAL(15,4),
    size DECIMAL(15,4),
    conditions TEXT[],
    exchange VARCHAR(10),
    tape VARCHAR(10),
    source VARCHAR(20) DEFAULT 'alpaca',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_signals (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100),
    symbol VARCHAR(10),
    action VARCHAR(10),
    qty DECIMAL(15,4),
    price DECIMAL(15,4),
    confidence DECIMAL(4,2),
    execution_mode VARCHAR(20),
    order_id VARCHAR(50),
    executed BOOLEAN DEFAULT FALSE,
    reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trades_created ON trades(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_account_snapshots_created ON account_snapshots(created_at DESC);

-- Alpaca-specific indexes
CREATE INDEX IF NOT EXISTS idx_alpaca_orders_status ON alpaca_orders(status);
CREATE INDEX IF NOT EXISTS idx_alpaca_orders_symbol ON alpaca_orders(symbol);
CREATE INDEX IF NOT EXISTS idx_alpaca_orders_submitted ON alpaca_orders(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_alpaca_positions_symbol ON alpaca_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_timeframe ON market_bars(symbol, timeframe);
CREATE INDEX IF NOT EXISTS idx_market_bars_timestamp ON market_bars(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_trades_symbol ON market_trades(symbol);
CREATE INDEX IF NOT EXISTS idx_market_trades_timestamp ON market_trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_strategy ON strategy_signals(strategy_name);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_created ON strategy_signals(created_at DESC);

-- Live trading specific tables
CREATE TABLE IF NOT EXISTS live_trading_sessions (
    id SERIAL PRIMARY KEY,
    engine_id VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    initial_equity DECIMAL(15,2),
    final_equity DECIMAL(15,2),
    total_trades INT DEFAULT 0,
    profitable_trades INT DEFAULT 0,
    max_drawdown DECIMAL(15,2),
    confirmation_received BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS emergency_stops (
    id SERIAL PRIMARY KEY,
    engine_id VARCHAR(50),
    trigger_reason VARCHAR(200),
    positions_closed INT DEFAULT 0,
    orders_cancelled INT DEFAULT 0,
    equity_at_stop DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_mode_changes (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(100),
    old_mode VARCHAR(20),
    new_mode VARCHAR(20),
    changed_by VARCHAR(50),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for live trading tables
CREATE INDEX IF NOT EXISTS idx_live_sessions_engine ON live_trading_sessions(engine_id);
CREATE INDEX IF NOT EXISTS idx_emergency_stops_engine ON emergency_stops(engine_id);
CREATE INDEX IF NOT EXISTS idx_strategy_mode_changes_strategy ON strategy_mode_changes(strategy_name);