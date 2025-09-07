# Go-Live Guide for Mulroy Street Capital Trading System

## ⚠️ IMPORTANT: READ COMPLETELY BEFORE PROCEEDING

This guide walks you through safely transitioning from testing to live trading with real money.

## Pre-Requisites

Before starting the go-live process, ensure:

1. ✅ Alpaca account is funded with at least $25,000 (PDT requirement)
2. ✅ All strategies have been backtested with positive results
3. ✅ System has run in test mode for at least 1 week
4. ✅ Emergency contacts are configured
5. ✅ You understand the financial risks involved

## Go-Live Process

### Phase 1: Pre-Flight Check (Day 0)

```bash
# Run comprehensive system check
./scripts/go_live.py preflight

# Review all items and fix any failures
# All checks must pass before proceeding
```

### Phase 2: Shadow Mode (Days 1-2)

Shadow mode simulates trading without placing real orders.

```bash
# Start shadow mode
./scripts/go_live.py shadow

# Monitor for 24-48 hours
# Check dashboard for shadow trade performance
# Verify strategies are generating expected signals
```

Success Criteria:
- No system errors for 24 hours
- Strategy signals align with expectations
- P&L simulation shows positive results

### Phase 3: Canary Mode (Days 3-5)

Canary mode places minimal real trades (1 share).

```bash
# Start canary mode with 1 share positions
./scripts/go_live.py canary

# Monitor closely for 2-3 days
# Check every trade execution
# Verify orders are filled as expected
```

Success Criteria:
- Success rate > 80%
- No unexpected losses
- Order execution working correctly

### Phase 4: Gradual Ramp-Up (Days 6-12)

Gradually increase position sizes.

```bash
# Start 7-day ramp to target size
./scripts/go_live.py ramp

# Daily position size increases:
# Day 1: 1 share
# Day 2: 15 shares
# Day 3: 30 shares
# Day 4: 45 shares
# Day 5: 60 shares
# Day 6: 80 shares
# Day 7: 100 shares
```

Monitor Daily:
- P&L performance
- Risk metrics
- System stability

### Phase 5: Enable Live Trading (Day 13)

**⚠️ FINAL CHECKPOINT - REAL MONEY AT RISK**

```bash
# Get confirmation code
./scripts/go_live.py live

# Enter the confirmation code when prompted
# System will verify all safety checks
# Live trading will be enabled
```

## Safety Controls

### Emergency Stop

Immediately halt all trading:

```bash
./scripts/go_live.py emergency-stop
```

Options:
- Stop only (keeps positions)
- Stop and flatten (closes all positions)

### Pause Trading

Temporarily pause for maintenance:

```bash
./scripts/go_live.py pause --duration 60  # Pause for 60 minutes
```

### Kill Switch Locations

1. **Web Dashboard**: Red emergency stop button
2. **CLI**: `./scripts/go_live.py emergency-stop`
3. **API**: POST to `/api/controls/emergency_stop`
4. **Redis**: `SET engine:emergency_stop true`

## Monitoring Checklist

### Daily Tasks

- [ ] Check account equity and cash levels
- [ ] Review all positions and P&L
- [ ] Verify risk limits are enforced
- [ ] Check system alerts and logs
- [ ] Review strategy performance

### Weekly Tasks

- [ ] Analyze trade statistics
- [ ] Review and adjust risk parameters
- [ ] Check backtests vs live performance
- [ ] Update strategy parameters if needed
- [ ] Backup trade logs and data

### Red Flags - Stop Trading If:

- 🚨 Daily loss exceeds $1,000
- 🚨 System heartbeat missing > 60 seconds
- 🚨 Unexpected positions or orders
- 🚨 API connection issues
- 🚨 Risk manager warnings
- 🚨 Strategy behaving unexpectedly

## Risk Parameters

Default limits (adjust in config):

```yaml
risk_limits:
  daily_loss_limit: 1000
  max_position_size: 10000
  max_portfolio_heat: 0.02
  max_correlation: 0.7
  per_trade_stop_loss: 0.02
```

## Support Contacts

- Alpaca Support: support@alpaca.markets
- System Issues: [Your contact]
- Emergency: [Emergency contact]

## Rollback Procedure

If issues occur after go-live:

1. **Immediate**: Hit emergency stop
2. **Assess**: Review positions and losses
3. **Decide**: Close positions or hold
4. **Rollback**: Return to shadow/canary mode
5. **Fix**: Address issues before retry

## Tax Considerations

- All trades are taxable events
- Short-term gains taxed as ordinary income
- Keep detailed records for tax reporting
- Consider wash sale rules

## Legal Disclaimer

Trading involves substantial risk of loss. Past performance does not guarantee future results. Only trade with money you can afford to lose.

---

## Quick Reference Card

```
EMERGENCY STOP: ./scripts/go_live.py emergency-stop
PAUSE:          ./scripts/go_live.py pause
STATUS:         ./scripts/go_live.py status
DASHBOARD:      http://localhost:3000
LOGS:           tail -f logs/trading.jsonl
```

Remember: Start small, monitor constantly, and scale gradually!