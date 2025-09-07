import logging
import structlog
from pythonjsonlogger import jsonlogger
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """Setup structured logging for the trading system"""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure Python's logging
    log_file = log_path / f"trading_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    # JSON formatter for file logs
    json_formatter = jsonlogger.JsonFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'levelname': 'level', 'asctime': 'timestamp'}
    )
    
    # File handler for JSON logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(json_formatter)
    
    # Console handler for human-readable logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()

class CorrelationIdProcessor:
    """Add correlation ID to all log entries"""
    
    def __init__(self):
        self.correlation_id = None
    
    def __call__(self, logger, method_name, event_dict):
        if self.correlation_id:
            event_dict['correlation_id'] = self.correlation_id
        return event_dict

class TradingContextProcessor:
    """Add trading context to log entries"""
    
    def __call__(self, logger, method_name, event_dict):
        # Add trading-specific context
        event_dict['environment'] = 'live'
        event_dict['service'] = 'alpaca-trader'
        
        # Add any global context (e.g., current positions, strategies)
        if hasattr(logger, '_context'):
            event_dict.update(logger._context)
        
        return event_dict