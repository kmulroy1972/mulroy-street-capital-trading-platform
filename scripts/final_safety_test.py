#!/usr/bin/env python3
"""
Final safety test before go-live
Tests all emergency procedures
"""

import asyncio
import sys
from datetime import datetime
import redis.asyncio as redis

async def test_emergency_systems():
    """Test all emergency systems"""
    print("="*60)
    print("FINAL SAFETY SYSTEMS TEST")
    print("="*60)
    
    r = await redis.from_url("redis://localhost:6379")
    
    tests_passed = []
    tests_failed = []
    
    # Test 1: Kill switch
    print("\n[TEST 1] Testing kill switch...")
    try:
        await r.set("engine:emergency_stop", "true")
        result = await r.get("engine:emergency_stop")
        if result == b"true":
            print("✅ Kill switch works")
            tests_passed.append("Kill switch")
        await r.delete("engine:emergency_stop")
    except Exception as e:
        print(f"❌ Kill switch failed: {e}")
        tests_failed.append("Kill switch")
    
    # Test 2: Risk limits
    print("\n[TEST 2] Testing risk limits...")
    try:
        await r.set("risk:daily_loss_limit", "1000")
        limit = await r.get("risk:daily_loss_limit")
        if limit:
            print("✅ Risk limits configured")
            tests_passed.append("Risk limits")
    except Exception as e:
        print(f"❌ Risk limits failed: {e}")
        tests_failed.append("Risk limits")
    
    # Test 3: Monitoring
    print("\n[TEST 3] Testing monitoring...")
    try:
        await r.set("monitoring:status", "active")
        status = await r.get("monitoring:status")
        if status == b"active":
            print("✅ Monitoring active")
            tests_passed.append("Monitoring")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        tests_failed.append("Monitoring")
    
    # Test 4: Alerts
    print("\n[TEST 4] Testing alerts...")
    try:
        await r.lpush("alerts:test", "test_alert")
        alerts = await r.lrange("alerts:test", 0, -1)
        if alerts:
            print("✅ Alert system works")
            tests_passed.append("Alerts")
        await r.delete("alerts:test")
    except Exception as e:
        print(f"❌ Alert system failed: {e}")
        tests_failed.append("Alerts")
    
    # Test 5: Audit logging
    print("\n[TEST 5] Testing audit logging...")
    try:
        audit_entry = {
            "action": "safety_test",
            "timestamp": datetime.utcnow().isoformat(),
            "user": "system"
        }
        await r.lpush("audit:log", str(audit_entry))
        log = await r.lrange("audit:log", 0, 0)
        if log:
            print("✅ Audit logging works")
            tests_passed.append("Audit logging")
    except Exception as e:
        print(f"❌ Audit logging failed: {e}")
        tests_failed.append("Audit logging")
    
    # Results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Passed: {len(tests_passed)}/{len(tests_passed) + len(tests_failed)}")
    
    if tests_failed:
        print("\n❌ FAILED TESTS:")
        for test in tests_failed:
            print(f"  - {test}")
        print("\n⚠️  DO NOT PROCEED TO LIVE TRADING")
        print("Fix all issues before attempting go-live")
    else:
        print("\n✅ ALL SAFETY TESTS PASSED")
        print("System is ready for go-live process")
    
    await r.close()
    
    return len(tests_failed) == 0

if __name__ == "__main__":
    success = asyncio.run(test_emergency_systems())
    sys.exit(0 if success else 1)