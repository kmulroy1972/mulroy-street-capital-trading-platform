import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, Type, Optional
import logging
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

from packages.core.strategies.base import StrategyBase

logger = logging.getLogger(__name__)

class StrategyLoader:
    """Dynamic strategy loader with hot-reload capability"""
    
    def __init__(self, strategies_dir: str = "packages/strategies"):
        self.strategies_dir = Path(strategies_dir)
        self.loaded_strategies: Dict[str, StrategyBase] = {}
        self.strategy_classes: Dict[str, Type[StrategyBase]] = {}
        self.observer = None
        self.file_watcher = None
        
    def load_all_strategies(self) -> Dict[str, StrategyBase]:
        """Load all strategies from the strategies directory"""
        strategies = {}
        
        # Find all strategy Python files
        strategy_files = self.strategies_dir.glob("*/strategy.py")
        
        for strategy_file in strategy_files:
            strategy_name = strategy_file.parent.name
            if strategy_name in ['base', '__pycache__']:
                continue
                
            try:
                strategy = self.load_strategy(strategy_name)
                if strategy:
                    strategies[strategy_name] = strategy
                    logger.info(f"Loaded strategy: {strategy_name}")
            except Exception as e:
                logger.error(f"Failed to load strategy {strategy_name}: {e}")
        
        return strategies
    
    def load_strategy(self, strategy_name: str) -> Optional[StrategyBase]:
        """Load or reload a specific strategy"""
        strategy_path = self.strategies_dir / strategy_name / "strategy.py"
        config_path = self.strategies_dir / strategy_name / "config.json"
        
        if not strategy_path.exists():
            logger.error(f"Strategy file not found: {strategy_path}")
            return None
        
        try:
            # Load strategy configuration
            config = {}
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Load the module
            spec = importlib.util.spec_from_file_location(
                f"strategies.{strategy_name}",
                strategy_path
            )
            module = importlib.util.module_from_spec(spec)
            
            # Reload if already loaded
            if f"strategies.{strategy_name}" in sys.modules:
                importlib.reload(module)
            else:
                sys.modules[f"strategies.{strategy_name}"] = module
            
            spec.loader.exec_module(module)
            
            # Find the Strategy class
            strategy_class = None
            for name, obj in module.__dict__.items():
                if (isinstance(obj, type) and 
                    issubclass(obj, StrategyBase) and 
                    obj != StrategyBase):
                    strategy_class = obj
                    break
            
            if not strategy_class:
                logger.error(f"No Strategy class found in {strategy_name}")
                return None
            
            # Instantiate the strategy
            strategy_instance = strategy_class(config)
            self.loaded_strategies[strategy_name] = strategy_instance
            self.strategy_classes[strategy_name] = strategy_class
            
            logger.info(f"Successfully loaded strategy: {strategy_name} v{strategy_instance.version}")
            return strategy_instance
            
        except Exception as e:
            logger.error(f"Error loading strategy {strategy_name}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def reload_strategy(self, strategy_name: str) -> bool:
        """Hot-reload a strategy without stopping the engine"""
        logger.info(f"Hot-reloading strategy: {strategy_name}")
        
        # Save state if strategy exists
        old_state = None
        if strategy_name in self.loaded_strategies:
            old_strategy = self.loaded_strategies[strategy_name]
            if hasattr(old_strategy, 'get_state'):
                old_state = old_strategy.get_state()
        
        # Reload the strategy
        new_strategy = self.load_strategy(strategy_name)
        
        if new_strategy:
            # Restore state if available
            if old_state and hasattr(new_strategy, 'set_state'):
                new_strategy.set_state(old_state)
            
            logger.info(f"Strategy {strategy_name} reloaded successfully")
            return True
        
        return False
    
    def start_file_watcher(self, callback=None):
        """Start watching strategy files for changes"""
        class StrategyFileHandler(FileSystemEventHandler):
            def __init__(self, loader, callback):
                self.loader = loader
                self.callback = callback
                self.last_reload = {}
            
            def on_modified(self, event):
                if event.src_path.endswith('.py'):
                    # Prevent multiple reloads for same file
                    now = datetime.now()
                    if event.src_path in self.last_reload:
                        if (now - self.last_reload[event.src_path]).seconds < 2:
                            return
                    
                    self.last_reload[event.src_path] = now
                    
                    # Extract strategy name
                    path_parts = Path(event.src_path).parts
                    if 'strategies' in path_parts:
                        idx = path_parts.index('strategies')
                        if idx + 1 < len(path_parts):
                            strategy_name = path_parts[idx + 1]
                            
                            logger.info(f"Detected change in {strategy_name}")
                            if self.loader.reload_strategy(strategy_name):
                                if self.callback:
                                    self.callback(strategy_name)
        
        self.file_watcher = StrategyFileHandler(self, callback)
        self.observer = Observer()
        self.observer.schedule(
            self.file_watcher,
            str(self.strategies_dir),
            recursive=True
        )
        self.observer.start()
        logger.info("Strategy file watcher started")
    
    def stop_file_watcher(self):
        """Stop watching strategy files"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Strategy file watcher stopped")