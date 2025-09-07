#!/usr/bin/env python3
"""
Setup monitoring and alerts for the trading system
"""

import yaml
import asyncio
import redis.asyncio as redis
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

async def setup_monitoring():
    """Setup monitoring configuration"""
    
    # Load config
    config_file = Path("config/monitoring.yaml")
    if not config_file.exists():
        print("Creating default monitoring config...")
        config_file.parent.mkdir(exist_ok=True)
        config_file.write_text(DEFAULT_CONFIG)
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # Connect to Redis
    try:
        r = await redis.from_url("redis://localhost:6379")
        await r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        print("Make sure Redis is running: brew services start redis")
        return
    
    # Store config in Redis
    await r.set("monitoring:config", yaml.dump(config))
    print("✅ Monitoring configuration loaded")
    
    # Test Discord webhook if enabled
    if config['monitoring']['alerts']['discord']['enabled']:
        print("Testing Discord webhook...")
        try:
            from packages.core.monitoring.notifier import WebhookChannel, Alert, AlertSeverity
            
            webhook = WebhookChannel(
                config['monitoring']['alerts']['discord']['webhook_url'],
                "discord"
            )
            
            test_alert = Alert(
                id="test_001",
                severity=AlertSeverity.INFO,
                source="setup_script",
                title="Monitoring System Test",
                message="This is a test alert from the Alpaca Trading System setup",
                timestamp=datetime.utcnow()
            )
            
            await webhook.send(test_alert)
            print("✅ Discord test alert sent")
        except Exception as e:
            print(f"⚠️  Discord webhook test failed: {e}")
    
    # Initialize monitoring keys in Redis
    print("Setting up monitoring keys in Redis...")
    
    await r.set("monitoring:status", "active")
    await r.expire("alerts:active", 86400)
    await r.expire("alerts:resolved", 86400 * 7)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    print("✅ Monitoring system ready")
    print("\nNext steps:")
    print("1. Update config/monitoring.yaml with your Discord webhook URL")
    print("2. Run 'make monitor-start' to begin monitoring")
    print("3. Check logs/ directory for structured logs")
    
    await r.close()

DEFAULT_CONFIG = """monitoring:
  alerts:
    discord:
      enabled: false
      webhook_url: "YOUR_WEBHOOK_URL"
      min_severity: warning
    
    email:
      enabled: false
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      username: "your-email@gmail.com"
      password: "your-app-password"
      from_email: "alerts@trading.local"
      to_emails:
        - "trader@example.com"
      min_severity: error
  
  thresholds:
    heartbeat_timeout: 60
    daily_loss_limit: 1000
    order_reject_rate: 0.1
    latency_95th: 1000
    error_rate: 0.05
    position_concentration: 0.3
    max_drawdown: 0.15
  
  metrics:
    prometheus:
      enabled: true
      port: 9090
      path: "/metrics"
    
    retention:
      detailed: 7
      aggregated: 30
  
  logging:
    level: INFO
    format: json
    outputs:
      - file: logs/trading.jsonl
      - console: true
"""

if __name__ == "__main__":
    print("="*50)
    print("Alpaca Trading System - Monitoring Setup")
    print("="*50)
    
    asyncio.run(setup_monitoring())