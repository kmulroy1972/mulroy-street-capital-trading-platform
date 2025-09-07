#!/usr/bin/env python3
"""
Go-Live Control Script
Manage the transition from testing to live trading
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from tabulate import tabulate
import redis.asyncio as redis
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import time

from packages.core.controls.production_controller import ProductionController, SystemState

console = Console()

async def check_status(controller: ProductionController):
    """Display current system status"""
    console.print("\n[bold cyan]System Status[/bold cyan]")
    
    # Get current state
    console.print(f"State: [bold yellow]{controller.state.value}[/bold yellow]")
    
    # Pre-flight checklist
    checklist = controller.checklist
    
    table = Table(title="Pre-Flight Checklist")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="green")
    
    for key, value in checklist.__dict__.items():
        status = "✅ Passed" if value else "❌ Failed"
        style = "green" if value else "red"
        table.add_row(key.replace("_", " ").title(), f"[{style}]{status}[/{style}]")
    
    console.print(table)
    
    # Show recent performance
    shadow_stats = await controller.redis.get("shadow:statistics")
    if shadow_stats:
        stats = json.loads(shadow_stats)
        console.print("\n[bold]Shadow Mode Statistics:[/bold]")
        console.print(f"  Total Intents: {stats.get('total_intents', 0)}")
        console.print(f"  Duration: {stats.get('duration_hours', 0):.1f} hours")
    
    canary_stats = await controller.redis.get("canary:statistics")
    if canary_stats:
        stats = json.loads(canary_stats)
        console.print("\n[bold]Canary Mode Statistics:[/bold]")
        console.print(f"  Total Trades: {stats.get('total_trades', 0)}")
        console.print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
        console.print(f"  Total P&L: ${stats.get('total_pnl', 0):.2f}")

async def run_preflight(controller: ProductionController):
    """Run pre-flight checks"""
    console.print("\n[bold cyan]Running Pre-Flight Checks...[/bold cyan]")
    
    with console.status("[bold green]Checking systems...") as status:
        passed, failures = await controller.pre_flight_check()
    
    if passed:
        console.print("[bold green]✅ All pre-flight checks PASSED![/bold green]")
    else:
        console.print("[bold red]❌ Pre-flight checks FAILED:[/bold red]")
        for failure in failures:
            console.print(f"  - {failure}")
    
    return passed

async def start_shadow(controller: ProductionController):
    """Start shadow mode"""
    console.print("\n[bold yellow]Starting Shadow Mode...[/bold yellow]")
    
    if await controller.start_shadow_mode():
        console.print("[green]✅ Shadow mode activated[/green]")
        console.print("Monitor shadow trades in the dashboard")
        console.print("Run for at least 24 hours before proceeding to canary")
    else:
        console.print("[red]❌ Failed to start shadow mode[/red]")

async def start_canary(controller: ProductionController):
    """Start canary mode"""
    console.print("\n[bold yellow]Starting Canary Mode...[/bold yellow]")
    
    # Get initial size
    size = console.input("Initial position size (shares) [default: 1]: ")
    size = int(size) if size else 1
    
    if await controller.start_canary_mode(size):
        console.print(f"[green]✅ Canary mode activated with size {size}[/green]")
        console.print("Monitor canary trades closely")
        console.print("Success rate must exceed 80% before ramping up")
    else:
        console.print("[red]❌ Failed to start canary mode[/red]")

async def start_ramp(controller: ProductionController):
    """Start gradual ramp-up"""
    console.print("\n[bold yellow]Starting Gradual Ramp-Up...[/bold yellow]")
    
    target = console.input("Target position size (shares) [default: 100]: ")
    target = int(target) if target else 100
    
    days = console.input("Ramp-up period (days) [default: 7]: ")
    days = int(days) if days else 7
    
    if await controller.gradual_ramp_up(target, days):
        console.print(f"[green]✅ Ramp-up scheduled: {target} shares over {days} days[/green]")
        
        # Show schedule
        table = Table(title="Ramp-Up Schedule")
        table.add_column("Day", style="cyan")
        table.add_column("Position Size", style="green")
        table.add_column("Max Daily Trades", style="yellow")
        
        current_size = 1
        daily_increment = (target - current_size) / days
        
        for day in range(days):
            current_size += daily_increment
            table.add_row(
                str(day + 1),
                str(int(current_size)),
                str(min(10, 3 + day))
            )
        
        console.print(table)
    else:
        console.print("[red]❌ Failed to start ramp-up[/red]")

async def enable_live(controller: ProductionController):
    """Enable live trading"""
    console.print("\n[bold red]⚠️  ENABLE LIVE TRADING ⚠️[/bold red]")
    console.print("This will enable trading with REAL MONEY")
    
    # Generate confirmation code
    import hashlib
    confirmation_code = hashlib.sha256(
        f"{datetime.utcnow().date()}:ENABLE_LIVE_TRADING".encode()
    ).hexdigest()[:8]
    
    console.print(f"\nConfirmation code: [bold yellow]{confirmation_code}[/bold yellow]")
    
    user_input = console.input("Enter confirmation code to proceed: ")
    
    if user_input == confirmation_code:
        if await controller.enable_live_trading(confirmation_code):
            console.print("[bold green]🟢 LIVE TRADING ENABLED![/bold green]")
            console.print("Monitor closely at all times")
            console.print("Emergency stop available with: ./go_live.py emergency-stop")
        else:
            console.print("[red]❌ Failed to enable live trading[/red]")
    else:
        console.print("[red]❌ Invalid confirmation code[/red]")

async def emergency_stop(controller: ProductionController):
    """Trigger emergency stop"""
    console.print("\n[bold red]🚨 EMERGENCY STOP 🚨[/bold red]")
    
    reason = console.input("Reason for emergency stop: ")
    flatten = console.input("Flatten all positions? (yes/no) [no]: ")
    
    if flatten.lower() == "yes":
        reason += " - FLATTEN ALL"
    
    if await controller.emergency_stop(reason):
        console.print("[bold red]⛔ EMERGENCY STOP ACTIVATED[/bold red]")
        console.print("All trading halted")
        if flatten.lower() == "yes":
            console.print("All positions being flattened")
    else:
        console.print("[red]Failed to trigger emergency stop[/red]")

async def main():
    parser = argparse.ArgumentParser(description="Go-Live Control System")
    parser.add_argument("command", choices=[
        "status", "preflight", "shadow", "canary", 
        "ramp", "live", "pause", "resume", "emergency-stop"
    ])
    parser.add_argument("--duration", type=int, help="Pause duration in minutes")
    
    args = parser.parse_args()
    
    # Connect to Redis
    r = await redis.from_url("redis://localhost:6379")
    
    # Initialize controller
    controller = ProductionController(r)
    
    # ASCII Art Header
    console.print("""
    [bold cyan]
    ╔═══════════════════════════════════════╗
    ║   ALPACA TRADING SYSTEM - GO LIVE    ║
    ║      Mulroy Street Capital            ║
    ╚═══════════════════════════════════════╝
    [/bold cyan]
    """)
    
    # Execute command
    if args.command == "status":
        await check_status(controller)
    
    elif args.command == "preflight":
        await run_preflight(controller)
    
    elif args.command == "shadow":
        await start_shadow(controller)
    
    elif args.command == "canary":
        await start_canary(controller)
    
    elif args.command == "ramp":
        await start_ramp(controller)
    
    elif args.command == "live":
        await enable_live(controller)
    
    elif args.command == "pause":
        duration = args.duration or 60
        if await controller.pause_trading(duration):
            console.print(f"[yellow]Trading paused for {duration} minutes[/yellow]")
    
    elif args.command == "resume":
        controller.state = SystemState.LIVE
        console.print("[green]Trading resumed[/green]")
    
    elif args.command == "emergency-stop":
        await emergency_stop(controller)
    
    await r.close()

if __name__ == "__main__":
    asyncio.run(main())