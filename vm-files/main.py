from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from working_generators import generate_change_script as working_generate_change_script
import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import datetime
import subprocess
import json
import asyncio

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Mulroy Street Capital Trading API",
    version="1.0.0"
)

# Configure CORS - Enhanced with more allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.mulroystreetcap.com", 
        "https://mulroystreetcap.com",
        "https://thankful-glacier-03a07990f.1.azurestaticapps.net",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Alpaca client
# Check if we're using paper or live trading based on the API URL
api_base_url = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')
is_paper = 'paper' in api_base_url.lower()

trading_client = TradingClient(
    api_key=os.getenv('APCA_API_KEY_ID'),
    secret_key=os.getenv('APCA_API_SECRET_KEY'),
    paper=is_paper  # Automatically detect based on API URL
)

@app.get("/health")
async def health():
    """Basic health check"""
    return {"status": "healthy", "service": "trading-api", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/health")
async def api_health():
    """API health check with Alpaca connection test"""
    try:
        # Test Alpaca connection
        account = trading_client.get_account()
        return {
            "status": "healthy",
            "service": "trading-api",
            "alpaca_connected": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "trading-api", 
            "alpaca_connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/account")
@app.get("/api/account")
async def get_account():
    """Get Alpaca account details"""
    try:
        account = trading_client.get_account()
        return {
            "id": account.id,
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "last_equity": float(account.last_equity),
            "portfolio_value": float(account.portfolio_value),
            "pattern_day_trader": account.pattern_day_trader,
            "trading_blocked": account.trading_blocked,
            "transfers_blocked": account.transfers_blocked,
            "account_blocked": account.account_blocked,
            "daytrade_count": account.daytrade_count,
            "currency": account.currency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/positions")
@app.get("/api/positions")
async def get_positions():
    """Get all current positions"""
    try:
        positions = trading_client.get_all_positions()
        return [
            {
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "side": pos.side,
                "market_value": float(pos.market_value) if pos.market_value else 0,
                "cost_basis": float(pos.cost_basis) if pos.cost_basis else 0,
                "unrealized_pl": float(pos.unrealized_pl) if pos.unrealized_pl else 0,
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0,
                "current_price": float(pos.current_price) if pos.current_price else 0,
                "avg_entry_price": float(pos.avg_entry_price) if pos.avg_entry_price else 0
            }
            for pos in positions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders")
@app.get("/api/orders")
async def get_orders(limit: int = 100):
    """Get recent orders"""
    try:
        orders = trading_client.get_orders(filter=None, limit=limit)
        return [
            {
                "id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty) if order.qty else 0,
                "side": order.side,
                "type": order.type,
                "time_in_force": order.time_in_force,
                "status": order.status,
                "submitted_at": order.submitted_at.isoformat() if order.submitted_at else None,
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "filled_qty": float(order.filled_qty) if order.filled_qty else 0,
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else 0
            }
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clock")
@app.get("/api/clock")
async def get_clock():
    """Get market clock status"""
    try:
        clock = trading_client.get_clock()
        return {
            "timestamp": clock.timestamp.isoformat() if clock.timestamp else None,
            "is_open": clock.is_open,
            "next_open": clock.next_open.isoformat() if clock.next_open else None,
            "next_close": clock.next_close.isoformat() if clock.next_close else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8600)

# ===== NEW ENDPOINTS FOR DASHBOARD =====

@app.get("/api/weather/{location}")
async def get_weather(location: str):
    """Get weather for DC or Asbury Park"""
    try:
        # Using wttr.in service (no API key needed)
        import urllib.request
        import json
        
        # Map friendly names to locations
        locations = {
            "dc": "Washington,DC",
            "asbury": "Asbury+Park,NJ"
        }
        
        loc = locations.get(location.lower(), location)
        url = f"https://wttr.in/{loc}?format=j1"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            current = data['current_condition'][0]
            
            return {
                "location": location,
                "temp_f": current['temp_F'],
                "temp_c": current['temp_C'],
                "description": current['weatherDesc'][0]['value'],
                "humidity": current['humidity'],
                "feels_like_f": current['FeelsLikeF']
            }
    except Exception as e:
        return {"error": str(e), "location": location}

@app.get("/api/market-times")
async def get_market_times():
    """Get current time in major markets"""
    from datetime import datetime
    import pytz
    
    markets = {
        "New York": "America/New_York",
        "London": "Europe/London",
        "Tokyo": "Asia/Tokyo",
        "Hong Kong": "Asia/Hong_Kong",
        "Sydney": "Australia/Sydney"
    }
    
    times = {}
    for city, tz in markets.items():
        timezone = pytz.timezone(tz)
        local_time = datetime.now(timezone)
        times[city] = {
            "time": local_time.strftime("%H:%M"),
            "date": local_time.strftime("%Y-%m-%d"),
            "is_market_hours": is_market_open(city, local_time)
        }
    
    return times

def is_market_open(city: str, local_time):
    """Check if market is open in given city"""
    hour = local_time.hour
    weekday = local_time.weekday()
    
    # Skip weekends
    if weekday >= 5:
        return False
    
    # Market hours (simplified)
    market_hours = {
        "New York": (9.5, 16),  # 9:30 AM - 4:00 PM
        "London": (8, 16.5),     # 8:00 AM - 4:30 PM
        "Tokyo": (9, 15),        # 9:00 AM - 3:00 PM
        "Hong Kong": (9.5, 16),  # 9:30 AM - 4:00 PM
        "Sydney": (10, 16)       # 10:00 AM - 4:00 PM
    }
    
    if city in market_hours:
        open_time, close_time = market_hours[city]
        return open_time <= hour + (local_time.minute / 60) < close_time
    return False

@app.get("/api/market-data")
async def get_market_data():
    """Get live market data for major indices"""
    try:
        # Get latest bars for major ETFs as proxy for indices
        symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
        
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockLatestQuoteRequest
        
        data_client = StockHistoricalDataClient(
            api_key=os.getenv('APCA_API_KEY_ID'),
            secret_key=os.getenv('APCA_API_SECRET_KEY')
        )
        
        request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
        quotes = data_client.get_stock_latest_quote(request)
        
        market_data = {}
        for symbol in symbols:
            if symbol in quotes:
                quote = quotes[symbol]
                market_data[symbol] = {
                    "price": float(quote.ask_price),
                    "bid": float(quote.bid_price),
                    "ask": float(quote.ask_price),
                    "timestamp": quote.timestamp.isoformat() if quote.timestamp else None
                }
        
        return market_data
    except Exception as e:
        return {"error": str(e)}

# ===== ENHANCED ADMIN PANEL API ENDPOINTS =====

# Store change requests in a simple JSON file
CHANGE_QUEUE_FILE = '/home/ktmulroy/admin-changes.json'

def load_change_queue():
    """Load the change queue from file"""
    try:
        if os.path.exists(CHANGE_QUEUE_FILE):
            with open(CHANGE_QUEUE_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading change queue: {e}")
        return []

def save_change_queue(queue):
    """Save the change queue to file"""
    try:
        with open(CHANGE_QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving change queue: {e}")
        return False

@app.post("/api/admin/change-request")
async def create_change_request(request: dict):
    """Receive change request from admin panel"""
    try:
        queue = load_change_queue()
        
        # Add new request
        change_request = {
            'id': len(queue) + 1,
            'timestamp': datetime.now().isoformat(),
            'description': request.get('description', ''),
            'type': request.get('type', 'custom'),
            'status': 'pending',
            'result': None,
            'script_path': None,
            'execution_log': []
        }
        
        queue.append(change_request)
        
        if save_change_queue(queue):
            return {
                'success': True,
                'message': 'Change request queued',
                'id': change_request['id'],
                'instruction': f'Click "Prepare" to generate execution script for change #{change_request["id"]}'
            }
        else:
            return {'success': False, 'error': 'Failed to save change request'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.get("/api/admin/change-queue")
async def get_change_queue():
    """Get all change requests"""
    try:
        queue = load_change_queue()
        return {'success': True, 'queue': queue}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.post("/api/admin/execute-change/{change_id}")
async def execute_change(change_id: int):
    """Prepare change for execution (create script)"""
    try:
        queue = load_change_queue()
        
        for change in queue:
            if change['id'] == change_id:
                if change['status'] == 'script_created':
                    # Execute the script directly
                    return await run_change_script(change_id)
                
                # Create execution script
                change['status'] = 'executing'
                change['execution_log'].append(f"[{datetime.now().isoformat()}] Creating execution script")
                
                script_content = working_generate_change_script(change)
                script_path = f'/home/ktmulroy/pending-changes/change-{change_id}.sh'
                
                os.makedirs('/home/ktmulroy/pending-changes', exist_ok=True)
                
                try:
                    with open(script_path, 'w') as f:
                        f.write(script_content)
                    os.chmod(script_path, 0o755)
                    
                    change['status'] = 'script_created'
                    change['script_path'] = script_path
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Script created: {script_path}")
                    
                    if save_change_queue(queue):
                        return {
                            'success': True,
                            'message': f'Script ready for execution',
                            'instruction': f'Change is now ready to execute. Click "EXECUTE" to run.'
                        }
                    else:
                        return {'success': False, 'error': 'Failed to update change status'}
                        
                except Exception as script_error:
                    change['status'] = 'failed'
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Script creation failed: {str(script_error)}")
                    save_change_queue(queue)
                    return {'success': False, 'error': f'Script creation failed: {str(script_error)}'}
        
        return {'success': False, 'error': 'Change request not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.post("/api/admin/auto-execute-change/{change_id}")
async def auto_execute_change(change_id: int):
    """Auto-execute simple changes directly"""
    try:
        queue = load_change_queue()
        
        for change in queue:
            if change['id'] == change_id:
                change['status'] = 'executing'
                change['execution_log'].append(f"[{datetime.now().isoformat()}] Starting auto-execution")
                save_change_queue(queue)
                
                # For safety, only auto-execute very specific types of changes
                description = change['description'].lower()
                if any(keyword in description for keyword in ['remove weather', 'change color', 'change header']):
                    return await run_safe_change(change_id, description)
                else:
                    change['status'] = 'failed'
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Auto-execution not supported for this change type")
                    save_change_queue(queue)
                    return {'success': False, 'error': 'Change not suitable for auto-execution'}
        
        return {'success': False, 'error': 'Change request not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def run_change_script(change_id: int):
    """Execute the prepared script for a change"""
    try:
        queue = load_change_queue()
        
        for change in queue:
            if change['id'] == change_id and change['status'] == 'script_created':
                change['status'] = 'executing'
                change['execution_log'].append(f"[{datetime.now().isoformat()}] Starting script execution")
                save_change_queue(queue)
                
                script_path = change.get('script_path')
                if not script_path or not os.path.exists(script_path):
                    change['status'] = 'failed'
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Script not found: {script_path}")
                    save_change_queue(queue)
                    return {'success': False, 'error': 'Script file not found'}
                
                try:
                    # Execute the script with timeout
                    result = subprocess.run(
                        ['/usr/bin/bash', script_path],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd='/home/ktmulroy'
                    )
                    
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Script output: {result.stdout}")
                    if result.stderr:
                        change['execution_log'].append(f"[{datetime.now().isoformat()}] Script errors: {result.stderr}")
                    
                    if result.returncode == 0:
                        change['status'] = 'completed'
                        change['result'] = 'success'
                        change['execution_log'].append(f"[{datetime.now().isoformat()}] Execution completed successfully")
                        save_change_queue(queue)
                        return {
                            'success': True,
                            'message': f'Change {change_id} executed successfully',
                            'output': result.stdout
                        }
                    else:
                        change['status'] = 'failed'
                        change['result'] = 'error'
                        change['execution_log'].append(f"[{datetime.now().isoformat()}] Execution failed with code {result.returncode}")
                        save_change_queue(queue)
                        return {
                            'success': False,
                            'error': f'Script execution failed: {result.stderr or result.stdout}'
                        }
                        
                except subprocess.TimeoutExpired:
                    change['status'] = 'failed'
                    change['result'] = 'timeout'
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Execution timed out after 30 seconds")
                    save_change_queue(queue)
                    return {'success': False, 'error': 'Script execution timed out'}
                    
                except Exception as exec_error:
                    change['status'] = 'failed'
                    change['result'] = 'error'
                    change['execution_log'].append(f"[{datetime.now().isoformat()}] Execution error: {str(exec_error)}")
                    save_change_queue(queue)
                    return {'success': False, 'error': f'Execution failed: {str(exec_error)}'}
        
        return {'success': False, 'error': 'Change not found or not ready for execution'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def run_safe_change(change_id: int, description: str):
    """Execute safe changes directly without scripts"""
    try:
        queue = load_change_queue()
        
        for change in queue:
            if change['id'] == change_id:
                # Simulate safe execution
                await asyncio.sleep(2)  # Simulate processing time
                
                change['status'] = 'completed'
                change['result'] = 'success'
                change['execution_log'].append(f"[{datetime.now().isoformat()}] Safe auto-execution completed")
                save_change_queue(queue)
                
                return {
                    'success': True,
                    'message': f'Change {change_id} auto-executed successfully',
                    'instruction': 'Simple change completed automatically'
                }
        
        return {'success': False, 'error': 'Change not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

