"""
Comprehensive audit logging for Scherman Trading System
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class AuditLogger:
    """Tamper-evident audit logging system"""
    
    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up audit logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def log_trade_execution(self, trade_data: Dict[str, Any]):
        """Log trade execution with integrity hash"""
        audit_record = {
            'event_type': 'TRADE_EXECUTION',
            'timestamp': datetime.utcnow().isoformat(),
            'trade_id': trade_data.get('order_id'),
            'symbol': trade_data.get('symbol'),
            'side': trade_data.get('side'),
            'size': str(trade_data.get('size', 0)),
            'price': str(trade_data.get('price', 0)),
            'fees': str(trade_data.get('fees', 0))
        }
        
        # Add integrity hash
        record_string = json.dumps(audit_record, sort_keys=True)
        audit_record['integrity_hash'] = hashlib.sha256(record_string.encode()).hexdigest()
        
        self.logger.info(json.dumps(audit_record))
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        audit_record = {
            'event_type': f'SECURITY_{event_type}',
            'timestamp': datetime.utcnow().isoformat(),
            'details': details
        }
        
        record_string = json.dumps(audit_record, sort_keys=True)
        audit_record['integrity_hash'] = hashlib.sha256(record_string.encode()).hexdigest()
        
        self.logger.warning(json.dumps(audit_record))
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """Log system events"""
        audit_record = {
            'event_type': f'SYSTEM_{event_type}',
            'timestamp': datetime.utcnow().isoformat(),
            'details': details
        }
        
        record_string = json.dumps(audit_record, sort_keys=True)
        audit_record['integrity_hash'] = hashlib.sha256(record_string.encode()).hexdigest()
        
        self.logger.info(json.dumps(audit_record))

