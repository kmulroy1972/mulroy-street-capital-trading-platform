# Alpaca Trading API

## Overview

REST API for the Alpaca trading platform providing read-only public endpoints and secured admin endpoints for controlling the trading engine.

## Authentication

### Public Endpoints
No authentication required for read-only data access.

### Admin Endpoints
JWT token required. Get token with basic auth:

```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -u "admin:password" \
  -H "Content-Type: application/json"
```

Use token in Authorization header:
```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/api/strategies"
```

## Public Endpoints (No Auth Required)

### GET /api/health
Returns system health status including engine heartbeat

**Response:**
```json
{
  "status": "healthy",
  "engine_status": "running",
  "last_heartbeat": "2023-12-01T10:30:00",
  "version": "1.0.0"
}
```

### GET /api/account
Returns current account information

**Response:**
```json
{
  "equity": 50000.00,
  "cash": 25000.00,
  "buying_power": 100000.00,
  "positions_count": 5,
  "daily_pnl": 150.25,
  "total_pnl": 2500.00
}
```

### GET /api/positions
Returns all current positions

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "qty": 100,
    "avg_entry_price": 150.00,
    "current_price": 152.50,
    "market_value": 15250.00,
    "unrealized_pnl": 250.00,
    "unrealized_pnl_pct": 1.67
  }
]
```

### GET /api/orders?status={open|filled|cancelled}
Returns orders with optional status filter

**Parameters:**
- `status` (optional): Filter by order status

### GET /api/pnl?window={1d|1w|1m|ytd|all}
Returns P&L metrics for specified time window

**Parameters:**
- `window`: Time window for P&L calculation

## Admin Endpoints (JWT Required)

### POST /api/auth/token
Get JWT token with basic auth credentials

### GET /api/strategies
List all strategies and their current status

**Response:**
```json
[
  {
    "name": "momentum_strategy",
    "version": "1.0.0",
    "status": "enabled",
    "last_signal": "2023-12-01T10:25:00",
    "positions_count": 3,
    "daily_pnl": 75.50
  }
]
```

### PUT /api/strategies/{name}/toggle
Change strategy execution mode

**Body:**
```json
"enabled"
```

**Valid statuses:** disabled, shadow, canary, enabled

### GET /api/config
Get current trading configuration

### PUT /api/config
Update trading configuration with validation

**Body:**
```json
{
  "daily_loss_limit": 1500.0,
  "max_position_size": 15000.0,
  "strategies_enabled": ["momentum_strategy"],
  "trading_enabled": true
}
```

### POST /api/controls/flatten_all
Emergency: close all positions immediately

### POST /api/controls/trading_enabled
Enable/disable all trading (kill switch)

**Body:**
```json
true
```

## Error Handling

Standard HTTP status codes:
- 200: Success
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid/missing token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found
- 500: Internal Server Error

## Interactive Documentation

Visit `/docs` for Swagger UI with interactive API testing.